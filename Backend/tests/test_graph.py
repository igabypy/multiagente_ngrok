import json
from unittest.mock import MagicMock
import pytest

from app.agents.nodes import (
    classify_node,
    domain_node,
    router,
    format_history,
)


def _make_fake_chain(content: str):
    mock = MagicMock()
    mock.invoke.return_value = MagicMock(content=content)
    return mock


def test_classify_node_maps_id_and_label():
    fake = _make_fake_chain(json.dumps({"id": 3}))
    node = classify_node(fake)

    state = {"question": "X?", "category_id": None, "category_label": "", "answer": "", "history_text": ""}
    new = node(state.copy())
    assert new["category_id"] == 3
    assert new["category_label"] == "Médica"


def test_classify_node_fallback_on_bad_json():
    fake = _make_fake_chain("no es json")
    node = classify_node(fake)

    state = {"question": "X?", "category_id": None, "category_label": "", "answer": "", "history_text": ""}
    new = node(state.copy())
    assert new["category_id"] == 4
    assert new["category_label"] == "Genérica"


@pytest.mark.parametrize("cat_id,expected", [
    (1, "legal"),
    (2, "accounting"),
    (3, "medical"),
    (42, "generic"),
])
def test_router_returns_correct_node(cat_id, expected):
    state = {"question": "", "category_id": cat_id, "category_label": "", "answer": "", "history_text": ""}
    assert router(state) == expected


def test_domain_node_sets_answer():
    fake_chain = MagicMock()
    fake_chain.invoke.return_value = MagicMock(content="fake answer")

    node = domain_node(fake_chain)
    state = {"question": "hola", "category_id": 4, "category_label": "", "answer": "", "history_text": ""}
    out = node(state.copy())
    assert out["answer"] == "fake answer"


def test_domain_node_passes_history():
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
    assert format_history([]) == ""


def test_format_history_formats_messages():
    history = [
        {"role": "user", "content": "pregunta 1"},
        {"role": "assistant", "content": "respuesta 1"},
    ]
    result = format_history(history)
    assert "Usuario: pregunta 1" in result
    assert "Asistente: respuesta 1" in result
    assert result.startswith("Historial de conversación:")
