"""Facilities agent. The lease, the rent, and the shop date."""

from __future__ import annotations

from pathlib import Path

from pydantic_ai import Agent

from models import AgentReport

NAME = "facilities"
PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "facilities.md"
TOOLS = frozenset({"read_shop_space", "assess_ticket_request"})


def build(model, toolset) -> Agent[None, AgentReport]:
    allowed = toolset.filtered(lambda _ctx, tool: tool.name in TOOLS)
    return Agent(
        model,
        name=NAME,
        instructions=PROMPT_PATH.read_text(encoding="utf-8"),
        toolsets=[allowed],
        output_type=AgentReport,
        retries=2,
    )
