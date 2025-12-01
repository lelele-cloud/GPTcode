"""REST API surface for the AI health assistant demo."""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status

from .ai_engine import AIEngine, HealthSnapshot
from .schemas import (
    BackgroundRequest,
    BackgroundResponse,
    ChatRequest,
    ChatResponse,
    FeedbackRequest,
    FeedbackResponse,
    HealthPayload,
    LoginRequest,
    LoginResponse,
    RecordsResponse,
    SocialShareRequest,
    SocialShareResponse,
    SuggestionResponse,
    SubscriptionRequest,
    SubscriptionResponse,
    TrendPoint,
    TrendResponse,
)
from .storage import Feedback, HealthRecord, MemoryStore, SocialShare

router = APIRouter()
ai_engine = AIEngine()
store = MemoryStore()


def _enforce_analysis_limit(user_id: str) -> Optional[int]:
    _, remaining = store.record_analysis_usage(user_id)
    if remaining is not None and remaining < 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="今日免费分析次数已用完，请明日再试或升级订阅。",
        )
    return remaining


def _to_health_record(payload: HealthPayload) -> HealthRecord:
    return HealthRecord(
        timestamp=payload.timestamp,
        steps=payload.steps,
        resting_heart_rate=payload.resting_heart_rate,
        active_minutes=payload.active_minutes,
        sleep_hours=payload.sleep_hours,
        calories=payload.calories,
        weight_kg=payload.weight_kg,
    )


@router.post("/health-data/sync", response_model=SuggestionResponse)
def sync_healthkit_data(payload: HealthPayload) -> SuggestionResponse:
    remaining = _enforce_analysis_limit(payload.user_id)
    store.add_healthkit_record(payload.user_id, _to_health_record(payload))
    snapshot = HealthSnapshot(
        user_id=payload.user_id,
        steps=payload.steps,
        resting_heart_rate=payload.resting_heart_rate,
        active_minutes=payload.active_minutes,
        sleep_hours=payload.sleep_hours,
        calories=payload.calories,
        weight_kg=payload.weight_kg,
    )
    suggestions = ai_engine.generate_suggestions(snapshot)
    return SuggestionResponse(suggestions=suggestions, remaining_analyses_today=remaining)


@router.post("/manual-entry", response_model=SuggestionResponse)
def manual_entry(payload: HealthPayload) -> SuggestionResponse:
    remaining = _enforce_analysis_limit(payload.user_id)
    store.add_manual_entry(payload.user_id, _to_health_record(payload))
    snapshot = HealthSnapshot(
        user_id=payload.user_id,
        steps=payload.steps,
        resting_heart_rate=payload.resting_heart_rate,
        active_minutes=payload.active_minutes,
        sleep_hours=payload.sleep_hours,
        calories=payload.calories,
        weight_kg=payload.weight_kg,
    )
    suggestions = ai_engine.generate_suggestions(snapshot)
    return SuggestionResponse(suggestions=suggestions, remaining_analyses_today=remaining)


@router.get("/health-data/{user_id}", response_model=RecordsResponse)
def list_records(user_id: str) -> RecordsResponse:
    records = [
        HealthPayload(
            user_id=user_id,
            steps=r.steps,
            resting_heart_rate=r.resting_heart_rate,
            active_minutes=r.active_minutes,
            sleep_hours=r.sleep_hours,
            calories=r.calories,
            weight_kg=r.weight_kg,
            timestamp=r.timestamp,
        )
        for r in store.list_health_records(user_id)
    ]
    return RecordsResponse(records=records)


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    reply = ai_engine.chat(request.user_id, request.message)
    return ChatResponse(reply=reply)


@router.post("/trends", response_model=TrendResponse)
def trends(points: List[TrendPoint]) -> TrendResponse:
    warnings = ai_engine.trend_warnings([(p.metric, p.weekly_change) for p in points])
    return TrendResponse(warnings=warnings)


@router.post("/feedback", response_model=FeedbackResponse)
def submit_feedback(request: FeedbackRequest) -> FeedbackResponse:
    store.add_feedback(
        request.user_id,
        Feedback(timestamp=datetime.utcnow(), rating=request.rating, comment=request.comment),
    )
    return FeedbackResponse(status="received")


@router.post("/social/share", response_model=SocialShareResponse)
def social_share(request: SocialShareRequest) -> SocialShareResponse:
    store.add_social_post(
        request.user_id,
        SocialShare(timestamp=datetime.utcnow(), message=request.message, audience=request.audience),
    )
    return SocialShareResponse(status="posted")


@router.get("/stats")
def stats() -> dict:
    return store.stats()


@router.post("/auth/login", response_model=LoginResponse)
def login(request: LoginRequest) -> LoginResponse:
    profile = store.login_user(request.provider, request.external_id, request.display_name)
    return LoginResponse(
        user_id=f"{request.provider}:{request.external_id}",
        provider=profile.provider,
        display_name=profile.display_name,
        subscription_tier=profile.subscription_tier,
    )


@router.post("/subscription", response_model=SubscriptionResponse)
def update_subscription(request: SubscriptionRequest) -> SubscriptionResponse:
    tier, price = store.set_subscription(request.user_id, request.tier)
    return SubscriptionResponse(tier=tier, price=price)


@router.post("/settings/background", response_model=BackgroundResponse)
def update_background(request: BackgroundRequest) -> BackgroundResponse:
    mode = store.set_background(request.user_id, request.mode)
    return BackgroundResponse(status="updated", mode=mode)
