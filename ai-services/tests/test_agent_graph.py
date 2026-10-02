from langchain_core.messages import HumanMessage

from app.agent.graph import agent_graph


def invoke_agent(prompt: str):
    return agent_graph.invoke(
        {
            "messages": [
                HumanMessage(content=prompt)
            ]
        }
    )


def test_agent_lists_files():
    result = invoke_agent(
        "List the files in this repository"
    )

    messages = result["messages"]

    # The agent should make a tool call.
    assert any(
        getattr(message, "tool_calls", None)
        for message in messages
    )

    # The tool should actually execute.
    assert any(
        message.__class__.__name__ == "ToolMessage"
        for message in messages
    )

    # The agent should produce a final answer.
    final_message = messages[-1]

    assert final_message.content
    assert "README.md" in final_message.content


def test_agent_searches_repository():
    result = invoke_agent(
        "Find where MongoDB is configured in this repository"
    )

    messages = result["messages"]

    # A repository tool should have executed.
    assert any(
        message.__class__.__name__ == "ToolMessage"
        for message in messages
    )

    final_message = messages[-1]

    assert final_message.content
    assert "Mongo" in final_message.content


def test_agent_reads_requested_file():
    result = invoke_agent(
        "Read backend/internal/config/config.go"
    )

    messages = result["messages"]

    assert any(
        message.__class__.__name__ == "ToolMessage"
        for message in messages
    )

    final_message = messages[-1]

    assert final_message.content
    assert "MongoURI" in final_message.content


def test_agent_handles_missing_file():
    result = invoke_agent(
        "Read backend/does-not-exist.go"
    )

    final_message = result["messages"][-1]

    assert final_message.content

    response = final_message.content.lower()

    assert (
        "not found" in response
        or "does-not-exist.go" in response
    )