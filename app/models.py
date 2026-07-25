from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_id: str = Field(..., description="Unique user id from mini-program openid/unionid.")
    session_id: str = Field(..., description="Conversation session id.")
    message: str = Field(..., min_length=1, description="Current user input.")
    venue_id: Optional[str] = Field(default=None, description="Optional venue id, such as nuanquan_ancient_town.")
    location: Optional[str] = Field(default=None, description="Optional location context.")
    weather: Optional[str] = Field(default=None, description="Optional weather context.")
    step_rate: Optional[float] = Field(default=None, description="Optional steps per minute.")
    facial_emotion: Optional[str] = Field(default=None, description="Optional expression emotion signal.")


class RecommendationCard(BaseModel):
    id: str
    type: str
    title: str
    subtitle: str = ""
    description: str = ""
    reason: str = ""
    action_label: str = "查看"
    priority: float = 0.5
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, object] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    answer: str
    memory_summary: str
    profile: Dict[str, str]
    recommendations: List[str]
    recommendation_cards: List[RecommendationCard] = Field(default_factory=list)
    intent_state: Dict[str, object] = Field(default_factory=dict)
    ab_variant: str = "control"
    safety_guardrails: List[str] = Field(default_factory=list)


class Turn(BaseModel):
    role: str
    text: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class UserProfile(BaseModel):
    user_id: str
    preferences: Dict[str, str] = Field(default_factory=dict)
    travel_style: str = "balanced"
    budget_level: str = "medium"
    risk_preference: str = "normal"


class AnalyticsEvent(BaseModel):
    user_id: str
    session_id: str
    event_type: str
    metadata: Dict[str, str | float | int] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class EventRequest(BaseModel):
    user_id: str
    session_id: str
    event_type: str
    theme: Optional[str] = None
    poi_id: Optional[str] = None
    dwell_seconds: Optional[int] = None
    clicked: Optional[int] = None
    converted: Optional[int] = None
    metadata: Dict[str, str | float | int] = Field(default_factory=dict)


class SessionEventRequest(BaseModel):
    user_id: str
    session_id: str
    venue_id: str = "nuanquan_ancient_town"
    event_type: str
    spot_id: Optional[str] = None
    content: Optional[str] = None
    value: Optional[int | float | str] = None
    metadata: Dict[str, str | float | int | bool] = Field(default_factory=dict)


class SessionMemory(BaseModel):
    session_id: str
    user_id: str
    venue_id: str
    current_spot_id: Optional[str] = None
    visit_stage: str = "entry"
    recent_messages: List[Dict[str, str]] = Field(default_factory=list)
    visited_spots: List[str] = Field(default_factory=list)
    stay_time_by_spot: Dict[str, int] = Field(default_factory=dict)
    interest_signals: Dict[str, float] = Field(default_factory=dict)
    negative_signals: Dict[str, float] = Field(default_factory=dict)
    accepted_actions: List[str] = Field(default_factory=list)
    dismissed_actions: List[str] = Field(default_factory=list)
    last_triggered_rule_ids: List[str] = Field(default_factory=list)
    last_service_at: Optional[datetime] = None


class ContextSnapshot(BaseModel):
    user_id: str
    session_id: str
    venue_id: str = "nuanquan_ancient_town"
    current_spot_id: Optional[str] = None
    location_text: Optional[str] = None
    visit_stage: str = "entry"
    available_time_minutes: Optional[int] = None
    group_type: Optional[str] = None
    weather: Optional[str] = None
    dwell_seconds: Optional[int] = None
    recent_intent: Optional[str] = None
    interest_top: List[str] = Field(default_factory=list)
    fatigue_level: str = "low"
    disturbance_risk: str = "low"


class ProactiveDecisionRequest(BaseModel):
    user_id: str
    session_id: str
    venue_id: str = "nuanquan_ancient_town"
    current_spot_id: Optional[str] = None
    location_text: Optional[str] = None
    context: Dict[str, str | float | int | bool | List[str]] = Field(default_factory=dict)


class ProactiveDecision(BaseModel):
    decision_id: str
    mode: str = "silent"
    action: str = "observe"
    venue_id: str
    spot_id: Optional[str] = None
    rule_id: Optional[str] = None
    title: str = ""
    message: str = ""
    primary_button: Optional[str] = None
    secondary_button: Optional[str] = "先不用"
    payload: Dict[str, str | float | int | bool | List[str]] = Field(default_factory=dict)
    priority: float = 0.0
    expires_in_seconds: int = 120
    status: str = "observe"


class FeatureSnapshot(BaseModel):
    user_id: str
    topic_distribution: Dict[str, float] = Field(default_factory=dict)
    hour_preference: Dict[str, int] = Field(default_factory=dict)
    geo_hotspots: Dict[str, int] = Field(default_factory=dict)
    session_stage: str = "start"


class IntentState(BaseModel):
    primary_intent: str
    secondary_intent: str
    confidence: float
    actionability: str
    priors: Dict[str, float] = Field(default_factory=dict)



