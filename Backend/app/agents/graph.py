from pathlib import Path

from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

from app.core.config import MODEL_NAME, MODEL_TEMPERATURE
from app.agents.nodes import (
    QAState,
    load_chat_prompt,
    classify_node,
    domain_node,
    router,
)

PROMPTS_DIR = Path(__file__).parent / "prompts"

# LLM instance
llm = ChatOpenAI(model_name=MODEL_NAME, temperature=MODEL_TEMPERATURE)

# LCEL chains: prompt | llm
classifier_chain = load_chat_prompt(PROMPTS_DIR, "classifier") | llm
domain_chains = {
    1: load_chat_prompt(PROMPTS_DIR, "legal") | llm,
    2: load_chat_prompt(PROMPTS_DIR, "accounting") | llm,
    3: load_chat_prompt(PROMPTS_DIR, "medical") | llm,
    4: load_chat_prompt(PROMPTS_DIR, "generic") | llm,
}

# Build state graph
graph = StateGraph(state_schema=QAState)

graph.add_node("classifier", classify_node(classifier_chain))

for idx, ch in domain_chains.items():
    name = {1: "legal", 2: "accounting", 3: "medical", 4: "generic"}[idx]
    graph.add_node(name, domain_node(ch))

graph.add_conditional_edges("classifier", router)
for dom in ("legal", "accounting", "medical", "generic"):
    graph.add_edge(dom, END)

graph.set_entry_point("classifier")
app_agent = graph.compile()
