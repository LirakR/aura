"""Pydantic models for agent configuration and approval flow."""

from __future__ import annotations

from pydantic import BaseModel


class AgentConfig(BaseModel):
    provider: str = "codex"
    model: str = "gpt-4.1"
    binary: str = "codex"


class ApprovalRequest(BaseModel):
    request_id: str
    thread_id: str
    tool_name: str
    tool_args: dict
    description: str


class ApprovalDecision(BaseModel):
    request_id: str
    decision: str  # "approve" | "deny"
