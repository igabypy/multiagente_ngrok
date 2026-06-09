from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.schemas.qa import Question, Answer, MessageRecord
from app.services.qa_service import ask_question
from app.db.supabase_client import get_history

api = FastAPI(title="Entropia QA")

api.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@api.get("/health")
def health():
    return {"status": "ok"}


@api.post("/qa", response_model=Answer)
def ask(q: Question):
    if not q.question.strip():
        raise HTTPException(status_code=400, detail="Empty question")

    return ask_question(q.question, q.session_id)


@api.get("/history/{session_id}", response_model=list[MessageRecord])
def history(session_id: str):
    return get_history(session_id)
