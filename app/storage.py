"""In-memory storage used by the demo server.

This keeps the example lightweight while showing where persistence
would live in production (database or cloud KV store).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple


@dataclass
class HealthRecord:
    timestamp: datetime
    steps: int = 0
    resting_heart_rate: Optional[int] = None
    active_minutes: int = 0
    sleep_hours: float = 0.0
    calories: Optional[int] = None
    weight_kg: Optional[float] = None


@dataclass
class Feedback:
    timestamp: datetime
    rating: int
    comment: str


@dataclass
class SocialShare:
    timestamp: datetime
    message: str
    audience: str


@dataclass
class UserProfile:
    provider: str
    external_id: str
    display_name: Optional[str] = None
    subscription_tier: str = "free"  # free, monthly, quarterly, yearly
    background_mode: str = "system"  # light, dark, system
    last_usage_day: Optional[str] = None  # YYYY-MM-DD
    usage_count_today: int = 0


@dataclass
class UserState:
    manual_entries: List[HealthRecord] = field(default_factory=list)
    healthkit_records: List[HealthRecord] = field(default_factory=list)
    feedback: List[Feedback] = field(default_factory=list)
    social_posts: List[SocialShare] = field(default_factory=list)


class MemoryStore:
    def __init__(self) -> None:
        self._data: Dict[str, UserState] = {}
        self._profiles: Dict[str, UserProfile] = {}

    def login_user(
        self, provider: str, external_id: str, display_name: Optional[str] = None
    ) -> UserProfile:
        user_id = f"{provider}:{external_id}"
        profile = self._profiles.get(user_id)
        if profile is None:
            profile = UserProfile(provider=provider, external_id=external_id, display_name=display_name)
            self._profiles[user_id] = profile
        else:
            if display_name:
                profile.display_name = display_name
        # ensure state exists
        self._user(user_id)
        return profile

    def set_subscription(self, user_id: str, tier: str) -> Tuple[str, float]:
        profile = self._profiles.setdefault(user_id, UserProfile(provider="unknown", external_id=user_id))
        profile.subscription_tier = tier
        pricing = {"free": 0.0, "monthly": 14.9, "quarterly": 39.9, "yearly": 150.0}
        return tier, pricing.get(tier, 0.0)

    def set_background(self, user_id: str, mode: str) -> str:
        profile = self._profiles.setdefault(user_id, UserProfile(provider="unknown", external_id=user_id))
        profile.background_mode = mode
        return mode

    def get_profile(self, user_id: str) -> Optional[UserProfile]:
        return self._profiles.get(user_id)

    def _user(self, user_id: str) -> UserState:
        return self._data.setdefault(user_id, UserState())

    def add_healthkit_record(self, user_id: str, record: HealthRecord) -> None:
        self._user(user_id).healthkit_records.append(record)

    def add_manual_entry(self, user_id: str, record: HealthRecord) -> None:
        self._user(user_id).manual_entries.append(record)

    def get_latest_snapshot(self, user_id: str) -> Optional[HealthRecord]:
        user = self._user(user_id)
        all_records = user.healthkit_records + user.manual_entries
        if not all_records:
            return None
        return sorted(all_records, key=lambda r: r.timestamp)[-1]

    def list_health_records(self, user_id: str) -> List[HealthRecord]:
        user = self._user(user_id)
        return sorted(user.healthkit_records + user.manual_entries, key=lambda r: r.timestamp)

    def add_feedback(self, user_id: str, feedback: Feedback) -> None:
        self._user(user_id).feedback.append(feedback)

    def add_social_post(self, user_id: str, share: SocialShare) -> None:
        self._user(user_id).social_posts.append(share)

    def stats(self) -> Dict[str, int]:
        return {"users": len(self._data), "profiles": len(self._profiles)}

    def record_analysis_usage(self, user_id: str) -> Tuple[int, Optional[int]]:
        profile = self._profiles.setdefault(user_id, UserProfile(provider="unknown", external_id=user_id))
        today = datetime.utcnow().date().isoformat()
        if profile.last_usage_day != today:
            profile.last_usage_day = today
            profile.usage_count_today = 0
        profile.usage_count_today += 1
        if profile.subscription_tier == "free":
            remaining = 3 - profile.usage_count_today
            return profile.usage_count_today, remaining
        return profile.usage_count_today, None
