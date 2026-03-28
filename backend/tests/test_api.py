from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_dashboard_endpoint():
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    body = response.json()
    assert body["hero_deal_id"] == "deal-apex-expansion"
    assert len(body["metrics"]) == 4


def test_runtime_endpoint_defaults_to_mock():
    response = client.get("/api/runtime")
    assert response.status_code == 200
    body = response.json()
    assert body["crm_provider"] == "mock"
    assert body["live_crm_connected"] is False


def test_deal_intelligence_generates_actions():
    response = client.post("/api/agents/deal-intelligence/analyze", json={"deal_id": "deal-apex-expansion"})
    assert response.status_code == 200
    body = response.json()
    assert body["agent_type"] == "deal_intelligence"
    assert len(body["actions"]) >= 2


def test_execute_action_creates_task():
    insight = client.post("/api/agents/prospect", json={"deal_id": "deal-apex-expansion"}).json()
    action = next(item for item in insight["actions"] if item["type"] == "create_task")
    response = client.post("/api/agents/action/execute", json={"action": action})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "applied"
