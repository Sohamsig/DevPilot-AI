from langchain_core.messages import AIMessage, ToolMessage
from langchain_ollama import ChatOllama
from langgraph.graph import START, END, StateGraph
from langgraph.prebuilt import ToolNode

from app.agent.prompts import SYSTEM_PROMPT
from app.config import settings
from app.agent.state import AgentState
from app.repository.context import build_repository_context

from app.tools.repository import (
    list_files,
    list_top_level_folders,
    read_file,
    search_code,
)
from app.agent.tool_normalization import normalize_tool_call

from app.tools.code_changes import (
    preview_file_change,
    propose_file_change,
)


llm = ChatOllama(
    model="qwen2.5-coder:7b",
    temperature=0,
)

tools = [
    list_files,
    list_top_level_folders,
    read_file,
    search_code,
    preview_file_change,
    propose_file_change,
]

llm_with_tools = llm.bind_tools(tools)


def format_repository_context(context) -> str:
    if context is None:
        return ""

    lines = [
        "Repository Context",
        "",
        f"Root: {context.root}",
        f"Files: {context.file_count}",
        f"Directories: {context.directory_count}",
        f"Truncated: {context.truncated}",
        "",
        "Languages:",
    ]

    if context.languages:
        lines.extend(
            f"- {language}"
            for language in context.languages
        )
    else:
        lines.append("- None detected")

    lines.append("")
    lines.append("Repository structure:")

    if context.directories:
        lines.extend(
            f"- {directory}/"
            for directory in context.directories
        )

    if context.files:
        lines.extend(
            f"- {file_path}"
            for file_path in context.files
        )

    return "\n".join(lines)


def format_tool_result(tool_message: ToolMessage) -> str:
    content = tool_message.content

    if isinstance(content, str):
        return content

    return str(content)


def agent_node(state: AgentState):
    messages = state["messages"]

    # Route explicit top-level-folder requests to the dedicated tool.
    last_user_message = next(
        (
            message
            for message in reversed(messages)
            if getattr(message, "type", None) == "human"
        ),
        None,
    )
    request_text = (
        str(last_user_message.content).lower()
        if last_user_message is not None
        else ""
    )

    asks_for_top_level = (
        ("top-level" in request_text or "top level" in request_text)
        and "folder" in request_text
    )

    if (
        asks_for_top_level
        and messages
        and getattr(messages[-1], "type", None) == "human"
    ):
        workspace_path = (
            state.get("workspace_path")
            or settings.workspace_root
        )
        return {
            "messages": [
                AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "list_top_level_folders",
                            "args": {
                                "workspace_path": str(workspace_path),
                            },
                            "id": "list-top-level-folders",
                            "type": "tool_call",
                        }
                    ],
                )
            ]
        }

    # Route explicit code-search requests directly to search_code.
    if messages and getattr(messages[-1], "type", None) == "human":
        import re

        search_text = str(messages[-1].content).strip()

        search_request = re.match(
            r"""^\s*
                (?:(?:please|can you)\s+)?
                (?:search|find|look\s+for|look\s+up)
                \s+(?:the\s+)?
                (?:code|repository|repo|files?)
                \s+(?:for|containing|with)\s+
                (.+?)
                \s*$""",
            search_text,
            flags=re.IGNORECASE | re.VERBOSE,
        )

        if search_request:
            query = search_request.group(1).strip()
            query = query.removeprefix("the exact string ").strip()

            for marker in (". Report", ". Show", ". Tell", ". Explain"):
                if marker.lower() in query.lower():
                    query = query[:query.lower().index(marker.lower())].strip()
                    break

            if len(query) >= 2 and query[0] == query[-1]:
                if query[0] in ("'", '"', "`"):
                    query = query[1:-1].strip()

            if query:
                workspace_path = (
                    state.get("workspace_path")
                    or settings.workspace_root
                )

                return {
                    "messages": [
                        AIMessage(
                            content="",
                            tool_calls=[
                                {
                                    "name": "search_code",
                                    "args": {
                                        "query": query,
                                        "workspace_path": str(workspace_path),
                                    },
                                    "id": "search-requested-code",
                                    "type": "tool_call",
                                }
                            ],
                        )
                    ]
                }

    # Route explicit file-read requests directly to read_file.
    if messages and getattr(messages[-1], "type", None) == "human":
        import re

        request_text = str(messages[-1].content).strip()

        read_request = re.match(
            r"""^\s*(?:please\s+)?read\s+
                (?:the\s+file\s+)?
                [`'"]?([^\s`'"]+\.[A-Za-z0-9_+-]+)
                [`'"]?
                (?:\s+.*)?$""",
            request_text,
            flags=re.IGNORECASE | re.VERBOSE,
        )

        if read_request:
            requested_path = read_request.group(1).strip()
            workspace_path = (
                state.get("workspace_path")
                or settings.workspace_root
            )

            return {
                "messages": [
                    AIMessage(
                        content="",
                        tool_calls=[
                            {
                                "name": "read_file",
                                "args": {
                                    "file_path": requested_path,
                                    "workspace_path": str(workspace_path),
                                },
                                "id": "read-requested-file",
                                "type": "tool_call",
                            }
                        ],
                    )
                ]
            }

    # Preserve explicit missing-file errors from repository tools.
    if messages and isinstance(messages[-1], ToolMessage):
        tool_result = format_tool_result(messages[-1])

        if tool_result.lstrip().lower().startswith("file not found:"):
            return {
                "messages": [
                    AIMessage(content=tool_result)
                ]
            }

    workspace_path = (
        state.get("workspace_path")
        or settings.workspace_root
    )

    repository_context = format_repository_context(
        state.get("repository_context")
    )

    system_content = SYSTEM_PROMPT

    if repository_context:
        system_content = (
            f"{SYSTEM_PROMPT}\n\n"
            f"{repository_context}"
        )

    response = llm_with_tools.invoke(
        [
            {
                "role": "system",
                "content": system_content,
            },
            *messages,
        ]
    )

    response = normalize_tool_call(
        response,
        workspace_path=workspace_path,
    )

    return {
        "messages": [response],
    }


def repository_context_node(state: AgentState):
    workspace_path = (
        state.get("workspace_path")
        or settings.workspace_root
    )

    context = build_repository_context(
        workspace_path
    )

    return {
        "repository_context": context,
    }


def route_after_agent(state: AgentState):
    """Route to tools only when the latest AI message has a valid tool call."""
    messages = state["messages"]

    if not messages:
        return END

    last_message = messages[-1]

    if isinstance(last_message, AIMessage):
        tool_calls = getattr(last_message, "tool_calls", None) or []
        if any(call.get("name") in {
            "list_files",
            "list_top_level_folders",
            "read_file",
            "search_code",
            "preview_file_change",
            "propose_file_change",
        } for call in tool_calls):
            return "tools"

    return END


def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node(
        "repository_context",
        repository_context_node,
    )

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
        "repository_context",
    )

    graph.add_edge(
        "repository_context",
        "agent",
    )

    graph.add_conditional_edges(
        "agent",
        route_after_agent,
        {
            "tools": "tools",
            END: END,
        },
    )

    graph.add_edge(
        "tools",
        "agent",
    )

    return graph.compile()


agent_graph = build_graph()
