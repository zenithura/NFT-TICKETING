"""Pydantic models for API request/response validation."""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


# User models
class UserBase(BaseModel):
    email: str = Field(..., description="User email address")
    username: Optional[str] = Field(None, description="Username")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    role: str = Field(..., description="User role: BUYER or ORGANIZER")


class UserResponse(BaseModel):
    user_id: int
    email: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str
    is_email_verified: bool
    created_at: str


# Authentication models
class RegisterRequest(BaseModel):
    email: str = Field(..., description="User email")
    password: str = Field(..., min_length=8, description="User password")
    username: Optional[str] = Field(None, max_length=100)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    role: str = Field(..., description="User role: BUYER or ORGANIZER")


class LoginRequest(BaseModel):
    email: str = Field(..., description="User email")
    password: str = Field(..., description="User password")


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token")


class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., description="User email")


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., description="Reset token")
    new_password: str = Field(..., min_length=8, description="New password")


class VerifyEmailRequest(BaseModel):
    token: str = Field(..., description="Verification token")


class AuthResponse(BaseModel):
    success: bool
    message: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    user: Optional[UserResponse] = None


# Event models
class EventCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    date: str = Field(..., description="Event date (ISO format)")
    location: str = Field(..., min_length=1, max_length=200)
    total_tickets: int = Field(..., gt=0)
    price: float = Field(..., ge=0)
    organizer_address: Optional[str] = Field(None, description="Organizer wallet address (optional, will use authenticated user)")
    image_url: Optional[str] = None
    category: Optional[str] = "All"
    currency: Optional[str] = "ETH"

class EventResponse(EventCreate):
    id: int
    created_at: datetime
    sold_tickets: Optional[int] = 0


# Ticket models
class TicketCreate(BaseModel):
    event_id: int
    owner_address: str
    nft_token_id: Optional[int] = None
    status: Literal["available", "bought", "used"] = Field(default="available")


class TicketResponse(TicketCreate):
    id: int
    created_at: Optional[datetime] = None


# Marketplace models
class MarketplaceListingCreate(BaseModel):
    ticket_id: int
    seller_address: str
    price: float = Field(..., ge=0)
    status: Literal["active", "sold", "cancelled"] = Field(default="active")


class MarketplaceListingResponse(MarketplaceListingCreate):
    id: int
    created_at: Optional[datetime] = None


class MarketplaceListingUpdate(BaseModel):
    price: Optional[float] = Field(None, ge=0)
    status: Optional[Literal["active", "sold", "cancelled"]] = None


# Authentication
class WalletAuthRequest(BaseModel):
    address: str
    signature: Optional[str] = None
    message: Optional[str] = None


# Blockchain Request Models
class MintRequest(BaseModel):
    to_address: str
    token_uri: str
    event_id: int
    price: float  # In ETH

class ValidatorRequest(BaseModel):
    validator_address: str

class ValidateRequest(BaseModel):
    ticket_id: int
    validator_address: Optional[str] = None # If not provided, use default account

class ListRequest(BaseModel):
    ticket_id: int
    price: float # In ETH

class BuyRequest(BaseModel):
    ticket_id: int
    value: float # In ETH

class UpdatePriceRequest(BaseModel):
    ticket_id: int
    new_price: float # In ETH

class EscrowRequest(BaseModel):
    ticket_id: int
