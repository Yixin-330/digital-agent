from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from app.models import SessionMemory
from app.services.venue_data_service import VenueDataService


class SessionMemoryService:
    """Short-term memory for the current visit session."""

    def __init__(self, venue_data: VenueDataService | None = None) -> None:
        self._sessions: Dict[str, SessionMemory] = {}
        self.venue_data = venue_data or VenueDataService()

    def get_or_create(self, user_id: str, session_id: str, venue_id: str) -> SessionMemory:
        memory = self._sessions.get(session_id)
        if memory:
            return memory
        memory = SessionMemory(user_id=user_id, session_id=session_id, venue_id=venue_id)
        self._sessions[session_id] = memory
        return memory

    def get(self, session_id: str) -> Optional[SessionMemory]:
        return self._sessions.get(session_id)

    def update_message(self, user_id: str, session_id: str, venue_id: str, role: str, text: str) -> SessionMemory:
        memory = self.get_or_create(user_id, session_id, venue_id)
        memory.recent_messages.append(
            {"role": role, "text": text[:300], "created_at": datetime.utcnow().isoformat()}
        )
        memory.recent_messages = memory.recent_messages[-8:]
        self._apply_text_signals(memory, text)
        return memory

    def enter_spot(self, user_id: str, session_id: str, venue_id: str, spot_id: str) -> SessionMemory:
        memory = self.get_or_create(user_id, session_id, venue_id)
        memory.current_spot_id = spot_id
        memory.visit_stage = "exploring"
        if spot_id not in memory.visited_spots:
            memory.visited_spots.append(spot_id)
        self._apply_spot_signals(memory, spot_id)
        return memory

    def update_dwell(
        self,
        user_id: str,
        session_id: str,
        venue_id: str,
        spot_id: Optional[str],
        dwell_seconds: int,
    ) -> SessionMemory:
        memory = self.get_or_create(user_id, session_id, venue_id)
        resolved_spot_id = spot_id or memory.current_spot_id
        if resolved_spot_id:
            memory.current_spot_id = resolved_spot_id
            if resolved_spot_id not in memory.visited_spots:
                memory.visited_spots.append(resolved_spot_id)
            memory.stay_time_by_spot[resolved_spot_id] = max(
                dwell_seconds,
                memory.stay_time_by_spot.get(resolved_spot_id, 0),
            )
            self._apply_spot_signals(memory, resolved_spot_id)
        if dwell_seconds >= 180:
            self._bump(memory.interest_signals, "deep_viewing", 0.25)
        return memory

    def mark_action(self, user_id: str, session_id: str, venue_id: str, action: str, accepted: bool) -> SessionMemory:
        memory = self.get_or_create(user_id, session_id, venue_id)
        target = memory.accepted_actions if accepted else memory.dismissed_actions
        if action not in target:
            target.append(action)
        if accepted:
            self._bump(memory.interest_signals, action, 0.2)
        else:
            self._bump(memory.negative_signals, action, 0.35)
        return memory

    def mark_rule_triggered(self, session_id: str, rule_id: str) -> None:
        memory = self._sessions.get(session_id)
        if not memory:
            return
        if rule_id not in memory.last_triggered_rule_ids:
            memory.last_triggered_rule_ids.append(rule_id)
        memory.last_service_at = datetime.utcnow()

    def set_visit_stage(self, user_id: str, session_id: str, venue_id: str, stage: str) -> SessionMemory:
        memory = self.get_or_create(user_id, session_id, venue_id)
        memory.visit_stage = stage
        return memory

    def top_interests(self, memory: SessionMemory, limit: int = 3) -> List[str]:
        ranked = sorted(memory.interest_signals.items(), key=lambda item: item[1], reverse=True)
        return [name for name, value in ranked[:limit] if value > 0]

    def disturbance_risk(self, memory: SessionMemory) -> str:
        if len(memory.dismissed_actions) >= 2:
            return "high"
        if memory.dismissed_actions or memory.negative_signals:
            return "medium"
        return "low"

    def _apply_text_signals(self, memory: SessionMemory, text: str) -> None:
        mapping = {
            "孩子": ("family", 0.35),
            "亲子": ("family", 0.35),
            "剪纸": ("papercut", 0.35),
            "非遗": ("heritage", 0.3),
            "西古堡": ("architecture", 0.3),
            "古堡": ("architecture", 0.25),
            "历史": ("history", 0.25),
            "打树花": ("performance", 0.35),
            "拍照": ("photography", 0.25),
            "摄影": ("photography", 0.25),
            "纪念品": ("commerce_interest", 0.55),
            "文创": ("commerce_interest", 0.45),
            "不想走": ("long_walk", -0.3),
            "太累": ("fatigue", -0.3),
            "先不用": ("disturbance", -0.35),
        }
        for token, (topic, score) in mapping.items():
            if token in text:
                if score > 0:
                    self._bump(memory.interest_signals, topic, score)
                else:
                    self._bump(memory.negative_signals, topic, abs(score))

    def _apply_spot_signals(self, memory: SessionMemory, spot_id: str) -> None:
        spots = self.venue_data.list_spots(memory.venue_id)
        spot = next((item for item in spots if item.get("id") == spot_id), None)
        if not spot:
            return
        for tag in spot.get("tags", [])[:4]:
            self._bump(memory.interest_signals, str(tag), 0.08)
        for user_type in spot.get("suitable_for", [])[:3]:
            self._bump(memory.interest_signals, str(user_type), 0.08)

    def _bump(self, target: Dict[str, float], key: str, value: float) -> None:
        target[key] = round(min(1.0, target.get(key, 0.0) + value), 4)
