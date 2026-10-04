from pathlib import Path

from app.agent.graph import agent_graph
from langchain_core.messages import HumanMessage

workspace = str(Path(__file__).resolve().parents[1])

print("WORKSPACE =", workspace)
print("EXISTS =", Path(workspace).exists())
print("README =", Path(workspace, "README.md").exists())
print(
    "CONFIG =",
    Path(workspace, "backend", "internal", "config", "config.go").exists()
)

result = agent_graph.invoke(
    {
        "messages": [
            HumanMessage(
                content="Read backend/internal/config/config.go"
            )
        ],
        "workspace_path": workspace,
    }
)

print()
print("MESSAGES")
print("=" * 80)

for i, message in enumerate(result["messages"]):
    print()
    print("MESSAGE", i)
    print("TYPE:", type(message).__name__)
    print("CONTENT:", repr(message.content))
    print("TOOL CALLS:", getattr(message, "tool_calls", None))
