# multi_agent/tests/test_utils.py
import sys
from pathlib import Path
import json
from unittest.mock import MagicMock
import pytest

# inserta la carpeta padre (multi_agent/) en PYTHONPATH
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

import app.multi_agent as multi_mod
from app.multi_agent import classify_node, domain_node, router, classifier_chain, domain_chains, format_history


def _make_fake_chain(content: str):
    """Crea un chain falso compatible con .invoke()."""
    mock = MagicMock()
    mock.invoke.return_value = MagicMock(content=content)
    return mock


def test_classify_node_maps_id_and_label(monkeypatch):
    """Verifica que classify_node extraiga category_id y category_label correctamente."""
    fake = _make_fake_chain(json.dumps({"id": 3}))
    monkeypatch.setattr(multi_mod, "classifier_chain", fake)

    state = {"question": "¿X?", "category_id": None, "category_label": "", "answer": "", "history_text": ""}
    new = classify_node(state.copy())
    assert new["category_id"] == 3
    assert new["category_label"] == "Médica"


def test_classify_node_fallback_on_bad_json(monkeypatch):
    """Verifica que classify_node caiga a Genérica si el JSON es inválido."""
    fake = _make_fake_chain("no es json")
    monkeypatch.setattr(multi_mod, "classifier_chain", fake)

    state = {"question": "¿X?", "category_id": None, "category_label": "", "answer": "", "history_text": ""}
    new = classify_node(state.copy())
    assert new["category_id"] == 4
    assert new["category_label"] == "Genérica"


@pytest.mark.parametrize("cat_id,expected", [
    (1, "legal"),
    (2, "accounting"),
    (3, "medical"),
    (42, "generic"),
])
def test_router_returns_correct_node(cat_id, expected):
    """Comprueba que router() enrute según category_id."""
    state = {"question": "", "category_id": cat_id, "category_label": "", "answer": "", "history_text": ""}
    assert router(state) == expected


def test_domain_node_sets_answer():
    """Verifica que domain_node() inserte la respuesta devuelta por el chain."""
    fake_chain = MagicMock()
    fake_chain.invoke.return_value = MagicMock(content="fake answer")

    node = domain_node(fake_chain)
    state = {"question": "hola", "category_id": 4, "category_label": "", "answer": "", "history_text": ""}
    out = node(state.copy())
    assert out["answer"] == "fake answer"


def test_domain_node_passes_history():
    """Verifica que domain_node() pase el historial al chain."""
    captured = {}

    def fake_invoke(params):
        captured.update(params)
        return MagicMock(content="resp")

    fake_chain = MagicMock()
    fake_chain.invoke = fake_invoke

    node = domain_node(fake_chain)
    history_text = "Historial de conversación:\n  Usuario: anterior"
    state = {"question": "hola", "category_id": 4, "category_label": "", "answer": "", "history_text": history_text}
    node(state.copy())
    assert "anterior" in captured["history"]


def test_format_history_empty():
    """format_history con lista vacía devuelve cadena vacía."""
    assert format_history([]) == ""


def test_format_history_formats_messages():
    """format_history genera texto con roles y contenido."""
    history = [
        {"role": "user", "content": "pregunta 1"},
        {"role": "assistant", "content": "respuesta 1"},
    ]
    result = format_history(history)
    assert "Usuario: pregunta 1" in result
    assert "Asistente: respuesta 1" in result
    assert result.startswith("Historial de conversación:")
