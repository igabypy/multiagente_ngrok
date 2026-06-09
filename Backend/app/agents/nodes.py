import json
import re
from typing import TypedDict

from langchain_core.prompts import (
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
)

from app.core.config import MAX_HISTORY_TURNS

# System message to enforce Spanish
system_es = SystemMessagePromptTemplate.from_template(
    "Eres un asistente que RESPONDE SIEMPRE EN ESPAÑOL, SIN MEZCLAR OTROS IDIOMAS."
)


class QAState(TypedDict):
    question: str
    category_id: int
    category_label: str
    answer: str
    history_text: str


def load_chat_prompt(prompts_dir, name: str) -> ChatPromptTemplate:
    text = (prompts_dir / f"{name}.txt").read_text(encoding="utf-8")
    human = HumanMessagePromptTemplate.from_template(text)
    return ChatPromptTemplate.from_messages([system_es, human])


def format_history(history: list[dict]) -> str:
    if not history:
        return ""
    lines = ["Historial de conversación:"]
    for msg in history[-MAX_HISTORY_TURNS * 2:]:
        role = "Usuario" if msg.get("role") == "user" else "Asistente"
        lines.append(f"  {role}: {msg.get('content', '')}")
    return "\n".join(lines)


def classify_node(classifier_chain):
    def _node(state: QAState) -> QAState:
        history_text = state.get("history_text") or ""
        result = classifier_chain.invoke({
            "question": state["question"],
            "history": history_text,
        })
        raw = result.content.strip()

        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            json_str = match.group(0)
            try:
                parsed = json.loads(json_str)
                state["category_id"] = int(parsed.get("id", 4))
                label_map = {1: "Legal", 2: "Contable", 3: "Médica", 4: "Genérica"}
                state["category_label"] = parsed.get("label", label_map[state["category_id"]])
                return state
            except json.JSONDecodeError:
                pass

        state["category_id"] = 4
        state["category_label"] = "Genérica"
        return state

    return _node


def domain_node(chain):
    def _node(state: QAState) -> QAState:
        history_text = state.get("history_text") or ""
        result = chain.invoke({
            "question": state["question"],
            "history": history_text,
        })
        state["answer"] = result.content
        return state
    return _node


def router(state: QAState) -> str:
    return {1: "legal", 2: "accounting", 3: "medical"}.get(state["category_id"], "generic")
