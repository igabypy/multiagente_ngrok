# tests/test_supabase_client.py
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))


@pytest.fixture(autouse=True)
def reset_client():
    """Resetea el singleton entre tests."""
    import app.supabase_client as mod
    mod._client = None
    yield
    mod._client = None


@pytest.fixture
def mock_supabase():
    """Provee un mock del cliente Supabase."""
    mock_client = MagicMock()
    with patch("app.supabase_client.create_client", return_value=mock_client):
        with patch("app.supabase_client._SUPABASE_URL", "https://fake.supabase.co"):
            with patch("app.supabase_client._SUPABASE_KEY", "fake-key"):
                yield mock_client


def test_save_message(mock_supabase):
    from app.supabase_client import save_message

    fake_row = {
        "session_id": "s1",
        "role": "user",
        "content": "hola",
        "category_label": None,
    }
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [fake_row]

    result = save_message("s1", "user", "hola")
    assert result["session_id"] == "s1"
    assert result["role"] == "user"
    mock_supabase.table.assert_called_with("conversations")


def test_save_message_with_category(mock_supabase):
    from app.supabase_client import save_message

    fake_row = {
        "session_id": "s1",
        "role": "assistant",
        "content": "respuesta",
        "category_label": "Legal",
    }
    mock_supabase.table.return_value.insert.return_value.execute.return_value.data = [fake_row]

    result = save_message("s1", "assistant", "respuesta", "Legal")
    assert result["category_label"] == "Legal"


def test_get_history(mock_supabase):
    from app.supabase_client import get_history

    fake_data = [
        {"role": "user", "content": "pregunta", "category_label": None, "created_at": "2025-01-01"},
        {"role": "assistant", "content": "respuesta", "category_label": "Legal", "created_at": "2025-01-01"},
    ]
    chain = mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value
    chain.execute.return_value.data = fake_data

    result = get_history("s1")
    assert len(result) == 2
    assert result[0]["role"] == "user"
    assert result[1]["category_label"] == "Legal"


def test_get_client_raises_without_env():
    from app.supabase_client import get_client
    import app.supabase_client as mod

    mod._SUPABASE_URL = ""
    mod._SUPABASE_KEY = ""
    with pytest.raises(RuntimeError, match="SUPABASE_URL"):
        get_client()
