from __future__ import annotations

from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.models import ContextSnapshot, ProactiveDecision, ProactiveDecisionRequest, SessionMemory
from app.services.session_memory_service import SessionMemoryService
from app.services.venue_data_service import VenueDataService


class ProactiveDecisionService:
    """Turns venue context rules into low-disturbance service prompts."""

    def __init__(
        self,
        venue_data: VenueDataService,
        session_memory: SessionMemoryService,
    ) -> None:
        self.venue_data = venue_data
        self.session_memory = session_memory

    def decide(self, req: ProactiveDecisionRequest) -> ProactiveDecision:
        memory = self.session_memory.get_or_create(req.user_id, req.session_id, req.venue_id)
        snapshot = self._build_snapshot(req, memory)
        venue = self.venue_data.get_venue(req.venue_id) or {}
        candidates = [
            self._score_rule(rule, snapshot, memory)
            for rule in venue.get("context_rules", [])
        ]
        candidates = [item for item in candidates if item["score"] > 0]
        candidates.sort(key=lambda item: item["score"], reverse=True)
        if not candidates:
            return self._silent(req.venue_id, snapshot.current_spot_id)

        best = candidates[0]
        rule = best["rule"]
        action = str(rule.get("action", "observe"))
        if self._should_silence(action, str(rule.get("id", "")), memory, snapshot):
            return self._silent(req.venue_id, snapshot.current_spot_id)

        decision = self._build_decision(rule, action, best["score"], snapshot, memory)
        if decision.status == "trigger" and decision.rule_id:
            self.session_memory.mark_rule_triggered(req.session_id, decision.rule_id)
        return decision

    def _build_snapshot(self, req: ProactiveDecisionRequest, memory: SessionMemory) -> ContextSnapshot:
        context = req.context
        current_spot_id = req.current_spot_id or self._spot_from_location(req.venue_id, req.location_text) or memory.current_spot_id
        dwell_seconds = self._as_int(context.get("dwell_seconds")) or (
            memory.stay_time_by_spot.get(current_spot_id, 0) if current_spot_id else 0
        )
        group_type = str(context.get("group_type") or "")
        if not group_type and "family" in memory.interest_signals:
            group_type = "family"
        visit_stage = str(context.get("visit_stage") or memory.visit_stage)
        disturbance_risk = self.session_memory.disturbance_risk(memory)
        fatigue_level = "medium" if dwell_seconds >= 240 or "fatigue" in memory.negative_signals else "low"
        if memory.negative_signals.get("fatigue", 0) >= 0.5:
            fatigue_level = "high"
        return ContextSnapshot(
            user_id=req.user_id,
            session_id=req.session_id,
            venue_id=req.venue_id,
            current_spot_id=current_spot_id,
            location_text=req.location_text,
            visit_stage=visit_stage,
            available_time_minutes=self._as_int(context.get("available_time_minutes")),
            group_type=group_type or None,
            weather=str(context.get("weather") or "") or None,
            dwell_seconds=dwell_seconds,
            recent_intent=str(context.get("recent_intent") or "") or None,
            interest_top=self.session_memory.top_interests(memory),
            fatigue_level=fatigue_level,
            disturbance_risk=disturbance_risk,
        )

    def _score_rule(self, rule: Dict[str, Any], snapshot: ContextSnapshot, memory: SessionMemory) -> Dict[str, Any]:
        trigger = rule.get("trigger", {})
        if not isinstance(trigger, dict):
            return {"rule": rule, "score": 0.0}
        score = 0.0

        min_dwell = self._as_int(trigger.get("dwell_time_seconds_gte"))
        if min_dwell:
            if (snapshot.dwell_seconds or 0) < min_dwell:
                return {"rule": rule, "score": 0.0}
            score += 0.35

        if trigger.get("scene") == "entry":
            if snapshot.visit_stage != "entry":
                return {"rule": rule, "score": 0.0}
            score += 0.25

        if trigger.get("persona") == "family":
            if snapshot.group_type != "family" and "family" not in memory.interest_signals:
                return {"rule": rule, "score": 0.0}
            score += 0.35

        if trigger.get("visit_stage") == "leaving":
            if snapshot.visit_stage != "leaving":
                return {"rule": rule, "score": 0.0}
            score += 0.35

        if trigger.get("interest_strength_gte"):
            threshold = float(trigger.get("interest_strength_gte", 0))
            if not memory.interest_signals or max(memory.interest_signals.values()) < threshold:
                return {"rule": rule, "score": 0.0}
            score += 0.25

        tag_score = self._tag_match_score(snapshot.venue_id, snapshot.current_spot_id, trigger.get("spot_tags_any"))
        if trigger.get("spot_tags_any") and tag_score <= 0:
            return {"rule": rule, "score": 0.0}
        score += tag_score

        interest_score = self._interest_match_score(memory, trigger.get("interest_any"))
        if trigger.get("interest_any") and interest_score <= 0:
            return {"rule": rule, "score": 0.0}
        score += interest_score

        if trigger.get("time_relation") == "before_performance":
            if "performance" not in memory.interest_signals and "night_tour" not in memory.interest_signals:
                return {"rule": rule, "score": 0.0}
            score += 0.2

        if not trigger:
            score = 0.05
        return {"rule": rule, "score": min(score, 1.0)}

    def _should_silence(
        self,
        action: str,
        rule_id: str,
        memory: SessionMemory,
        snapshot: ContextSnapshot,
    ) -> bool:
        if rule_id and rule_id in memory.last_triggered_rule_ids:
            return True
        if action in memory.dismissed_actions:
            return True
        if snapshot.disturbance_risk == "high" and action != "recommend_route":
            return True
        if action == "recommend_product_with_reason":
            if snapshot.visit_stage != "leaving" and "commerce_interest" not in memory.interest_signals:
                return True
            if snapshot.disturbance_risk != "low":
                return True
        return False

    def _build_decision(
        self,
        rule: Dict[str, Any],
        action: str,
        score: float,
        snapshot: ContextSnapshot,
        memory: SessionMemory,
    ) -> ProactiveDecision:
        spot = self._spot(snapshot.venue_id, snapshot.current_spot_id)
        spot_name = str(spot.get("name", "这里")) if spot else "这里"
        templates = {
            "recommend_route": {
                "mode": "card",
                "title": "我帮你安排一条顺路路线",
                "message": "可以先走一条轻量路线，把核心点位串起来，后面再根据体力调整。",
                "primary": "查看路线",
            },
            "offer_deep_explanation": {
                "mode": "soft_prompt",
                "title": "这里可以听一个短故事",
                "message": f"你已经来到{spot_name}，我可以用 30 秒讲讲它和暖泉古镇的关系。",
                "primary": "听一段",
            },
            "trigger_interactive_task": {
                "mode": "card",
                "title": "来一个轻任务",
                "message": f"在{spot_name}可以做一个观察任务，适合边走边看，不会占太久。",
                "primary": "开始任务",
            },
            "remind_dashuhua_route": {
                "mode": "soft_prompt",
                "title": "打树花可以提前安排",
                "message": "如果你今晚想看打树花，我可以先帮你把夜游路线和候场节奏排出来，具体时间以现场为准。",
                "primary": "安排夜游",
            },
            "recommend_product_with_reason": {
                "mode": "card",
                "title": "可以收藏一件有文化记忆的小物",
                "message": "结合你这一路关注的主题，我可以推荐和暖泉记忆相关的轻量文创，先收藏也可以。",
                "primary": "看看文创",
            },
        }
        template = templates.get(action, templates["recommend_route"])
        payload: Dict[str, str | float | int | bool | List[str]] = {
            "visit_stage": snapshot.visit_stage,
            "interest_top": snapshot.interest_top,
        }
        candidate_routes = rule.get("candidate_routes")
        if isinstance(candidate_routes, list):
            payload["candidate_routes"] = [str(item) for item in candidate_routes]
        if snapshot.current_spot_id:
            payload["spot_id"] = snapshot.current_spot_id
        return ProactiveDecision(
            decision_id=f"dec_{uuid4().hex[:10]}",
            mode=str(template["mode"]),
            action=action,
            venue_id=snapshot.venue_id,
            spot_id=snapshot.current_spot_id,
            rule_id=str(rule.get("id", "")) or None,
            title=str(template["title"]),
            message=str(template["message"]),
            primary_button=str(template["primary"]),
            secondary_button="先不用",
            payload=payload,
            priority=round(score, 4),
            status="trigger",
        )

    def _silent(self, venue_id: str, spot_id: Optional[str]) -> ProactiveDecision:
        return ProactiveDecision(
            decision_id=f"dec_{uuid4().hex[:10]}",
            mode="silent",
            action="observe",
            venue_id=venue_id,
            spot_id=spot_id,
            title="",
            message="",
            priority=0.0,
            status="observe",
        )

    def _tag_match_score(self, venue_id: str, spot_id: Optional[str], required_tags: Any) -> float:
        if not required_tags or not spot_id:
            return 0.0
        spot = self._spot(venue_id, spot_id)
        if not spot:
            return 0.0
        tags = {str(tag) for tag in spot.get("tags", [])}
        if any(str(tag) in tags for tag in required_tags):
            return 0.25
        return 0.0

    def _interest_match_score(self, memory: SessionMemory, required_interests: Any) -> float:
        if not required_interests:
            return 0.0
        known = set(memory.interest_signals)
        if any(str(item) in known for item in required_interests):
            return 0.25
        return 0.0

    def _spot_from_location(self, venue_id: str, location_text: Optional[str]) -> Optional[str]:
        if not location_text:
            return None
        for spot in self.venue_data.list_spots(venue_id):
            name = str(spot.get("name", ""))
            spot_id = str(spot.get("id", ""))
            if name and name in location_text:
                return spot_id
            if spot_id and spot_id in location_text:
                return spot_id
        return None

    def _spot(self, venue_id: str, spot_id: Optional[str]) -> Optional[Dict[str, Any]]:
        if not spot_id:
            return None
        for spot in self.venue_data.list_spots(venue_id):
            if spot.get("id") == spot_id:
                return spot
        return None

    def _as_int(self, value: object) -> Optional[int]:
        if value is None or value == "":
            return None
        try:
            return int(value)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return None
