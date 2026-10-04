from langchain_core.messages import HumanMessage

from app.agent.graph import agent_graph


def test_agent_does_not_invent_missing_endpoint(tmp_path):
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
                        "Does POST /v1/payments/quantum-transfer exist "
                        "in this repository? Search first. "
                        "Do not invent an implementation."
                    )
                )
            ],
        }
    )

    final_message = result["messages"][-1]

    assert final_message.content

    answer = final_message.content.lower()

    assert (
        "does not exist" in answer
        or "not found" in answer
        or "no match" in answer
        or "not present" in answer
    )
