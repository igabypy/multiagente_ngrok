# multi_agent/tests/test_app_agent.py
import sys
from pathlib import Path
from unittest.mock import patch
import pytest

from fastapi.testclient import TestClient

# inserta la carpeta padre (multi_agent/) en PYTHONPATH
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

from app.main_multi_agent import api
import app.main_multi_agent as main_mod


@pytest.fixture(autouse=True)
def patch_agent(monkeypatch):
    """Parchea app_agent.invoke y las funciones de Supabase."""
    dummy_response = {
        "category_id": 4,
        "category_label": "Genérica",
        "answer": "Respuesta simulada",
        "history_text": "",
    }
    monkeypatch.setattr(
        main_mod, "app_agent",
        type("A", (), {"invoke": lambda self, x: dummy_response})(),
    )
    monkeypatch.setattr(main_mod, "save_message", lambda *a, **kw: {})
    monkeypatch.setattr(main_mod, "get_history", lambda sid, **kw: [])


def test_api_qa_success():
    """Testea el endpoint /qa con payload válido."""
    client = TestClient(api)
    resp = client.post("/qa", json={"question": "¿Algo?"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["category_id"] == 4
    assert data["category_label"] == "Genérica"
    assert data["answer"] == "Respuesta simulada"
    assert "session_id" in data
    assert len(data["session_id"]) > 0


def test_api_qa_empty_question():
    """Testea que /qa rechace preguntas vacías con 400."""
    client = TestClient(api)
    resp = client.post("/qa", json={"question": "   "})
    assert resp.status_code == 400
    assert "Empty question" in resp.json()["detail"]


def test_api_qa_preserves_session_id():
    """Testea que /qa devuelva el mismo session_id si se envía uno."""
    client = TestClient(api)
    resp = client.post("/qa", json={"question": "Hola", "session_id": "mi-sesion-123"})
    assert resp.status_code == 200
    assert resp.json()["session_id"] == "mi-sesion-123"


def test_api_qa_generates_session_id():
    """Testea que /qa genere un session_id si no se envía."""
    client = TestClient(api)
    resp = client.post("/qa", json={"question": "Hola"})
    assert resp.status_code == 200
    assert resp.json()["session_id"]  # no vacío


def test_history_endpoint():
    """Testea GET /history/{session_id}."""
    client = TestClient(api)
    resp = client.get("/history/test-session")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
