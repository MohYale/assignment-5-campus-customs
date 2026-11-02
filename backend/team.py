"""Agent loop for the Campus Customs team.

The boss and the four specialists delegate through handoffs. Each step is one
agent run. Shop facts come from the Campus Customs MCP server, which reads
data/campus_customs_new.db. This loop does not query that database itself.

Each step is appended to output/audit_trail.json. A later run adds rows.
It does not replace the file.

The model is gpt-6-luna through the course Portkey gateway. Override with
MODEL_NAME. Put PORTKEY_API_KEY in .env or in the course portkey_api_key.env.
"""

from __future__ import annotations

import json
import os
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
MCP_DIR = ROOT / "mcp_server"
if str(MCP_DIR) not in sys.path:
    sys.path.insert(0, str(MCP_DIR))

import accounting  # noqa: E402
import boss  # noqa: E402
import customer_service  # noqa: E402
import facilities  # noqa: E402
import inventory  # noqa: E402
from dotenv import load_dotenv  # noqa: E402
from models import AgentReport  # noqa: E402
from openai import AsyncOpenAI  # noqa: E402
from pydantic_ai import Agent  # noqa: E402
from pydantic_ai.mcp import MCPToolset  # noqa: E402
from pydantic_ai.messages import (  # noqa: E402
    BaseToolCallPart,
    BaseToolReturnPart,
    ModelRequest,
    ModelResponse,
    RetryPromptPart,
    TextPart,
    ThinkingPart,
)
from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings  # noqa: E402
from pydantic_ai.providers.openai import OpenAIProvider  # noqa: E402
from pydantic_ai.usage import UsageLimits  # noqa: E402
from pydantic_core import to_json  # noqa: E402

load_dotenv(ROOT / ".env")
load_dotenv(ROOT.parent / ".env")
load_dotenv(ROOT.parent / "portkey_api_key.env")

MODEL_NAME = os.getenv("MODEL_NAME", "gpt-6-luna").strip() or "gpt-6-luna"
PORTKEY_BASE_URL = os.getenv("PORTKEY_BASE_URL", "https://api.portkey.ai/v1").rstrip("/")
AUDIT_PATH = ROOT / "output" / "audit_trail.json"
MAX_DEPTH = 3
MAX_STEPS = 16
MAX_MODEL_REQUESTS = 12
RESULT_PREVIEW_CHARS = 500

ROLES = {
    boss.NAME: boss,
    inventory.NAME: inventory,
    accounting.NAME: accounting,
    facilities.NAME: facilities,
    customer_service.NAME: customer_service,
}

_audit_lock = threading.Lock()
_toolset: MCPToolset | None = None
_model: OpenAIResponsesModel | None = None


def _mcp_toolset() -> MCPToolset:
    """Attach the Campus Customs FastMCP server in-process."""
    global _toolset
    if _toolset is None:
        from mcp_server import mcp as campus_mcp

        _toolset = MCPToolset(campus_mcp)
    return _toolset


def _model_client() -> OpenAIResponsesModel:
    global _model
    if _model is None:
        api_key = os.getenv("PORTKEY_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError(
                "PORTKEY_API_KEY is not set. Put it in .env or the course portkey_api_key.env."
            )
        client = AsyncOpenAI(
            api_key=api_key,
            base_url=PORTKEY_BASE_URL,
            default_headers={"x-portkey-api-key": api_key},
        )
        _model = OpenAIResponsesModel(MODEL_NAME, provider=OpenAIProvider(openai_client=client))
    return _model


def _redact(text: str) -> str:
    secret = os.getenv("PORTKEY_API_KEY", "").strip()
    if secret:
        text = text.replace(secret, "[redacted]")
    return text


def _preview(value: Any) -> str:
    text = value if isinstance(value, str) else to_json(value).decode("utf-8", "replace")
    text = " ".join(text.split())
    text = _redact(text)
    return text if len(text) <= RESULT_PREVIEW_CHARS else text[: RESULT_PREVIEW_CHARS - 1] + "…"


def _summarize_run(messages: list[Any]) -> tuple[list[str], list[dict[str, Any]], str]:
    thoughts: list[str] = []
    calls: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}
    finish_reason: str | None = None
    last_response = max(
        (i for i, message in enumerate(messages) if isinstance(message, ModelResponse)),
        default=-1,
    )
    for index, message in enumerate(messages):
        if isinstance(message, ModelResponse):
            finish_reason = message.finish_reason
            has_calls = any(isinstance(part, BaseToolCallPart) for part in message.parts)
            for part in message.parts:
                if isinstance(part, ThinkingPart) and part.content:
                    thoughts.append(part.content)
                elif isinstance(part, TextPart) and part.content and has_calls and index != last_response:
                    thoughts.append(part.content)
                elif isinstance(part, BaseToolCallPart):
                    entry = {
                        "tool": part.tool_name,
                        "args": part.args_as_dict(),
                        "result": None,
                    }
                    calls.append(entry)
                    by_id[part.tool_call_id] = entry
                elif isinstance(part, BaseToolReturnPart):
                    found = by_id.get(part.tool_call_id)
                    if found is not None:
                        found["result"] = _preview(part.content)
        elif isinstance(message, ModelRequest):
            for part in message.parts:
                if isinstance(part, (BaseToolReturnPart, RetryPromptPart)):
                    found = by_id.get(part.tool_call_id)
                    if found is not None:
                        found["result"] = _preview(part.content)
    return thoughts, calls, f"final answer (finish_reason={finish_reason or 'stop'})"


def _append_audit(entry: dict[str, Any]) -> None:
    with _audit_lock:
        AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
        rows: list[Any] = []
        if AUDIT_PATH.exists() and AUDIT_PATH.stat().st_size > 0:
            try:
                loaded = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
                rows = loaded if isinstance(loaded, list) else [loaded]
            except json.JSONDecodeError:
                stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                AUDIT_PATH.replace(AUDIT_PATH.with_name(f"audit_trail.corrupt-{stamp}.json"))
        rows.append(entry)
        tmp = AUDIT_PATH.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(AUDIT_PATH)


class _Loop:
    def __init__(self, ticket_id: int | None = None) -> None:
        self.run_id = uuid4().hex[:12]
        self.ticket_id = ticket_id
        self.steps = 0
        self.needs_human_approval = False
        self.approval_kinds: list[str] = []


def _note_approval(loop: _Loop, report: AgentReport) -> None:
    if report.needs_human_approval:
        loop.needs_human_approval = True
        if report.approval_kind != "none" and report.approval_kind not in loop.approval_kinds:
            loop.approval_kinds.append(report.approval_kind)


def _run_once(
    loop: _Loop,
    agent_name: str,
    task: str,
    *,
    depth: int,
    caller: str | None,
) -> AgentReport:
    loop.steps += 1
    step = loop.steps
    role = ROLES[agent_name]
    entry: dict[str, Any] = {
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "run_id": loop.run_id,
        "ticket_id": loop.ticket_id,
        "step": step,
        "agent": agent_name,
        "caller": caller,
        "depth": depth,
        "task": task,
        "model": MODEL_NAME,
        "thoughts": [],
        "tool_calls": [],
        "handoffs": [],
        "needs_human_approval": False,
        "approval_kind": "none",
        "final_call": None,
        "stopped": "",
        "reply": "",
    }
    try:
        if loop.steps > MAX_STEPS:
            raise RuntimeError(f"Stopped: the team reached {MAX_STEPS} steps.")
        agent: Agent[None, AgentReport] = role.build(_model_client(), _mcp_toolset())
        run = agent.run_sync(
            task,
            usage_limits=UsageLimits(request_limit=MAX_MODEL_REQUESTS),
            model_settings=OpenAIResponsesModelSettings(openai_reasoning_summary="auto"),
        )
        report = run.output
        thoughts, calls, stopped = _summarize_run(run.new_messages())
        entry.update(
            thoughts=thoughts,
            tool_calls=calls,
            handoffs=[item.model_dump() for item in report.handoffs],
            needs_human_approval=report.needs_human_approval,
            approval_kind=report.approval_kind,
            final_call=report.final_call,
            stopped=stopped,
            reply=report.summary,
        )
        _note_approval(loop, report)
        return report
    except Exception as exc:
        detail = _redact(f"{type(exc).__name__}: {exc}")[:500]
        report = AgentReport(
            agent=agent_name,  # type: ignore[arg-type]
            summary=f"{agent_name} stopped with an error. ({detail})",
        )
        entry.update(stopped=f"error: {detail}", reply=report.summary)
        return report
    finally:
        _append_audit(entry)


def _follow(agent_name: str, reports: list[AgentReport], *, boss_final: bool) -> str:
    lines = [f"{report.agent}: {report.summary}" for report in reports]
    body = "\n".join(lines)
    if boss_final:
        return (
            "Specialist reports are below. Leave handoffs empty. Write the final call. "
            "Name each ticket, what the team found, and what the owner must check "
            "before any payment or any customer contact.\n\n"
            + body
        )
    return (
        "Reports from the agents you asked are below. Leave handoffs empty unless a "
        "shop fact is still missing. Finish your own summary.\n\n"
        + body
    )


def _walk(
    loop: _Loop,
    agent_name: str,
    task: str,
    *,
    depth: int,
    caller: str | None,
    chain: tuple[str, ...],
) -> AgentReport:
    report = _run_once(loop, agent_name, task, depth=depth, caller=caller)
    if depth >= MAX_DEPTH or not report.handoffs or loop.steps >= MAX_STEPS:
        return report
    children: list[AgentReport] = []
    seen = set(chain)
    for handoff in report.handoffs:
        if handoff.agent in seen or handoff.agent == agent_name:
            continue
        seen.add(handoff.agent)
        children.append(
            _walk(
                loop,
                handoff.agent,
                handoff.task,
                depth=depth + 1,
                caller=agent_name,
                chain=chain + (handoff.agent,),
            )
        )
    if not children or loop.steps >= MAX_STEPS:
        return report
    return _run_once(
        loop,
        agent_name,
        _follow(agent_name, children, boss_final=agent_name == "boss"),
        depth=depth,
        caller=caller,
    )


def run_team(ticket_id: int | None = None) -> dict[str, Any]:
    """Run the boss. Pass a ticket id to work that ticket only."""
    loop = _Loop(ticket_id)
    if ticket_id is None:
        task = (
            "Work every open Campus Customs ticket. Read each ticket, hand it to the "
            "specialist who should lead it, and wait for the follow-up before the final call. "
            "Do not move money. Do not contact a customer."
        )
    else:
        task = (
            f"Work only ticket {ticket_id}. Do not work the other tickets. "
            "Read that ticket, hand it to the specialist who should lead it, "
            "and wait for the follow-up before the final call. "
            "Do not move money. Do not contact a customer."
        )
    final = _walk(
        loop,
        "boss",
        task,
        depth=0,
        caller=None,
        chain=("boss",),
    )
    return {
        "run_id": loop.run_id,
        "ticket_id": ticket_id,
        "model": MODEL_NAME,
        "steps": loop.steps,
        "final_call": final.final_call,
        "summary": final.summary,
        "needs_human_approval": loop.needs_human_approval or final.needs_human_approval,
        "approval_kinds": loop.approval_kinds,
        "audit_trail": str(AUDIT_PATH.relative_to(ROOT)).replace("\\", "/"),
    }


if __name__ == "__main__":
    print(json.dumps(run_team(), indent=2, ensure_ascii=False))
