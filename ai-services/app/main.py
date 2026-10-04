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
        result = agent_graph.invoke(
            {
                "workspace_path": request.workspace_path,
                "repository_context": None,
                "messages": [
                    HumanMessage(
                        content=request.message
                    )
                ],
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
