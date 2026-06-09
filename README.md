# Entropia QA — Sistema Multi-Agente

Sistema multi-agente de preguntas y respuestas que clasifica preguntas en dominios especializados (Legal, Contable, Médico, Genérico) y las dirige al agente apropiado.

---

## Arquitectura

```
Frontend (nginx:3000) ──/api/──▶ Backend (FastAPI:8000) ──▶ OpenAI + Supabase
```

- **Backend/** — FastAPI + LangGraph + Supabase (API, agentes, memoria)
- **Frontend/** — HTML/CSS/JS vanilla servido con nginx (chat UI)

Para más detalles ver [architecture.md](architecture.md).

---

## Requisitos

- **Docker & Docker Compose**
- **Clave de OpenAI** en `Backend/.env`
- **Credenciales Supabase** en `Backend/.env` (para memoria conversacional)

---

## Inicio rápido

```bash
# 1. Configurar variables de entorno
#    Si es la primera vez, copia el ejemplo y edita con tus claves:
cp Backend/.env.example Backend/.env
#    Si ya tienes Backend/.env con tus claves, salta este paso.

# 2. Levantar servicios
docker compose up -d --build

# 3. Abrir en navegador
# Frontend: http://localhost:3000
# API docs: http://localhost:8000/docs
```

---

## Desarrollo

Todo el desarrollo se ejecuta dentro de contenedores:

```bash
# Desde Backend/
make start      # Levantar contenedores
make test       # Ejecutar tests
make logs       # Ver logs del backend
make shell      # Abrir bash en el contenedor
make rebuild    # Reconstruir imagen

# O directamente con docker compose
docker compose up -d
docker compose exec backend pytest tests/ -v
```

---

## Endpoints

| Método | Ruta                    | Descripción                    |
|--------|------------------------|--------------------------------|
| POST   | `/qa`                  | Enviar pregunta al multiagente |
| GET    | `/history/{session_id}` | Historial de conversación      |
| GET    | `/health`              | Estado del servicio             |

---

## Flujo multi-agente

1. **Clasificador** — LLM clasifica la pregunta en 4 categorías
2. **Router** — Edge condicional dirige al nodo de dominio correcto
3. **Agente de dominio** — LLM especialista genera la respuesta
4. **Memoria** — Supabase persiste mensajes, inyectados como contexto

---

## Tests

```bash
docker compose exec backend pytest tests/ -v
```

Tests mockean LLM y Supabase para no requerir conexiones reales.

---

## Estructura

```
├── Backend/           # FastAPI + LangGraph + Supabase
├── Frontend/          # HTML/CSS/JS + nginx
├── .claude/agents/    # Subagentes Claude Code
├── spec/              # Planes de implementación
├── docker-compose.yml # Orquestación
└── architecture.md    # Diagrama de arquitectura
```
