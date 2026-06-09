import pytest

from fastapi.testclient import TestClient

from app.main import api
import app.main as main_mod


@pytest.fixture(autouse=True)
def patch_service(monkeypatch):
    """Patch the service layer to avoid real LLM and Supabase calls."""
    dummy_result = {
        "question": "test",
        "session_id": "abc123",
        "category_id": 4,
        "category_label": "Genérica",
        "answer": "Respuesta simulada",
    }
    monkeypatch.setattr(
        main_mod, "ask_question",
        lambda q, sid=None: {**dummy_result, "question": q, "session_id": sid or "abc123"},
    )
    monkeypatch.setattr(
        main_mod, "get_history",
        lambda sid, **kw: [],
    )


def test_qa_success():
    client = TestClient(api)
    resp = client.post("/qa", json={"question": "Algo?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["category_id"] == 4
    assert data["answer"] == "Respuesta simulada"
    assert "session_id" in data


def test_qa_empty_question():
    client = TestClient(api)
    resp = client.post("/qa", json={"question": "   "})
    assert resp.status_code == 400
    assert "Empty question" in resp.json()["detail"]


def test_qa_preserves_session_id():
    client = TestClient(api)
    resp = client.post("/qa", json={"question": "Hola", "session_id": "mi-sesion-123"})
    assert resp.status_code == 200
    assert resp.json()["session_id"] == "mi-sesion-123"


def test_history_endpoint():
    client = TestClient(api)
    resp = client.get("/history/test-session")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_health():
    client = TestClient(api)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
