import os

from langchain_core.messages import BaseMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from tools import TOOLS

SYSTEM_PROMPT = (
    "Sos un asistente de consultas de pedidos. Usá las herramientas para obtener "
    "datos reales, nunca inventes. Si una herramienta devuelve un error, intentá "
    "otra vez con otros parámetros o pedile una aclaración al usuario."
)


def build_graph(checkpointer: BaseCheckpointSaver) -> CompiledStateGraph:
    llm = ChatGoogleGenerativeAI(
        model=os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite"),
        temperature=0,
        timeout=120,
        max_retries=2,
    ).bind_tools(TOOLS)

    async def call_model(state: MessagesState) -> dict[str, list[BaseMessage]]:
        response = await llm.ainvoke([SystemMessage(SYSTEM_PROMPT), *state["messages"]])
        return {"messages": [response]}

    builder = StateGraph(MessagesState)  # MessagesState ya usa el reducer add_messages
    builder.add_node("agent", call_model)
    builder.add_node("tools", ToolNode(TOOLS))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition)  # -> "tools" o END
    builder.add_edge("tools", "agent")  # el ciclo ReAct
    return builder.compile(checkpointer=checkpointer)