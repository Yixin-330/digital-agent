from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"




def test_venues_endpoint_lists_nuanquan_package():
    response = client.get("/api/v1/venues")
    assert response.status_code == 200
    venues = response.json()["venues"]
    assert any(venue["id"] == "nuanquan_ancient_town" for venue in venues)

def test_chat_returns_intent_and_recommendations():
    response = client.post(
        "/api/v1/chat",
        json={
            "user_id": "u_test_1",
            "session_id": "s_test_1",
            "message": "我想看文物和非遗，顺便规划路线",
            "location": "古城街区",
            "weather": "小雨",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert "answer" in payload
    assert payload["ab_variant"] in ("control", "treatment")
    assert payload["intent_state"]["primary_intent"] in {
        "culture_explore",
        "route_plan",
        "food_discovery",
        "ticket_service",
        "traffic_guide",
    }
    assert len(payload["recommendations"]) >= 1
    assert "recommendation_cards" in payload
    assert len(payload["recommendation_cards"]) >= 1
    assert {"id", "type", "title", "description", "reason"}.issubset(payload["recommendation_cards"][0])



def test_chat_uses_nuanquan_venue_data():
    response = client.post(
        "/api/v1/chat",
        json={
            "user_id": "u_test_nuanquan",
            "session_id": "s_test_nuanquan",
            "venue_id": "nuanquan_ancient_town",
            "message": "我想带孩子在暖泉古镇看西古堡和剪纸，帮我规划路线",
            "location": "暖泉古镇入口",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    joined = "\n".join(payload["recommendations"])
    assert "蔚县暖泉古镇路线" in joined
    assert "西古堡" in joined or "剪纸" in joined
    card_types = {card["type"] for card in payload["recommendation_cards"]}
    assert "route" in card_types


def test_recommendations_endpoint_returns_structured_cards():
    response = client.get(
        "/api/v1/users/u_test_cards/recommendations",
        params={"venue_id": "nuanquan_ancient_town", "location": "暖泉古镇入口"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["recommendations"]) >= 1
    assert len(payload["recommendation_cards"]) >= 1
    first = payload["recommendation_cards"][0]
    assert first["type"] in {"route", "spot", "task", "product", "reminder", "memory_hint"}
    assert first["title"]
    assert "action_label" in first

def test_events_and_ab_report_pipeline():
    chat_response = client.post(
        "/api/v1/chat",
        json={
            "user_id": "u_test_2",
            "session_id": "s_test_2",
            "message": "推荐个博物馆路线",
        },
    )
    assert chat_response.status_code == 200

    event_response = client.post(
        "/api/v1/events",
        json={
            "user_id": "u_test_2",
            "session_id": "s_test_2",
            "event_type": "feedback",
            "theme": "culture",
            "clicked": 1,
            "converted": 0,
            "dwell_seconds": 80,
            "metadata": {"location": "古城街区"},
        },
    )
    assert event_response.status_code == 200
    assert event_response.json()["status"] == "ok"

    report_response = client.get("/api/v1/ops/ab-report")
    assert report_response.status_code == 200
    payload = report_response.json()
    assert "metrics" in payload
    assert "guardrail" in payload


def test_graph_rag_grounded_answer_has_citations():
    response = client.get(
        "/api/v1/knowledge/grounded-answer",
        params={"query": "请介绍暖泉古镇的西古堡和打树花"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "answer" in payload
    assert isinstance(payload["citations"], list)
    assert len(payload["citations"]) >= 1
    assert payload["confidence"] > 0
    assert payload["confidence_label"] in {"较低", "中等", "较高"}
    assert "evidence_summary" in payload
    assert "source_quality" in payload
    assert "source_type" in payload["citations"][0]



def test_graph_rag_unknown_query_has_no_fake_citations():
    response = client.get(
        "/api/v1/knowledge/grounded-answer",
        params={"query": "请介绍一个完全不存在的虚构点位"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["citations"] == []
    assert "未检索到可靠文化证据" in payload["answer"]
    assert payload["confidence"] == 0.0
    assert payload["confidence_label"] == "未命中"


def test_session_event_long_dwell_triggers_proactive_explanation():
    session_id = "s_test_proactive_dwell"
    enter_response = client.post(
        "/api/v1/session/events",
        json={
            "user_id": "u_test_proactive",
            "session_id": session_id,
            "venue_id": "nuanquan_ancient_town",
            "event_type": "enter_spot",
            "spot_id": "spot_xigubao",
        },
    )
    assert enter_response.status_code == 200

    dwell_response = client.post(
        "/api/v1/session/events",
        json={
            "user_id": "u_test_proactive",
            "session_id": session_id,
            "venue_id": "nuanquan_ancient_town",
            "event_type": "dwell",
            "spot_id": "spot_xigubao",
            "value": 240,
        },
    )
    assert dwell_response.status_code == 200
    payload = dwell_response.json()
    decision = payload["next_decision"]
    assert decision["status"] == "trigger"
    assert decision["action"] == "offer_deep_explanation"
    assert decision["mode"] in {"soft_prompt", "card"}

    memory_response = client.get(f"/api/v1/session/{session_id}/memory")
    assert memory_response.status_code == 200
    memory = memory_response.json()["memory"]
    assert memory["current_spot_id"] == "spot_xigubao"
    assert memory["stay_time_by_spot"]["spot_xigubao"] == 240


def test_dismissed_action_silences_repeated_prompt():
    session_id = "s_test_proactive_dismiss"
    client.post(
        "/api/v1/session/events",
        json={
            "user_id": "u_test_dismiss",
            "session_id": session_id,
            "venue_id": "nuanquan_ancient_town",
            "event_type": "skip",
            "value": "offer_deep_explanation",
        },
    )
    response = client.post(
        "/api/v1/proactive/decision",
        json={
            "user_id": "u_test_dismiss",
            "session_id": session_id,
            "venue_id": "nuanquan_ancient_town",
            "current_spot_id": "spot_xigubao",
            "context": {"dwell_seconds": 240},
        },
    )
    assert response.status_code == 200
    decision = response.json()["decision"]
    assert decision["status"] == "observe"
    assert decision["mode"] == "silent"


