from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    message: str = Field(min_length=1)
    workspace_path: str | None = None


class AgentResponse(BaseModel):
    answer: str