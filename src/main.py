import asyncio
import json
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from graph import build_graph

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
TRACE_PATH = ROOT / "traces" / "ejemplo_traza.json"
DB_PATH = ROOT / "checkpoints.sqlite"
RECURSION_LIMIT = 10

def texto(msg: BaseMessage) -> str:
    c = msg.content
    if isinstance(c, str):
        return c
    return "".join(b.get("text", "") if isinstance(b, dict) else str(b) for b in c)


def serializar(msg: BaseMessage) -> dict[str, Any]:
    return {
        "tipo": msg.type,
        "contenido": texto(msg),
        "tool_calls": getattr(msg, "tool_calls", None) or None,
        "tool_name": getattr(msg, "name", None),
    }


async def preguntar(graph: Any, pregunta: str, thread_id: str) -> list[dict[str, Any]]:
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": RECURSION_LIMIT}
    previos = len((await graph.aget_state(config)).values.get("messages", []))
    result = await graph.ainvoke({"messages": [("user", pregunta)]}, config)
    nuevos = result["messages"][previos:]  # solo lo de este turno
    for m in nuevos:
        print(f"[{m.type}] {texto(m)} {getattr(m, 'tool_calls', '') or ''}")
    return [serializar(m) for m in nuevos]


async def main() -> None:
    thread_id = "sesion-demo-1"
    preguntas = [
        "¿Cuántos pedidos tuvo Juan Perez y cuál fue el total?",  # 2 tool calls
        "¿Y el último?",                                          # memoria
        "¿Y los pedidos de Pedro Lopez?",                         # error -> aclaración
    ]
    traza: list[dict[str, Any]] = []
    TRACE_PATH.parent.mkdir(exist_ok=True)
    async with AsyncSqliteSaver.from_conn_string(str(DB_PATH)) as saver:
        graph = build_graph(saver)
        for p in preguntas:
            print(f"\n=== Usuario: {p}")
            traza.append({"usuario": p, "pasos": await preguntar(graph, p, thread_id)})

    TRACE_PATH.write_text(json.dumps(traza, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nTraza guardada en {TRACE_PATH}")


if __name__ == "__main__":
    asyncio.run(main())