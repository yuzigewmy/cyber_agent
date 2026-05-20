from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class AgentMode(str, Enum):
    defense = "defense"
    redteam = "redteam"
    threat_intel = "threat_intel"


class ScopeApproval(BaseModel):
    approved: bool = False
    approver: str | None = None
    ticket_id: str | None = None
    time_window: str | None = None
    rules_of_engagement: str | None = None


class AgentRequest(BaseModel):
    mode: AgentMode = AgentMode.defense
    question: str = Field(min_length=1, max_length=12000)
    assets: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    tenant_id: str = "default"
    user_id: str = "anonymous"
    session_id: str | None = None
    scope: ScopeApproval = Field(default_factory=ScopeApproval)
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievedContext(BaseModel):
    source: str
    collection: str
    score: float
    text: str
    sensitivity: str = "internal"


class Finding(BaseModel):
    title: str
    severity: Literal["info", "low", "medium", "high", "critical"] = "info"
    evidence: list[str] = Field(default_factory=list)
    mapping: list[str] = Field(default_factory=list)
    recommendation: str | None = None


class AgentResponse(BaseModel):
    session_id: str | None = None
    mode: AgentMode
    blocked: bool = False
    severity: Literal["info", "low", "medium", "high", "critical"] = "info"
    answer: str
    findings: list[Finding] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    retrieved_contexts: list[RetrievedContext] = Field(default_factory=list)
    policy_reasons: list[str] = Field(default_factory=list)
    requires_human_approval: bool = False
    trace: dict[str, Any] = Field(default_factory=dict)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=1, max_length=256)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    username: str
    roles: list[str] = Field(default_factory=list)


class UserProfile(BaseModel):
    username: str
    roles: list[str] = Field(default_factory=list)



class ChatSessionCreate(BaseModel):
    title: str | None = Field(default=None, max_length=200)
    mode: AgentMode = AgentMode.defense
    tenant_id: str = "default"


class ChatSessionSummary(BaseModel):
    id: str
    title: str
    mode: str
    tenant_id: str
    created_at: str
    updated_at: str


class ChatMessageRecord(BaseModel):
    id: str
    session_id: str
    role: Literal["user", "assistant", "system"] | str
    mode: str
    content: str
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: str
