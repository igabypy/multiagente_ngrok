from supabase import create_client, Client

from app.core.config import SUPABASE_URL, SUPABASE_KEY

_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is None:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise RuntimeError("SUPABASE_URL y SUPABASE_KEY deben estar en .env")
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


def save_message(
    session_id: str,
    role: str,
    content: str,
    category_label: str | None = None,
) -> dict:
    row = {
        "session_id": session_id,
        "role": role,
        "content": content,
        "category_label": category_label,
    }
    result = get_client().table("conversations").insert(row).execute()
    return result.data[0] if result.data else row


def get_history(session_id: str, limit: int = 50) -> list[dict]:
    result = (
        get_client()
        .table("conversations")
        .select("role, content, category_label, created_at")
        .eq("session_id", session_id)
        .order("created_at")
        .limit(limit)
        .execute()
    )
    return result.data
