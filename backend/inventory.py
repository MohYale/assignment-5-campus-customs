"""Inventory agent. Stock by SKU and size, shortages, and the restock vendor."""

from __future__ import annotations

from pathlib import Path

from pydantic_ai import Agent

from models import AgentReport

NAME = "inventory"
PROMPT_PATH = Path(__file__).resolve().parent / "prompts" / "inventory.md"
TOOLS = frozenset(
    {
        "check_stock",
        "list_shortages",
        "recommend_vendor",
        "check_inventory_for_ticket",
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
