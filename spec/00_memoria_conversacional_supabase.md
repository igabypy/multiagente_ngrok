# 00 — Memoria Conversacional con Supabase

Plan para agregar persistencia de historial de conversaciones al sistema multi-agente, usando Supabase como backend de almacenamiento.

---

## Estado actual

- Cada pregunta en `POST /qa` es **stateless**: no hay sesión ni historial.
- El frontend (`chat.js`) mantiene mensajes solo en el DOM; al recargar se pierden.
- `app/test_supabase.py` ya valida la conexión y operaciones CRUD contra la tabla `conversations`.
- Las variables `SUPABASE_URL` y `SUPABASE_KEY` ya existen en `.env`.

---

## Tabla `conversations` esperada en Supabase

```sql
create table conversations (
  id         bigint generated always as identity primary key,
  session_id text not null,
  role       text not null,          -- 'user' | 'assistant'
  content    text not null,
  category_label text,               -- null para mensajes del usuario
  created_at timestamptz default now()
);

create index idx_conversations_session on conversations (session_id, created_at);
```

> Si la tabla ya existe (el test la usa), verificar que el esquema coincida.

---

## Fases de implementacion

### Fase 1 — Capa de persistencia en backend

**Archivo nuevo:** `app/supabase_client.py`

Responsabilidades:
- Inicializar el cliente Supabase una sola vez (singleton).
- Exponer funciones:
  - `save_message(session_id, role, content, category_label=None)` — inserta un registro.
  - `get_history(session_id, limit=50)` — devuelve los ultimos N mensajes de la sesion ordenados por `created_at`.

**Impacto:**
| Archivo | Cambio |
|---|---|
| `app/supabase_client.py` | Nuevo |
| `app/requirements_multi_agent.txt` | Ya tiene `supabase`; sin cambios |

---

### Fase 2 — Integrar memoria en el endpoint `/qa`

**Archivo:** `app/main_multi_agent.py`

Cambios:
1. El request `Question` recibe un campo opcional `session_id: str | None = None`. Si no llega, el backend genera uno con `uuid4`.
2. Despues de recibir la pregunta, llamar `save_message(session_id, "user", question)`.
3. Despues de obtener la respuesta del agente, llamar `save_message(session_id, "assistant", answer, category_label)`.
4. El response `Answer` incluye el `session_id` para que el frontend lo reuse.

**Nuevo endpoint:** `GET /history/{session_id}`
- Retorna la lista de mensajes de una sesion.
- Modelo de respuesta: `list[MessageRecord]` con campos `role`, `content`, `category_label`, `created_at`.

**Impacto:**
| Archivo | Cambio |
|---|---|
| `app/main_multi_agent.py` | Modificado: nuevos modelos, nuevo endpoint, logica de guardado |
| `app/supabase_client.py` | Consumido aqui |

---

### Fase 3 — Inyectar historial como contexto al agente

**Archivo:** `app/multi_agent.py`

Cambios:
1. Agregar campo `history: list[dict]` al `QAState`.
2. En `classify_node` y en cada `domain_node`, construir el prompt incluyendo los ultimos N turnos del historial para que el LLM tenga contexto conversacional.
3. Ajustar los prompts en `app/prompts/*.txt` para aceptar una variable `{history}` opcional (si viene vacia, se omite).

**Impacto:**
| Archivo | Cambio |
|---|---|
| `app/multi_agent.py` | Modificado: `QAState` extendido, nodos usan historial |
| `app/prompts/legal.txt` | Modificado: variable `{history}` |
| `app/prompts/accounting.txt` | Modificado: variable `{history}` |
| `app/prompts/medical.txt` | Modificado: variable `{history}` |
| `app/prompts/generic.txt` | Modificado: variable `{history}` |
| `app/prompts/classifier.txt` | Modificado: variable `{history}` (para desambiguar preguntas de seguimiento) |
| `app/main_multi_agent.py` | Modificado: cargar historial antes de invocar el agente y pasarlo en el estado |

---

### Fase 4 — Cambios en frontend

**Archivos:** `app/static/js/chat.js`, `app/static/index.html`

Cambios en `chat.js`:
1. Mantener una variable `sessionId` (inicialmente `null`).
2. En `sendMessage`, enviar `{ question, session_id: sessionId }`.
3. Al recibir la respuesta, guardar `sessionId = data.session_id` para los siguientes mensajes.
4. Agregar boton "Nueva conversacion" que resetea `sessionId = null` y limpia el chat.
5. (Opcional) Al cargar la pagina, si hay un `sessionId` en `localStorage`, llamar `GET /history/{sessionId}` y renderizar los mensajes previos.

Cambios en `index.html`:
1. Agregar boton "Nueva conversacion" en el header.
2. (Opcional) Sidebar o dropdown para listar sesiones anteriores.

**Impacto:**
| Archivo | Cambio |
|---|---|
| `app/static/js/chat.js` | Modificado: manejo de sesion, persistencia en localStorage, carga de historial |
| `app/static/index.html` | Modificado: boton nueva conversacion |
| `app/static/css/style.css` | Modificado: estilos del boton nuevo |

---

### Fase 5 — Tests

**Archivos nuevos/modificados en `tests/`**

| Test | Que valida |
|---|---|
| `tests/test_supabase_client.py` (nuevo) | Unit tests de `save_message` y `get_history` con mock del cliente Supabase |
| `tests/test_app_agent.py` (modificar) | Verificar que `/qa` retorna `session_id`, que `/history/{id}` funciona, que mensajes se persisten (mockeando supabase_client) |
| `tests/test_utils.py` (modificar) | Verificar que el historial se inyecta correctamente en los nodos del grafo |

---

## Orden de ejecucion sugerido

```
Fase 1 → Fase 2 → Fase 5 (tests de 1 y 2) → Fase 3 → Fase 4 → Fase 5 (tests de 3)
```

Las fases 1 y 2 dan persistencia sin cambiar el comportamiento del agente. Se pueden desplegar y probar de forma independiente. La fase 3 es la que agrega contexto conversacional real al LLM. La fase 4 puede avanzar en paralelo con la fase 3.

---

## Riesgos y consideraciones

- **Tokens**: inyectar historial largo incrementa el consumo de tokens. Limitar a los ultimos 5-10 turnos.
- **Latencia**: cada request hara 2 llamadas a Supabase (leer historial + guardar). Considerar guardar en background (fire-and-forget) el `save_message` post-respuesta.
- **Seguridad**: el `session_id` viaja desde el frontend; no hay autenticacion. Cualquiera con un session_id puede leer el historial. Para MVP es aceptable, pero documentar como deuda tecnica.
