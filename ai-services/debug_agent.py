from app.agent.graph import agent_graph
from langchain_core.messages import HumanMessage

queries = [
    "List the files in this repository",
    "Find where MongoDB is configured in this repository",
    "Read backend/internal/config/config.go",
]

for query in queries:
    print()
    print("=" * 100)
    print("QUERY:", query)
    print("=" * 100)

    result = agent_graph.invoke(
        {
            "messages": [
                HumanMessage(content=query)
            ],
            "workspace_path": r"C:\Users\soham\Devpilot-ai",
        }
    )

    for i, message in enumerate(result["messages"]):
        print()
        print("-" * 80)
        print("MESSAGE:", i)
        print("TYPE:", type(message).__name__)
        print("CONTENT:", repr(message.content))
        print("TOOL CALLS:", getattr(message, "tool_calls", None))
        print("TOOL CALL ID:", getattr(message, "tool_call_id", None))
        print("NAME:", getattr(message, "name", None))
