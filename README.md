# Agente ReAct con memoria persistente (LangGraph + Gemini)

Agente de razonamiento cíclico (ReAct) que consulta una base de datos simulada de clientes y pedidos. Decide por sí mismo cuándo llamar a sus herramientas, reintenta o pide aclaración ante errores y recuerda la conversación mediante un `thread_id`.

## Requisitos

- Python 3.12+
- API key de Gemini (gratis en https://aistudio.google.com/apikey)

## Instalación

Windows (PowerShell):

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Linux / macOS:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Editá `.env` y colocá tu `GOOGLE_API_KEY`. El archivo `.env` está en `.gitignore` y nunca se sube al repositorio.

## Ejecución

```bash
cd src
python main.py
```

Esto ejecuta tres preguntas con el mismo `thread_id` y genera:

- `traces/ejemplo_traza.json`: traza ReAct de la ejecución.
- `checkpoints.sqlite`: base del checkpointer (ignorada por git).

Para guardar la traza en otro archivo: `python main.py nombre_traza.json`.

## Estructura

```
.
├── src/
│   ├── tools.py    # herramientas con @tool
│   ├── graph.py    # StateGraph + LLM + checkpointer
│   └── main.py     # ejecución async, thread_id y traza
├── traces/         # trazas de ejecución (.json)
├── requirements.txt
├── .env.example
└── README.md
```

## Arquitectura

- **Herramientas (`src/tools.py`):** dos herramientas con `@tool` y docstrings descriptivos: `buscar_cliente_id` (nombre → ID) y `buscar_pedidos` (ID → pedidos, total y detalle). Están encadenadas: una consulta por nombre exige al menos dos llamadas.
- **Grafo (`src/graph.py`):** `StateGraph(MessagesState)` con un nodo `agent` (LLM con `bind_tools`) y un nodo `tools` (`ToolNode`), unidos por la arista condicional `tools_condition`. El ciclo `agent → tools → agent` es el bucle ReAct: el agente decide si llama a una herramienta o responde.
- **Ejecución (`src/main.py`):** entorno asíncrono (`asyncio`), `AsyncSqliteSaver`, `thread_id` por sesión y `recursion_limit=10`.

## Decisiones de diseño

- **`AsyncSqliteSaver` en lugar de `SqliteSaver`:** el `SqliteSaver` síncrono no soporta `ainvoke` (lanza `NotImplementedError`). `AsyncSqliteSaver` es la versión asíncrona del mismo checkpointer SQLite (paquete `langgraph-checkpoint-sqlite`) y permite cumplir el requisito de `asyncio`.
- **`recursion_limit=10`:** evita bucles infinitos y costos inesperados en la API.
- **Docstrings descriptivos:** el LLM elige herramientas únicamente por su descripción.
- **Errores como datos:** las herramientas devuelven `{"error": ...}` en lugar de lanzar excepciones, para que el agente pueda reintentar o pedir aclaración.
- **Timeout y reintentos en el LLM:** resiliencia ante errores transitorios de la API.
- **Modelo:** `gemini-3.1-flash-lite` por defecto, configurable con la variable `GEMINI_MODEL`. Durante el desarrollo algunos modelos más nuevos dieron timeouts (504/503).
- **Secretos:** la API key se lee desde variables de entorno (`python-dotenv`).

## Ejemplo de traza

Ver [`traces/ejemplo_traza.json`](traces/ejemplo_traza.json). Resumen:

1. *"¿Cuántos pedidos tuvo Juan Perez y cuál fue el total?"* → `buscar_cliente_id("Juan Perez")` → `{"cliente_id": 102}` → `buscar_pedidos(102)` → respuesta: 3 pedidos, total 14.500. **Razonamiento multi-paso: 2 llamadas a herramientas.**
2. *"¿Y el último?"* (mismo `thread_id`) → responde desde la memoria, sin llamar herramientas: pedido 9003 del 21/10/2026.
3. *"¿Y los pedidos de Pedro Lopez?"* → la herramienta devuelve un error → el agente pide aclaración al usuario.

## Persistencia

Con el mismo `thread_id`, el historial se guarda en `checkpoints.sqlite` y se recupera incluso entre ejecuciones del programa.

Prueba entre ejecuciones: en un segundo proceso, con el mismo `thread_id`, la pregunta *"¿Y cuál fue el pedido más barato?"* se respondió sin mencionar al cliente. El agente recordó que era el cliente 102 y llamó directamente a `buscar_pedidos(102)`.
