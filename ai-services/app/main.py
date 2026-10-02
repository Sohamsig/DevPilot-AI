from fastapi import FastAPI, HTTPException
from langchain_core.messages import HumanMessage

from app.agent.graph import agent_graph
from app.schemas import AgentRequest, AgentResponse


app = FastAPI(
    title="DevPilot AI Service",
    version="0.6.1",
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "devpilot-ai",
        "version": "0.6.1",
    }


@app.post(
    "/v1/agent/runs",
    response_model=AgentResponse,
)
def run_agent(request: AgentRequest):
    try:
        if request.workspace_path:
            message = (
                f"Workspace path: "
                f"{request.workspace_path}\n\n"
                f"User task: {request.message}"
            )
        else:
            message = request.message

        result = agent_graph.invoke(
            {
                "messages": [
                    HumanMessage(
                        content=message
                    )
                ]
            }
        )

        final_message = result["messages"][-1]

        return AgentResponse(
            answer=final_message.content
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )

