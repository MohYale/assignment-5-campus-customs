"""Campus Customs API for the later dashboard.

Run from backend/:  uvicorn main:app --reload --port 8000
Open API docs:      http://127.0.0.1:8000/docs

Agents still only prepare a payment. POST /api/approve is the human step
that changes the checking balance in data/campus_customs_new.db.
"""

from __future__ import annotations

import json
import shutil
import sqlite3
from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from team import AUDIT_PATH, run_team

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DB_PATH = ROOT / "data" / "campus_customs_new.db"
ORIGINAL_DB = ROOT / "data" / "campus_customs.db"

app = FastAPI(title="Campus Customs", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ApproveBody(BaseModel):
    kind: Literal["invoice_payment", "rent_payment", "purchase_order"]
    ref_id: int = 0
    sku: str = ""
    size: str = ""
    qty: int = 0
    approved_by: str = Field(default="owner", max_length=80)


def _read() -> sqlite3.Connection:
    if not DB_PATH.is_file():
        raise HTTPException(status_code=500, detail=f"Database not found: {DB_PATH.name}")
    uri = DB_PATH.resolve().as_posix()
    conn = sqlite3.connect(f"file:{uri}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _write() -> sqlite3.Connection:
    if not DB_PATH.is_file():
        raise HTTPException(status_code=500, detail=f"Database not found: {DB_PATH.name}")
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def _money(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _ticket_row(row: sqlite3.Row) -> dict[str, Any]:
    status = str(row["status"] or "")
    open_ticket = status.strip().lower() == "open"
    qty = row["qty"]
    on_hand = row["on_hand"]
    shortfall = None
    if qty is not None and row["sku"]:
        held = int(on_hand) if on_hand is not None else 0
        shortfall = max(int(qty) - held, 0)
    return {
        "id": row["id"],
        "type": row["type"],
        "requester": row["requester"],
        "subject": row["subject"],
        "sku": row["sku"],
        "size": row["size"],
        "qty": qty,
        "item_name": row["item_name"],
        "unit_cost": _money(row["unit_cost"]),
        "invoice_id": row["invoice_id"],
        "invoice_amount": _money(row["invoice_amount"]),
        "lease_id": row["lease_id"],
        "monthly_rent": _money(row["monthly_rent"]),
        "space_name": row["space_name"],
        "on_hand": on_hand,
        "shortfall": shortfall,
        "status": status,
        "open": open_ticket,
        "resolved": not open_ticket,
    }


@app.get("/api/tickets")
def list_tickets() -> dict[str, Any]:
    """The three shop tickets, each marked open or resolved."""
    with _read() as conn:
        rows = conn.execute(
            """
            SELECT t.id, t.type, t.requester, t.subject, t.sku, t.size, t.qty,
                   t.status, t.invoice_id, t.lease_id, i.qty AS on_hand,
                   i.name AS item_name, p.unit_cost, inv.amount AS invoice_amount,
                   l.monthly_rent, l.space_name
            FROM tickets AS t
            LEFT JOIN inventory AS i ON i.sku = t.sku AND i.size = t.size
            LEFT JOIN pricing AS p ON p.sku = t.sku
            LEFT JOIN invoices AS inv ON inv.id = t.invoice_id
            LEFT JOIN leases AS l ON l.id = t.lease_id
            ORDER BY t.id
            """
        ).fetchall()
    tickets = [_ticket_row(row) for row in rows]
    return {"tickets": tickets, "count": len(tickets)}


@app.post("/api/tickets/{ticket_id}/run")
def run_ticket(ticket_id: int) -> dict[str, Any]:
    """Run the agent team on one ticket. The team appends to the audit trail."""
    with _read() as conn:
        found = conn.execute("SELECT id FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if found is None:
        raise HTTPException(status_code=404, detail=f"No ticket {ticket_id}.")
    result = run_team(ticket_id)
    failed = result.get("steps") == 0 or str(result.get("summary") or "").startswith(
        "boss stopped with an error"
    )
    if not failed:
        with _write() as conn:
            conn.execute(
                "UPDATE tickets SET status = 'resolved' WHERE id = ?",
                (ticket_id,),
            )
            conn.commit()
        result["status"] = "resolved"
        result["resolved"] = True
    return result


@app.get("/api/events")
def recent_events(limit: int = Query(default=30, ge=1, le=200)) -> dict[str, Any]:
    """What each recent agent step said, and which tools it used."""
    if not AUDIT_PATH.is_file() or AUDIT_PATH.stat().st_size == 0:
        return {"events": [], "count": 0}
    try:
        loaded = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail="audit_trail.json could not be read.") from exc
    rows = loaded if isinstance(loaded, list) else [loaded]
    events = []
    for row in rows[-limit:]:
        if not isinstance(row, dict):
            continue
        calls = row.get("tool_calls") or []
        tools = []
        for call in calls:
            if isinstance(call, dict) and call.get("tool"):
                tools.append(call["tool"])
        thoughts = []
        for thought in (row.get("thoughts") or [])[:3]:
            text = " ".join(str(thought).split())
            if text:
                thoughts.append(text[:500])
        events.append(
            {
                "time": row.get("time"),
                "run_id": row.get("run_id"),
                "ticket_id": row.get("ticket_id"),
                "step": row.get("step"),
                "agent": row.get("agent"),
                "caller": row.get("caller"),
                "said": row.get("reply") or "",
                "thoughts": thoughts,
                "tools": tools,
                "final_call": row.get("final_call"),
                "needs_human_approval": bool(row.get("needs_human_approval")),
                "approval_kind": row.get("approval_kind") or "none",
            }
        )
    return {"events": events, "count": len(events)}


@app.post("/api/approve")
def approve_payment(body: ApproveBody) -> dict[str, Any]:
    """Post a prepared payment or purchase. This is the step that changes cash."""
    approved_by = body.approved_by.strip() or "owner"
    with _write() as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            amount, ref_id, detail = _price_the_approval(conn, body)
            cash = conn.execute(
                "SELECT name, balance FROM cash_accounts WHERE name = 'checking'"
            ).fetchone()
            if cash is None:
                raise HTTPException(status_code=500, detail="No checking account.")
            balance = float(cash["balance"])
            if amount > balance:
                raise HTTPException(
                    status_code=400,
                    detail=f"Checking has ${balance:.2f}, which is short of ${amount:.2f}.",
                )
            if body.kind in {"invoice_payment", "rent_payment"}:
                already = conn.execute(
                    "SELECT id FROM payments WHERE kind = ? AND ref_id = ?",
                    (body.kind, ref_id),
                ).fetchone()
                if already is not None:
                    raise HTTPException(
                        status_code=409,
                        detail=f"A {body.kind} for ref {ref_id} is already posted.",
                    )
            desk = conn.execute("SELECT date_today FROM desk").fetchone()
            paid_at = desk["date_today"] if desk else ""
            conn.execute(
                """
                INSERT INTO payments (kind, ref_id, amount, account, paid_at, approved_by)
                VALUES (?, ?, ?, 'checking', ?, ?)
                """,
                (body.kind, ref_id, amount, paid_at, approved_by),
            )
            new_balance = round(balance - amount, 2)
            conn.execute(
                "UPDATE cash_accounts SET balance = ? WHERE name = 'checking'",
                (new_balance,),
            )
            if body.kind == "invoice_payment":
                conn.execute("UPDATE invoices SET status = 'paid' WHERE id = ?", (ref_id,))
            conn.commit()
        except HTTPException:
            conn.rollback()
            raise
        except Exception:
            conn.rollback()
            raise
    return {
        "approved": True,
        "kind": body.kind,
        "ref_id": ref_id,
        "amount": amount,
        "account": "checking",
        "balance": new_balance,
        "approved_by": approved_by,
        "detail": detail,
        "money_moved": True,
    }


def _price_the_approval(conn: sqlite3.Connection, body: ApproveBody) -> tuple[float, int, str]:
    if body.kind == "invoice_payment":
        row = conn.execute("SELECT * FROM invoices WHERE id = ?", (body.ref_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail=f"No invoice {body.ref_id}.")
        if str(row["status"]).lower() != "open":
            raise HTTPException(status_code=409, detail=f"Invoice {body.ref_id} is already {row['status']}.")
        amount = round(float(row["amount"]), 2)
        return amount, int(row["id"]), str(row["description"] or "")
    if body.kind == "rent_payment":
        row = conn.execute("SELECT * FROM leases WHERE id = ?", (body.ref_id,)).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail=f"No lease {body.ref_id}.")
        amount = round(float(row["monthly_rent"]), 2)
        return amount, int(row["id"]), f"{row['space_name']} rent"
    if not body.sku or not body.size or body.qty <= 0:
        raise HTTPException(status_code=400, detail="A purchase order needs sku, size, and a qty above zero.")
    price = conn.execute("SELECT unit_cost FROM pricing WHERE sku = ?", (body.sku,)).fetchone()
    if price is None:
        raise HTTPException(status_code=404, detail=f"No pricing row for {body.sku}.")
    stock = conn.execute(
        "SELECT name FROM inventory WHERE sku = ? AND size = ?",
        (body.sku, body.size),
    ).fetchone()
    amount = round(float(price["unit_cost"]) * body.qty, 2)
    name = stock["name"] if stock else body.sku
    return amount, 0, f"{body.qty} × {name} ({body.sku}) size {body.size}"


@app.get("/api/cash")
def checking_balance() -> dict[str, Any]:
    """The current checking balance."""
    with _read() as conn:
        row = conn.execute(
            "SELECT name, balance, date FROM cash_accounts WHERE name = 'checking'"
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=500, detail="No checking account.")
    return {"name": row["name"], "balance": float(row["balance"]), "date": row["date"]}


@app.post("/api/reset")
def reset_database() -> dict[str, Any]:
    """Copy the original shop database back over the working file."""
    if not ORIGINAL_DB.is_file():
        raise HTTPException(status_code=500, detail="Original database data/campus_customs.db is missing.")
    shutil.copyfile(ORIGINAL_DB, DB_PATH)
    cash = checking_balance()
    return {
        "reset": True,
        "database": "data/campus_customs_new.db",
        "restored_from": "data/campus_customs.db",
        "checking_balance": cash["balance"],
    }
