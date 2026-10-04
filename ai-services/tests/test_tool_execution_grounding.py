from langchain_core.messages import HumanMessage, ToolMessage

from app.agent.graph import agent_graph


def test_agent_executes_repository_tool_and_returns_grounded_answer(tmp_path):
    (tmp_path / "app.py").write_text(
        "ROUTE = '/v1/agent/runs'\n",
        encoding="utf-8",
    )

    result = agent_graph.invoke(
        {
            "workspace_path": str(tmp_path),
            "repository_context": None,
            "messages": [
                HumanMessage(
                    content=(
                        "Find where /v1/agent/runs appears. "
                        "Use repository tools. "
                        "Do not guess."
                    )
                )
            ],
        }
    )

    messages = result["messages"]

    assert len(messages) >= 4

    tool_messages = [
        message
        for message in messages
        if isinstance(message, ToolMessage)
    ]

    assert tool_messages

    tool_result = tool_messages[-1].content

    assert "app.py" in tool_result
    assert "v1/agent/runs" in tool_result

    final_message = messages[-1]

    assert final_message.content
    assert "v1/agent/runs" in final_message.content
