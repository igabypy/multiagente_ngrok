from pydantic import BaseModel


class Question(BaseModel):
    question: str
    session_id: str | None = None


class Answer(BaseModel):
    question: str
    session_id: str
    category_id: int
    category_label: str
    answer: str


class MessageRecord(BaseModel):
    role: str
    content: str
    category_label: str | None = None
    created_at: str | None = None
