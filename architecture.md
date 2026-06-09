# Arquitectura — Entropia QA

## Diagrama General

```
┌─────────────────────┐
│     Frontend         │
│  (nginx:alpine)      │
│  HTML / CSS / JS     │
│  Puerto: 3000        │
└────────┬────────────┘
         │ /api/*
         │ (proxy reverso)
         ▼
┌─────────────────────┐
│     Backend          │
│  (python:3.11-slim)  │
│  FastAPI + LangGraph │
│  Puerto: 8000        │
└────────┬────────────┘
         │
    ┌────┴─────┐
    ▼          ▼
┌────────┐ ┌──────────┐
│ OpenAI │ │ Supabase │
│ gpt-4o │ │ Postgres │
└────────┘ └──────────┘
```

## Stack Técnico

| Capa       | Tecnología                    | Ubicación       |
|------------|-------------------------------|-----------------|
| Frontend   | HTML5, CSS3, JS vanilla       | `Frontend/`     |
| Web Server | nginx:alpine                  | `Frontend/`     |
| API        | FastAPI, Pydantic             | `Backend/app/`  |
| Agentes    | LangGraph, LangChain, LCEL    | `Backend/app/agents/` |
| Persistencia | Supabase (PostgreSQL)       | `Backend/app/db/` |
| LLM        | OpenAI gpt-4o                | Externo         |
| Contenedores | Docker Compose              | Raíz            |

## Flujo del Grafo Multi-Agente

```
                    ┌─────────────┐
     Pregunta ────▶ │ Clasificador │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┬────────────┐
              ▼            ▼            ▼            ▼
         ┌────────┐  ┌──────────┐ ┌─────────┐ ┌──────────┐
         │ Legal  │  │ Contable │ │ Médico  │ │ Genérico │
         │ (id=1) │  │ (id=2)   │ │ (id=3)  │ │ (id=4)   │
         └────┬───┘  └────┬─────┘ └────┬────┘ └────┬─────┘
              │            │            │            │
              └────────────┴────────────┴────────────┘
                           │
                           ▼
                      Respuesta
```

## Modelo de Datos (Supabase)

```sql
conversations (
    id          bigint PRIMARY KEY,
    session_id  text,           -- UUID hex, indexado
    role        text,           -- "user" | "assistant"
    content     text,           -- Texto del mensaje
    category_label text NULL,   -- "Legal" | "Contable" | "Médica" | "Genérica"
    created_at  timestamptz DEFAULT now()
)
```

## Estructura del Proyecto

```
multiagente_ngrok_memoria/
├── Backend/
│   ├── app/
│   │   ├── main.py              # FastAPI endpoints
│   │   ├── core/config.py       # Environment settings
│   │   ├── agents/
│   │   │   ├── graph.py         # LangGraph StateGraph → app_agent
│   │   │   ├── nodes.py         # Nodos, router, QAState
│   │   │   └── prompts/         # Prompts por dominio
│   │   ├── db/supabase_client.py
│   │   ├── schemas/qa.py        # Pydantic models
│   │   └── services/qa_service.py
│   ├── tests/
│   ├── Dockerfile
│   ├── Makefile
│   └── .env
├── Frontend/
│   ├── src/                     # HTML, CSS, JS
│   ├── nginx.conf               # Proxy reverso
│   └── Dockerfile
├── .claude/agents/              # Subagentes Claude Code
├── spec/                        # Planes de implementación
├── docker-compose.yml           # Orquesta backend + frontend
└── CLAUDE.md
```

## Patrones Importantes

- **Todo en contenedor**: El desarrollo se hace dentro de Docker (Makefile wrappea docker compose)
- **Proxy reverso**: Frontend llama `/api/*` → nginx lo enruta a `backend:8000/`
- **Memoria conversacional**: Últimos 10 turnos inyectados como `{history}` en los prompts
- **Tests sin LLM**: Todos los tests mockean ChatOpenAI y Supabase
- **LCEL chains**: `prompt | llm` para cada agente de dominio
