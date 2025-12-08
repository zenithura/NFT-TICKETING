# Backend Performance Optimizations

## Current State

### ✅ Already Implemented
1. **Response Compression**: GZip middleware enabled for responses > 1KB
2. **Caching Layer**: Redis-based caching for hot endpoints
3. **Metrics**: Prometheus metrics collection
4. **Health Endpoints**: Fast health check endpoints

### Optimizations Needed

## 1. Pagination

### Events List Endpoint
**Current**: Returns all events
**Issue**: Can return large datasets
**Fix**: Add pagination with limit/offset or cursor-based pagination

```python
@router.get("/", response_model=List[EventResponse])
async def get_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Client = Depends(get_supabase_admin)
):
    """Get all events with pagination."""
    # Implementation with skip/limit
```

### Marketplace Listings
**Current**: Returns all listings
**Fix**: Implement pagination with default limit of 20

## 2. Field Selection / Projection

**Current**: Returns full objects
**Fix**: Add `fields` query parameter to select specific fields

```python
@router.get("/")
async def get_events(
    fields: Optional[str] = Query(None, description="Comma-separated list of fields"),
    ...
):
    if fields:
        selected_fields = fields.split(",")
        # Return only selected fields
```

## 3. Database Indexes

### Recommended Indexes

1. **Events Table**
   ```sql
   CREATE INDEX idx_events_status ON events(status);
   CREATE INDEX idx_events_date ON events(event_date);
   CREATE INDEX idx_events_organizer ON events(organizer_address);
   ```

2. **Tickets Table**
   ```sql
   CREATE INDEX idx_tickets_event_id ON tickets(event_id);
   CREATE INDEX idx_tickets_owner ON tickets(owner_address);
   CREATE INDEX idx_tickets_status ON tickets(status);
   ```

3. **Marketplace Listings**
   ```sql
   CREATE INDEX idx_listings_event_id ON marketplace_listings(event_id);
   CREATE INDEX idx_listings_status ON marketplace_listings(status);
   CREATE INDEX idx_listings_price ON marketplace_listings(price);
   ```

## 4. Query Optimization

### N+1 Query Prevention
- Use joins where possible
- Batch queries when fetching related data
- Use database views for complex queries

### Example: Events with Venue
```python
# Instead of:
for event in events:
    venue = db.table("venues").select("*").eq("venue_id", event.venue_id).execute()

# Use:
events = db.table("events").select("*, venues(*)").execute()
```

## 5. Response Streaming

For large datasets:
```python
from fastapi.responses import StreamingResponse

@router.get("/events/export")
async def export_events():
    async def generate():
        # Stream response in chunks
        yield json.dumps(event) + "\n"
    return StreamingResponse(generate(), media_type="application/json")
```

## 6. Caching Strategy

### Current Cache Keys
- `events:` - All events
- `event:{id}` - Single event
- `marketplace:` - Marketplace listings

### Recommended TTLs
- Events list: 60 seconds
- Single event: 300 seconds (5 minutes)
- Marketplace: 30 seconds
- User data: 180 seconds (3 minutes)

## 7. Database Connection Pooling

**Ensure Supabase client uses connection pooling**:
```python
# In database.py
from supabase import create_client
# Connection pooling is handled by Supabase SDK
```

## Performance Targets

- **API Response Time (p95)**: < 200ms
- **Database Query Time (p95)**: < 50ms
- **Cache Hit Rate**: > 80%
- **Payload Size (gzipped)**: < 100KB per response

## Monitoring

- Prometheus metrics for:
  - Response time (p50, p95, p99)
  - Error rate
  - Cache hit/miss ratio
  - Database query time

## Implementation Priority

1. **High**: Add pagination to events and marketplace endpoints
2. **High**: Add database indexes
3. **Medium**: Implement field selection/projection
4. **Medium**: Optimize N+1 queries
5. **Low**: Add response streaming for exports

