from unittest.mock import MagicMock, patch
import pytest


@pytest.fixture(autouse=True)
def reset_client():
    import app.db.supabase_client as mod
    mod._client = None
    yield
    mod._client = None


@pytest.fixture
def mock_supabase():
    mock_client = MagicMock()
    with patch("app.db.supabase_client.create_client", return_value=mock_client):
        with patch("app.db.supabase_client.SUPABASE_URL", "https://fake.supabase.co"):
            with patch("app.db.supabase_client.SUPABASE_KEY", "fake-key"):
                yield mock_client


def test_save_message(mock_supabase):
    from app.db.supabase_client import save_message

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
    from app.db.supabase_client import save_message

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
    from app.db.supabase_client import get_history

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
    from app.db.supabase_client import get_client
    import app.db.supabase_client as mod

    with patch.object(mod, "SUPABASE_URL", ""):
        with patch.object(mod, "SUPABASE_KEY", ""):
            with pytest.raises(RuntimeError, match="SUPABASE_URL"):
                get_client()
