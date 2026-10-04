from langchain_core.messages import HumanMessage

from app.agent.graph import agent_graph


def test_agent_can_ground_repository_question(tmp_path):
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
                        "Use repository tools and report the result."
                    )
                )
            ],
        }
    )

    final_message = result["messages"][-1]

    assert final_message.content
    assert "v1/agent/runs" in final_message.content
