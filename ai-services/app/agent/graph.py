import json
import uuid

from langchain_core.messages import AIMessage
from langchain_ollama import ChatOllama
from langgraph.graph import START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from app.agent.prompts import SYSTEM_PROMPT
from app.agent.state import AgentState
from app.tools.repository import (
    list_files,
    read_file,
    search_code,
)


tools = [
    list_files,
    read_file,
    search_code,
]


llm = ChatOllama(
    model="qwen2.5-coder:7b",
    temperature=0,
)


llm_with_tools = llm.bind_tools(tools)


TOOL_MAP = {
    "list_files": list_files,
    "read_file": read_file,
    "search_code": search_code,
}


def normalize_tool_call(response: AIMessage) -> AIMessage:
    """
    Normalize Qwen's JSON-in-content tool calls into
    LangChain's standard AIMessage.tool_calls format.
    """

    # If the provider already gave us proper tool calls,
    # do nothing.
    if response.tool_calls:
        return response

    content = response.content

    if not isinstance(content, str):
        return response

    content = content.strip()

    if not content.startswith("{"):
        return response

    try:
        payload = json.loads(content)
    except json.JSONDecodeError:
        return response

    if not isinstance(payload, dict):
        return response

    tool_name = payload.get("name")
    arguments = payload.get("arguments", {})

    if tool_name not in TOOL_MAP:
        return response

    if not isinstance(arguments, dict):
        return response

    return AIMessage(
        content="",
        tool_calls=[
            {
                "name": tool_name,
                "args": arguments,
                "id": f"call_{uuid.uuid4().hex}",
                "type": "tool_call",
            }
        ],
    )


def agent_node(state: AgentState):
    response = llm_with_tools.invoke(
        [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            *state["messages"],
        ]
    )

    response = normalize_tool_call(response)

    return {
        "messages": [response],
    }


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node(
        "agent",
        agent_node,
    )

    graph.add_node(
        "tools",
        ToolNode(tools),
    )

    graph.add_edge(
        START,
        "agent",
    )

    graph.add_conditional_edges(
        "agent",
        tools_condition,
    )

    graph.add_edge(
        "tools",
        "agent",
    )

    return graph.compile()


agent_graph = build_graph()