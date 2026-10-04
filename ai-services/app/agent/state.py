from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from app.repository.context import RepositoryContext


class AgentState(TypedDict):
    workspace_path: str | None
    repository_context: RepositoryContext | None
    messages: Annotated[
        list[BaseMessage],
        add_messages,
    ]
