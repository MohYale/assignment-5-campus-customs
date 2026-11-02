"""Accounting agent. Cash, invoices, margins, and drafts that wait for approval."""

from __future__ import annotations

from pathlib import Path

from pydantic_ai import Agent

from models import AgentReport

NAME = "accounting"
PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "accounting.md"
TOOLS = frozenset(
    {
        "read_cash",
        "list_invoices",
        "check_margin",
        "check_paid_in_full",
        "prepare_payment_or_po",
    }
)


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
