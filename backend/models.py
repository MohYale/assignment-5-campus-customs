"""Shared types for the Campus Customs agent team."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

AgentName = Literal["boss", "inventory", "accounting", "facilities", "customer_service"]
ApprovalKind = Literal["none", "payment", "purchase_order", "customer_message"]


class Handoff(BaseModel):
    """One task passed from one agent to another."""

    agent: AgentName
    task: str


class AgentReport(BaseModel):
    """What one agent-loop step returns after it has used the MCP tools."""

    agent: AgentName
    summary: str
    ticket_ids: list[int] = Field(default_factory=list)
    findings: list[str] = Field(default_factory=list)
    handoffs: list[Handoff] = Field(default_factory=list)
    final_call: str | None = None
    needs_human_approval: bool = False
    approval_kind: ApprovalKind = "none"
