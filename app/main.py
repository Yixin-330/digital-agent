from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.decision.proactive_decision_service import ProactiveDecisionService
from app.models import ChatRequest, ChatResponse, EventRequest, ProactiveDecisionRequest, SessionEventRequest
from app.services.agent_service import WenlvAgentService
from app.services.analytics_service import AnalyticsService
from app.services.interaction_event_service import InteractionEventService
from app.services.memory_store import MemoryStore
from app.services.profile_service import ProfileService
from app.services.recommendation_service import RecommendationService
from app.services.session_memory_service import SessionMemoryService

app = FastAPI(title="Wenlv Digital Human Agent", version="0.1.0")
demo_dir = Path(__file__).resolve().parent.parent / "frontend-demo"
if demo_dir.exists():
    app.mount("/demo", StaticFiles(directory=demo_dir, html=True), name="demo")

memory_store = MemoryStore()
profile_service = ProfileService()
analytics_service = AnalyticsService()
recommendation_service = RecommendationService()
session_memory_service = SessionMemoryService(venue_data=recommendation_service.venue_data)
interaction_event_service = InteractionEventService(session_memory=session_memory_service)
proactive_decision_service = ProactiveDecisionService(
    venue_data=recommendation_service.venue_data,
    session_memory=session_memory_service,
)
agent_service = WenlvAgentService(
    memory_store=memory_store,
    profile_service=profile_service,
    analytics_service=analytics_service,
    recommendation_service=recommendation_service,
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/v1/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    resolved_venue_id = recommendation_service.venue_data.infer_venue_id(req.venue_id, req.location, req.message)
    session_memory_service.update_message(
        req.user_id,
        req.session_id,
        resolved_venue_id or req.venue_id or "nuanquan_ancient_town",
        "user",
        req.message,
    )
    return agent_service.chat(req)



@app.get("/api/v1/venues")
def list_venues() -> dict:
    return {"venues": recommendation_service.venue_data.list_venues()}


@app.post("/api/v1/session/events")
def record_session_event(req: SessionEventRequest) -> dict:
    result = interaction_event_service.record(req)
    memory = result["session_memory"]
    decision = proactive_decision_service.decide(
        ProactiveDecisionRequest(
            user_id=req.user_id,
            session_id=req.session_id,
            venue_id=req.venue_id,
            current_spot_id=req.spot_id,
            context={
                "dwell_seconds": req.value if req.event_type == "dwell" and isinstance(req.value, (int, float)) else 0,
                **req.metadata,
            },
        )
    )
    return {
        "status": "ok",
        "event": result["event"],
        "session_memory": memory.model_dump(),
        "next_decision": decision.model_dump(),
    }


@app.get("/api/v1/session/{session_id}/memory")
def get_session_memory(session_id: str) -> dict:
    memory = session_memory_service.get(session_id)
    return {"session_id": session_id, "memory": memory.model_dump() if memory else None}


@app.post("/api/v1/proactive/decision")
def proactive_decision(req: ProactiveDecisionRequest) -> dict:
    decision = proactive_decision_service.decide(req)
    return {"decision": decision.model_dump()}
@app.get("/api/v1/users/{user_id}/profile")
def get_profile(user_id: str) -> dict:
    profile = profile_service.get_or_create(user_id)
    return profile.model_dump()


@app.get("/api/v1/users/{user_id}/recommendations")
def get_recommendations(
    user_id: str,
    location: str | None = None,
    weather: str | None = None,
    venue_id: str | None = None,
) -> dict:
    profile = profile_service.get_or_create(user_id)
    recommendations = recommendation_service.recommend(profile, location, weather, venue_id=venue_id)
    cards = recommendation_service.recommend_cards(profile, location, weather, venue_id=venue_id)
    return {
        "user_id": user_id,
        "recommendations": recommendations,
        "recommendation_cards": [card.model_dump() for card in cards],
    }


@app.get("/api/v1/users/{user_id}/analytics")
def get_analytics(user_id: str) -> dict:
    report = analytics_service.user_report(user_id)
    return {"user_id": user_id, **report}


@app.post("/api/v1/events")
def track_event(req: EventRequest) -> dict:
    analytics_service.track_event_request(req)
    if req.event_type == "feedback":
        agent_service.bandit.reward(
            user_id=req.user_id,
            clicked=int(req.clicked or 0),
            converted=int(req.converted or 0),
            dwell_seconds=int(req.dwell_seconds or 0),
        )
        variant = agent_service.ab.assign_variant(req.user_id)
        key = "ctr_control" if variant == "control" else "ctr_treatment"
        if req.clicked:
            agent_service.metrics.inc(key, 1.0)
    return {"status": "ok"}


@app.get("/api/v1/users/{user_id}/features")
def get_features(user_id: str, session_id: str) -> dict:
    feature = analytics_service.build_feature_snapshot(user_id, session_id)
    graph_features = agent_service.interest_graph.get_features(user_id)
    return {"feature_snapshot": feature.model_dump(), "interest_graph": graph_features}


@app.get("/api/v1/knowledge/grounded-answer")
def grounded_answer(query: str) -> dict:
    return agent_service.graph_rag.grounded_answer(query)


@app.post("/api/v1/ops/export-training-samples")
def export_samples(path: str = "artifacts/training_samples.json") -> dict:
    return analytics_service.export_training_samples(path)


@app.get("/api/v1/ops/ab-report")
def ab_report() -> dict:
    return {
        "metrics": agent_service.metrics.report(),
        "guardrail": agent_service.metrics.online_guardrail(),
    }





