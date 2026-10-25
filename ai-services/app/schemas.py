from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    message: str = Field(min_length=1)
    workspace_path: str | None = None


class ChangeProposalRequest(BaseModel):
    file_path: str = Field(min_length=1)
    proposed_content: str
    workspace_path: str | None = None


class ChangeProposalResponse(BaseModel):
    proposal_id: str
    file_path: str
    diff: str
    status: str


class AgentResponse(BaseModel):
    answer: str
    proposal: ChangeProposalResponse | None = None


class ChangeDecisionResponse(BaseModel):
    proposal_id: str
    status: str