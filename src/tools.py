from typing import Any

from langchain_core.tools import tool

CLIENTES: dict[str, int] = {"juan perez": 102, "maria gomez": 205}

PEDIDOS: dict[int, list[dict[str, Any]]] = {
    102: [
        {"id": 9001, "fecha": "2026-08-10", "monto": 4500},
        {"id": 9002, "fecha": "2026-09-03", "monto": 5000},
        {"id": 9003, "fecha": "2026-10-21", "monto": 5000},
    ],
    205: [{"id": 9010, "fecha": "2026-10-01", "monto": 8000}],
}


@tool
async def buscar_cliente_id(nombre: str) -> dict[str, Any]:
    """Busca en la base de datos el ID numérico de un cliente a partir de su
    nombre completo (ej: 'Juan Perez'). Usala SIEMPRE que el usuario mencione a
    un cliente por nombre y todavía no tengas su ID. Devuelve {'cliente_id': int}
    o {'error': str} si el cliente no existe; en ese caso podés reintentar con
    otra grafía del nombre o pedirle aclaración al usuario.
    """
    cliente_id = CLIENTES.get(nombre.strip().lower())
    if cliente_id is None:
        return {"error": f"No existe un cliente llamado '{nombre}'."}
    return {"cliente_id": cliente_id}


@tool
async def buscar_pedidos(cliente_id: int) -> dict[str, Any]:
    """Consulta los pedidos de un cliente dado su ID numérico (NO su nombre).
    Devuelve la cantidad de pedidos ('pedidos'), el monto total acumulado
    ('total') y la lista detallada ('detalle') con id, fecha y monto de cada
    pedido, útil para saber cuál fue el último. Si el ID no existe devuelve
    {'error': str}.
    """
    pedidos = PEDIDOS.get(cliente_id)
    if pedidos is None:
        return {"error": f"No hay pedidos para el cliente_id {cliente_id}."}
    return {
        "pedidos": len(pedidos),
        "total": sum(p["monto"] for p in pedidos),
        "detalle": pedidos,
    }

TOOLS = [buscar_cliente_id, buscar_pedidos]