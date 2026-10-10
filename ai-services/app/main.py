from fastapi import FastAPI, HTTPException
from langchain_core.messages import HumanMessage

from app.agent.graph import agent_graph
from app.schemas import (
    AgentRequest,
    AgentResponse,
    ChangeProposalRequest,
    ChangeProposalResponse,
    ChangeDecisionResponse,
)
from app.tools.change_approval import (
    create_proposal,
    approve_proposal,
    reject_proposal,
)


app = FastAPI(
    title="DevPilot AI Service",
    version="0.7.0",
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "devpilot-ai",
        "version": "0.7.0",
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
                    HumanMessage(content=request.message)
                ],
            }
        )

        final_message = result["messages"][-1]

        return AgentResponse(answer=final_message.content)

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )


@app.post(
    "/v1/changes/proposals",
    response_model=ChangeProposalResponse,
)
def propose_change(request: ChangeProposalRequest):
    try:
        return create_proposal(
            file_path=request.file_path,
            proposed_content=request.proposed_content,
            workspace_path=request.workspace_path,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post(
    "/v1/changes/{proposal_id}/approve",
    response_model=ChangeDecisionResponse,
)
def approve_change(proposal_id: str):
    try:
        return approve_proposal(proposal_id)
    except ValueError as exc:
        status_code = (
            404 if str(exc) == "Proposal not found." else 409
        )
        raise HTTPException(
            status_code=status_code,
            detail=str(exc),
        )


@app.post(
    "/v1/changes/{proposal_id}/reject",
    response_model=ChangeDecisionResponse,
)
def reject_change(proposal_id: str):
    try:
        return reject_proposal(proposal_id)
    except ValueError as exc:
        status_code = (
            404 if str(exc) == "Proposal not found." else 409
        )
        raise HTTPException(
            status_code=status_code,
            detail=str(exc),
        )
