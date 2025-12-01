"""Pydantic schemas for request/response validation."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, validator


class HealthPayload(BaseModel):
    user_id: str = Field(..., description="User identifier")
    steps: int = 0
    resting_heart_rate: Optional[int] = Field(None, ge=30, le=230)
    active_minutes: int = Field(0, ge=0)
    sleep_hours: float = Field(0.0, ge=0, le=24)
    calories: Optional[int] = Field(None, ge=0)
    weight_kg: Optional[float] = Field(None, ge=20, le=500)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @validator("steps")
    def _non_negative(cls, v: int) -> int:
        if v < 0:
            raise ValueError("Steps cannot be negative")
        return v


class SuggestionSchema(BaseModel):
    category: str
    title: str
    detail: str


class SuggestionResponse(BaseModel):
    suggestions: List[SuggestionSchema]
    remaining_analyses_today: Optional[int] = Field(
        None, description="Remaining analysis quota for today; null means unlimited"
    )


class ChatRequest(BaseModel):
    user_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str


class TrendPoint(BaseModel):
    metric: str
    weekly_change: float


class TrendResponse(BaseModel):
    warnings: List[str]


class FeedbackRequest(BaseModel):
    user_id: str
    rating: int = Field(..., ge=1, le=5)
    comment: str = ""


class FeedbackResponse(BaseModel):
    status: str


class SocialShareRequest(BaseModel):
    user_id: str
    message: str
    audience: str = Field(..., description="target audience description")


class SocialShareResponse(BaseModel):
    status: str


class RecordsResponse(BaseModel):
    records: List[HealthPayload]


class LoginRequest(BaseModel):
    provider: str = Field(..., regex="^(apple|google|x)$", description="login provider")
    external_id: str = Field(..., description="Opaque identifier from the provider")
    display_name: Optional[str] = Field(None, description="User-friendly name")


class LoginResponse(BaseModel):
    user_id: str
    provider: str
    display_name: Optional[str]
    subscription_tier: str


class SubscriptionRequest(BaseModel):
    user_id: str
    tier: str = Field(..., regex="^(free|monthly|quarterly|yearly)$")


class SubscriptionResponse(BaseModel):
    tier: str
    price: float
    currency: str = "USD"


class BackgroundRequest(BaseModel):
    user_id: str
    mode: str = Field(..., regex="^(light|dark|system)$")


class BackgroundResponse(BaseModel):
    status: str
    mode: str
