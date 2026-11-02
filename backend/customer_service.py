"""Customer-service agent. Drafts messages and does not send them."""

from __future__ import annotations

from pathlib import Path

from pydantic_ai import Agent

from models import AgentReport

NAME = "customer_service"
PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "customer_service.md"
TOOLS = frozenset({"draft_customer_message", "hold_payment_and_request_restock"})


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
