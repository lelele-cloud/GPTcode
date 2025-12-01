"""Lightweight AI orchestration and rule-based fallbacks.

This module simulates the integration point for a large language model
by providing structured prompt builders and deterministic fallbacks for
recommendations. In production, you would swap ``_llm_generate`` with a
call to an actual hosted model.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class HealthSnapshot:
    user_id: str
    steps: int = 0
    resting_heart_rate: Optional[int] = None
    active_minutes: int = 0
    sleep_hours: float = 0.0
    calories: Optional[int] = None
    weight_kg: Optional[float] = None


@dataclass
class Suggestion:
    category: str
    title: str
    detail: str


@dataclass
class ChatMessage:
    role: str
    content: str


class AIEngine:
    """Pseudo AI layer that can be replaced by a real LLM service."""

    def __init__(self) -> None:
        self._history: Dict[str, List[ChatMessage]] = {}

    def chat(self, user_id: str, message: str) -> str:
        history = self._history.setdefault(user_id, [])
        history.append(ChatMessage(role="user", content=message))
        reply = self._llm_generate(history)
        history.append(ChatMessage(role="assistant", content=reply))
        return reply

    def generate_suggestions(self, snapshot: HealthSnapshot) -> List[Suggestion]:
        suggestions: List[Suggestion] = []
        suggestions.extend(self._activity_suggestions(snapshot))
        suggestions.extend(self._sleep_suggestions(snapshot))
        suggestions.extend(self._nutrition_suggestions(snapshot))
        return suggestions

    def trend_warnings(self, trend_points: List[Tuple[str, float]]) -> List[str]:
        warnings: List[str] = []
        for metric, change in trend_points:
            if metric == "sleep_hours" and change <= -1:
                warnings.append("睡眠时间出现明显下降，请尽快排查作息或压力问题。")
            if metric == "resting_heart_rate" and change >= 5:
                warnings.append("静息心率持续升高，建议降低强度并监控恢复情况。")
        return warnings

    def _activity_suggestions(self, snapshot: HealthSnapshot) -> List[Suggestion]:
        target_steps = 8000
        detail = (
            "今天已完成步数 {steps}，建议设定目标 {target} 步，"
            "加入 20 分钟中等强度有氧或 10 分钟力量训练。"
        ).format(steps=snapshot.steps, target=target_steps)
        return [Suggestion(category="activity", title="活动计划", detail=detail)]

    def _sleep_suggestions(self, snapshot: HealthSnapshot) -> List[Suggestion]:
        tips = (
            "昨晚睡眠 {hours:.1f} 小时。保持固定睡前流程，避免睡前使用电子设备，"
            "必要时可进行 5 分钟呼吸放松训练。"
        ).format(hours=snapshot.sleep_hours)
        return [Suggestion(category="sleep", title="睡眠优化", detail=tips)]

    def _nutrition_suggestions(self, snapshot: HealthSnapshot) -> List[Suggestion]:
        tips = "关注蛋白质和蔬菜摄入，三餐保持 40/30/30 的碳水/蛋白质/脂肪比例。"
        if snapshot.weight_kg:
            tips += f" 当前体重 {snapshot.weight_kg:.1f} kg，保持轻度热量缺口。"
        return [Suggestion(category="nutrition", title="饮食建议", detail=tips)]

    def _llm_generate(self, history: List[ChatMessage]) -> str:
        last_user = next((m.content for m in reversed(history) if m.role == "user"), "")
        return (
            "你是个人化健康助理。我收到的信息是："
            f"{last_user}。结合运动、睡眠、饮食给出一句实用建议。"
        )
