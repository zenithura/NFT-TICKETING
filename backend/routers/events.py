"""Events management router."""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from supabase import Client

from database import get_supabase_admin
from models import EventCreate, EventResponse
from auth_middleware import get_current_user, require_role
from cache import cached, get as cache_get, set as cache_set, clear as cache_clear, _generate_cache_key

router = APIRouter(prefix="/events", tags=["Events"])


@router.post("/", response_model=EventResponse)
async def create_event(
    event: EventCreate,
    user: dict = Depends(require_role("ORGANIZER")),
    db: Client = Depends(get_supabase_admin)
):
    """Create a new event (organizer only)."""
    try:
        # Clear events cache when new event is created
        cache_clear("events:")
        # Get user's wallet address if available, otherwise use email as identifier
        user_wallet = user.get("wallet_address")
        if not user_wallet:
            # For now, use user email or create a placeholder
            # In production, users should connect their wallet
            user_wallet = user.get("email", "unknown")
        
        # Create or get venue from location
        venue_name = event.location.split(",")[0].strip() if event.location else "Unknown Venue"
        venue_location = event.location
        
        # Check if venue exists
        venue_response = db.table("venues").select("venue_id").eq("name", venue_name).eq("location", venue_location).execute()
        
        if venue_response.data:
            venue_id = venue_response.data[0]["venue_id"]
        else:
            # Create new venue
            venue_data = {
                "name": venue_name,
                "location": venue_location,
                "city": venue_location.split(",")[-1].strip() if "," in venue_location else venue_location,
                "capacity": event.total_tickets
            }
            venue_insert = db.table("venues").insert(venue_data).execute()
            if not venue_insert.data:
                raise HTTPException(status_code=500, detail="Failed to create venue")
            venue_id = venue_insert.data[0]["venue_id"]
        
        # Prepare event data for database
        # Map frontend fields to database schema
        from datetime import datetime
        event_date_str = event.date
        try:
            # Parse date string (could be ISO format or other)
            if "T" in event_date_str:
                event_date = datetime.fromisoformat(event_date_str.replace("Z", "+00:00"))
            else:
                event_date = datetime.fromisoformat(event_date_str)
        except Exception as parse_error:
            # Fallback: try to parse common formats
            try:
                from dateutil import parser
                event_date = parser.parse(event_date_str)
            except:
                # If all parsing fails, use current date + 1 day
                event_date = datetime.now()
                import logging
                logging.warning(f"Could not parse date {event_date_str}, using current date: {parse_error}")
        
        # Prepare event data for database
        event_data = {
            "name": event.name,
            "description": event.description,
            "event_date": event_date.isoformat(),
            "start_time": "00:00:00",  # Default, can be updated later
            "end_time": "23:59:59",  # Default, can be updated later
            "venue_id": venue_id,
            "organizer_address": user_wallet,  # Store organizer address
            "total_supply": event.total_tickets,  # Database uses total_supply
            "available_tickets": event.total_tickets,  # Initially all tickets are available
            "base_price": event.price,  # Database uses base_price
            "status": "UPCOMING"
        }
        
        # Create event
        response = db.table("events").insert(event_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create event")
        
        # Format response to match EventResponse model
        created_event = response.data[0]
        event_id = created_event.get("event_id") or created_event.get("id")
        
        result = EventResponse(
            id=event_id,
            name=created_event.get("name"),
            description=created_event.get("description"),
            date=created_event.get("event_date"),
            location=venue_location,
            total_tickets=created_event.get("total_supply") or created_event.get("total_tickets"),
            price=float(created_event.get("base_price") or created_event.get("price") or 0),
            organizer_address=user_wallet,
            image_url=event.image_url,
            category=event.category or "All",
            currency=event.currency or "ETH",
            created_at=created_event.get("created_at") or datetime.now().isoformat(),
            sold_tickets=0
        )
        
        # Clear cache after creating event
        cache_clear("events:")
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to create event: {str(e)}")


@router.get("/", response_model=List[EventResponse])
async def list_events(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
    db: Client = Depends(get_supabase_admin)
):
    """List events with pagination. Default: limit=20, skip=0."""
    cache_key = "events:list"
    cached_result = cache_get(cache_key)
    # Temporarily disable cache for debugging - remove this after fixing
    # if cached_result is not None:
    #     return cached_result
    
    try:
        # Optimized: Fetch events with pagination
        # Note: Supabase doesn't support direct JOINs, so we batch queries efficiently
        events_response = db.table("events").select("*").order("event_date", desc=False).range(skip, skip + limit - 1).execute()
        events = events_response.data
        
        # Debug: Log what events were fetched
        import logging
        logging.info(f"Fetched {len(events)} events from database")
        if events:
            event_ids = [e.get("event_id") or e.get("id") for e in events]
            logging.info(f"Event IDs in database: {event_ids}")
        
        if not events:
            return []
        
        # Batch fetch all venue IDs
        venue_ids = [e.get("venue_id") for e in events if e.get("venue_id")]
        unique_venue_ids = list(set(venue_ids))
        
        # Batch fetch all venues in one query
        venues_map = {}
        if unique_venue_ids:
            # Fetch venues in batches (Supabase limit is ~1000 per query)
            for venue_id in unique_venue_ids:
                venue_response = db.table("venues").select("venue_id, name, location, city").eq("venue_id", venue_id).limit(1).execute()
                if venue_response.data:
                    venue = venue_response.data[0]
                    venues_map[venue_id] = venue
        
        # Batch fetch ticket counts for all events
        event_ids = [e.get("event_id") or e.get("id") for e in events]
        unique_event_ids = list(set([eid for eid in event_ids if eid]))
        
        # Calculate sold tickets efficiently - use available_tickets from events table
        # This avoids N+1 queries since available_tickets is already in events table
        formatted_events = []
        for event in events:
            # Get event_id - prioritize event_id column (matches your schema)
            event_id = event.get("event_id")
            if event_id is None:
                event_id = event.get("id")
            # Ensure event_id is an integer
            try:
                event_id = int(event_id) if event_id is not None else None
            except (ValueError, TypeError):
                event_id = None
            
            if event_id is None:
                import logging
                logging.warning(f"Skipping event without ID. Event data: {list(event.keys())}")
                continue
                
            venue_id = event.get("venue_id")
            
            # Get venue location from map
            location = "Unknown Location"
            if venue_id and venue_id in venues_map:
                venue = venues_map[venue_id]
                location = venue.get("location") or f"{venue.get('name')}, {venue.get('city', '')}"
            
            # Use available_tickets from events table (no need for separate query)
            total_supply = event.get("total_supply", 0)
            available = event.get("available_tickets", total_supply)
            sold_count = total_supply - available
            
            formatted_event = {
                "id": event_id,  # This is event_id from database (6, 4, 5, etc.)
                "name": event.get("name"),
                "description": event.get("description"),
                "date": event.get("event_date"),
                "location": location,
                "total_tickets": total_supply,
                "price": float(event.get("base_price", 0)),
                "organizer_address": event.get("organizer_address") or "unknown",
                "image_url": event.get("image_url"),
                "category": event.get("category") or "All",
                "currency": event.get("currency") or "ETH",
                "created_at": event.get("created_at"),
                "sold_tickets": sold_count
            }
            formatted_events.append(formatted_event)
        
        # Debug: Log event IDs being returned
        import logging
        event_ids_returned = [e.get("id") for e in formatted_events]
        logging.info(f"Events API returning {len(formatted_events)} events with IDs: {event_ids_returned}")
        
        # Validate and create EventResponse objects, skip invalid ones
        result = []
        for event in formatted_events:
            try:
                event_response = EventResponse(**event)
                result.append(event_response)
            except Exception as validation_error:
                import traceback
                logging.warning(f"Skipping event {event.get('id')} due to validation error: {str(validation_error)}\nEvent data: {event}")
                # Continue with other events instead of failing completely
                continue
        
        # Cache for 2 minutes (events don't change frequently)
        cache_set(cache_key, result, ttl=120)
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Failed to list events: {str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: int,
    db: Client = Depends(get_supabase_admin)
):
    """Get a specific event by ID with caching."""
    cache_key = f"events:{event_id}"
    cached_result = cache_get(cache_key)
    if cached_result is not None:
        return cached_result
    
    try:
        # Try to find event by event_id column first (matches your schema)
        response = db.table("events").select("*").eq("event_id", event_id).execute()
        
        # If not found, try by id column (alternative schema)
        if not response.data:
            response = db.table("events").select("*").eq("id", event_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail=f"Event with ID {event_id} not found")
        
        event = response.data[0]
        event_id_actual = event.get("event_id") or event.get("id")
        venue_id = event.get("venue_id")
        
        # Get venue location (single query, cached)
        location = "Unknown Location"
        if venue_id:
            venue_cache_key = f"venues:{venue_id}"
            cached_venue = cache_get(venue_cache_key)
            if cached_venue:
                location = cached_venue.get("location") or f"{cached_venue.get('name')}, {cached_venue.get('city', '')}"
            else:
                venue_response = db.table("venues").select("name, location, city").eq("venue_id", venue_id).limit(1).execute()
                if venue_response.data:
                    venue = venue_response.data[0]
                    location = venue.get("location") or f"{venue.get('name')}, {venue.get('city', '')}"
                    # Cache venue for 10 minutes
                    cache_set(venue_cache_key, venue, ttl=600)
        
        # Use available_tickets from events table (no separate query needed)
        total_supply = event.get("total_supply", 0)
        available = event.get("available_tickets", total_supply)
        sold_count = total_supply - available
        
        # Parse created_at to datetime if it's a string
        from datetime import datetime
        created_at = event.get("created_at")
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except:
                created_at = datetime.now()
        elif created_at is None:
            created_at = datetime.now()
        
        # Format event_date to string if it's a datetime
        event_date = event.get("event_date")
        if isinstance(event_date, datetime):
            event_date = event_date.isoformat()
        elif event_date is None:
            event_date = datetime.now().isoformat()
        
        # Ensure total_tickets is at least 1 (EventCreate requires gt=0)
        total_tickets = max(1, total_supply) if total_supply else 1
        
        # Ensure event_id_actual is an integer
        try:
            event_id_actual = int(event_id_actual) if event_id_actual else int(event_id)
        except (ValueError, TypeError):
            event_id_actual = int(event_id)
        
        # Validate required fields
        event_name = event.get("name")
        if not event_name:
            raise HTTPException(status_code=500, detail="Event name is missing")
        
        # Ensure price is a valid float
        try:
            event_price = float(event.get("base_price", 0))
        except (ValueError, TypeError):
            event_price = 0.0
        
        formatted_event = {
            "id": event_id_actual,
            "name": event_name,
            "description": event.get("description") or "No description",
            "date": event_date,
            "location": location or "Unknown Location",
            "total_tickets": int(total_tickets),
            "price": event_price,
            "organizer_address": event.get("organizer_address") or "unknown",
            "image_url": event.get("image_url"),
            "category": event.get("category") or "All",
            "currency": event.get("currency") or "ETH",
            "created_at": created_at,
            "sold_tickets": int(sold_count)
        }
        
        try:
            result = EventResponse(**formatted_event)
        except Exception as validation_error:
            import traceback
            import logging
            logging.error(f"EventResponse validation failed for event {event_id}: {validation_error}")
            logging.error(f"Event data: {formatted_event}")
            logging.error(traceback.format_exc())
            error_msg = f"EventResponse validation failed: {str(validation_error)}"
            raise HTTPException(status_code=500, detail=error_msg)
        
        # Cache for 2 minutes
        cache_set(cache_key, result, ttl=120)
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Failed to get event: {str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)


@router.get("/organizer/{organizer_address}", response_model=List[EventResponse])
async def get_organizer_events(
    organizer_address: str,
    db: Client = Depends(get_supabase_admin)
):
    """Get all events created by a specific organizer."""
    try:
        response = db.table("events").select("*").eq("organizer_address", organizer_address).execute()
        return [EventResponse(**event) for event in response.data]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/organizer/{organizer_address}/stats")
async def get_organizer_stats(
    organizer_address: str,
    db: Client = Depends(get_supabase_admin)
):
    """Get statistics for a specific organizer."""
    try:
        # Fetch organizer's events
        events_response = db.table("events").select("*").eq("organizer_address", organizer_address).execute()
        events = events_response.data
        
        if not events:
            return {
                "total_revenue": 0,
                "tickets_sold": 0,
                "active_events": 0,
                "total_events": 0
            }
        
        # Calculate statistics
        total_revenue = 0
        tickets_sold = 0
        active_events = 0
        
        for event in events:
            event_id = event.get("event_id") or event.get("id")
            price = float(event.get("base_price", 0))
            total_supply = event.get("total_supply", 0)
            available = event.get("available_tickets", total_supply)
            sold_count = total_supply - available
            
            tickets_sold += sold_count
            total_revenue += sold_count * price
            
            # Count as active if event has tickets available
            if available > 0:
                active_events += 1
        
        return {
            "total_revenue": total_revenue,
            "tickets_sold": tickets_sold,
            "active_events": active_events,
            "total_events": len(events)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
