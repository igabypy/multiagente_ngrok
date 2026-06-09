import uuid

from app.agents.graph import app_agent
from app.agents.nodes import QAState, format_history
from app.db.supabase_client import save_message, get_history


def ask_question(question: str, session_id: str | None = None) -> dict:
    session_id = session_id or uuid.uuid4().hex

    # Load and format conversation history
    history = get_history(session_id)
    history_text = format_history(history)

    # Save user message
    save_message(session_id, "user", question)

    # Invoke agent graph
    res: QAState = app_agent.invoke({
        "question": question,
        "history_text": history_text,
    })

    # Save assistant response
    save_message(session_id, "assistant", res["answer"], res["category_label"])

    return {
        "question": question,
        "session_id": session_id,
        "category_id": res["category_id"],
        "category_label": res["category_label"],
        "answer": res["answer"],
    }
