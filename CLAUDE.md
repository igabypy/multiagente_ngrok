# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Multi-agent Q&A system ("Entropia QA") that classifies questions into domains (Legal, Accounting, Medical, Generic) and routes them to specialized LLM agents. Built with LangGraph + FastAPI + Supabase, using OpenAI's gpt-4o model. The project is in Spanish.

## Architecture

The project is split into two independent services:

- **Backend/** — FastAPI + LangGraph multi-agent system + Supabase persistence
- **Frontend/** — Vanilla HTML/CSS/JS chat UI served via nginx

Both run in Docker containers orchestrated by `docker-compose.yml` at the root.

## Commands

All development happens inside containers:

```bash
# Start all services (backend + frontend)
docker compose up -d

# Rebuild after changes
docker compose up -d --build

# Run tests (inside backend container)
docker compose exec backend pytest tests/ -v

# View backend logs
docker compose logs -f backend

# Open shell in backend
docker compose exec backend bash
```

Or use the Makefile from `Backend/`:
```bash
cd Backend
make start      # docker compose up
make test       # pytest inside container
make logs       # backend logs
make shell      # bash inside container
make rebuild    # rebuild + restart
```

## Key Entry Points

- `Backend/app/main.py` — FastAPI app (`api`), endpoints: POST /qa, GET /history/{session_id}, GET /health
- `Backend/app/agents/graph.py` — LangGraph StateGraph, exports `app_agent`
- `Backend/app/agents/nodes.py` — classify_node, domain_node, router, QAState, format_history
- `Backend/app/services/qa_service.py` — Orchestrates agent invocation + conversation memory
- `Backend/app/db/supabase_client.py` — Supabase CRUD (save_message, get_history)
- `Frontend/src/js/chat.js` — Chat UI logic, session management, API calls via `/api/`

## Data Flow

```
POST /qa → qa_service.ask_question()
  → get_history() + format_history()
  → save_message(user)
  → app_agent.invoke({question, history_text})
    → classify_node → router → domain_node
  → save_message(assistant)
  → return Answer
```

## Environment

Requires in `Backend/.env`:
- `OPENAI_API_KEY` — OpenAI API key
- `SUPABASE_URL` — Supabase project URL
- `SUPABASE_KEY` — Supabase anon key

## Testing

- Tests mock LLM and Supabase to avoid real API calls
- `tests/test_endpoints.py` — FastAPI endpoint tests (patches qa_service)
- `tests/test_graph.py` — LangGraph node and utility tests (patches chains)
- `tests/test_supabase.py` — Supabase client tests (patches create_client)

## Subagents

Three specialized Claude Code agents in `.claude/agents/`:
- **backend** (blue) — FastAPI, LangGraph, LangChain, Supabase, pytest
- **frontend** (red) — HTML/CSS/JS, chat UI, nginx, responsive design
- **architect** (yellow) — System design, graph topology, prompt strategy, specs
