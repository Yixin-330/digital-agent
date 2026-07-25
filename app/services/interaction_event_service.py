from __future__ import annotations

from datetime import datetime
from typing import Dict, List
from uuid import uuid4

from app.models import SessionEventRequest
from app.services.session_memory_service import SessionMemoryService


class InteractionEventService:
    """Stores visit events and turns them into session-memory updates."""

    def __init__(self, session_memory: SessionMemoryService) -> None:
        self.session_memory = session_memory
        self._events: List[Dict[str, object]] = []

    def record(self, req: SessionEventRequest) -> Dict[str, object]:
        event = {
            "event_id": f"evt_{uuid4().hex[:10]}",
            "user_id": req.user_id,
            "session_id": req.session_id,
            "venue_id": req.venue_id,
            "event_type": req.event_type,
            "spot_id": req.spot_id,
            "content": req.content,
            "value": req.value,
            "metadata": req.metadata,
            "created_at": datetime.utcnow().isoformat(),
        }
        self._events.append(event)
        memory = self._apply_to_memory(req)
        return {"event": event, "session_memory": memory}

    def list_events(self, session_id: str) -> List[Dict[str, object]]:
        return [event for event in self._events if event["session_id"] == session_id]

    def _apply_to_memory(self, req: SessionEventRequest):
        event_type = req.event_type
        if event_type in {"chat", "user_message"} and req.content:
            return self.session_memory.update_message(
                req.user_id,
                req.session_id,
                req.venue_id,
                "user",
                req.content,
            )
        if event_type in {"enter_spot", "enter_poi"} and req.spot_id:
            return self.session_memory.enter_spot(req.user_id, req.session_id, req.venue_id, req.spot_id)
        if event_type == "enter_venue":
            return self.session_memory.set_visit_stage(req.user_id, req.session_id, req.venue_id, "entry")
        if event_type in {"leave_venue", "leaving"}:
            return self.session_memory.set_visit_stage(req.user_id, req.session_id, req.venue_id, "leaving")
        if event_type == "dwell":
            dwell_seconds = int(req.value or req.metadata.get("dwell_seconds", 0) or 0)
            return self.session_memory.update_dwell(
                req.user_id,
                req.session_id,
                req.venue_id,
                req.spot_id,
                dwell_seconds,
            )
        if event_type in {"accept", "action_accept"}:
            action = str(req.metadata.get("action", req.value or "unknown"))
            return self.session_memory.mark_action(req.user_id, req.session_id, req.venue_id, action, accepted=True)
        if event_type in {"skip", "dismiss", "action_dismiss"}:
            action = str(req.metadata.get("action", req.value or "unknown"))
            return self.session_memory.mark_action(req.user_id, req.session_id, req.venue_id, action, accepted=False)
        if event_type == "task_complete":
            action = str(req.metadata.get("action", "trigger_interactive_task"))
            memory = self.session_memory.mark_action(req.user_id, req.session_id, req.venue_id, action, accepted=True)
            task_topic = str(req.metadata.get("topic", "task"))
            memory.interest_signals[task_topic] = min(1.0, memory.interest_signals.get(task_topic, 0.0) + 0.3)
            return memory
        return self.session_memory.get_or_create(req.user_id, req.session_id, req.venue_id)
