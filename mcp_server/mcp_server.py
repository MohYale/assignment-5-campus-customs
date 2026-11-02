"""Campus Customs MCP server.

Every agent in this assignment calls these tools. The tools read
data/campus_customs_new.db and do not write to it. Payment and purchase-order
tools return a draft for the owner to check. Message tools return wording
only. Nothing is paid, emailed, or called.
"""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

from fastmcp import FastMCP

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DB_PATH = ROOT / "data" / "campus_customs_new.db"
DB_FILE = "data/campus_customs_new.db"

mcp = FastMCP("campus-customs")


def _connect() -> sqlite3.Connection:
    if not DB_PATH.is_file():
        raise FileNotFoundError(f"Database not found: {DB_PATH}")
    uri = DB_PATH.resolve().as_posix()
    conn = sqlite3.connect(f"file:{uri}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _missing(ticket_id: int) -> dict:
    return {"error": f"No ticket {ticket_id} in {DB_FILE}."}


def _load_ticket(conn: sqlite3.Connection, ticket_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    return dict(row) if row else None


def _inventory_row(conn: sqlite3.Connection, sku: str, size: str | None) -> dict | None:
    if not sku or not size:
        return None
    row = conn.execute(
        """
        SELECT sku, name, size, qty, location
        FROM inventory
        WHERE sku = ? AND size = ?
        """,
        (sku, size),
    ).fetchone()
    return dict(row) if row else None


def _stock(conn: sqlite3.Connection, ticket: dict) -> dict:
    """What this ticket asks from the shelf, and whether that quantity is there."""
    sku = ticket.get("sku")
    size = ticket.get("size")
    qty_requested = ticket.get("qty")
    if not sku:
        return {
            "asks_for_product": False,
            "have_what_they_asked": False,
            "reason": "This ticket has no sku, so it is not an inventory request.",
        }
    row = _inventory_row(conn, sku, size)
    qty_on_hand = int(row["qty"]) if row else 0
    requested = int(qty_requested) if qty_requested is not None else None
    have = requested is not None and row is not None and qty_on_hand >= requested
    shortfall = None if requested is None else max(requested - qty_on_hand, 0)
    return {
        "asks_for_product": True,
        "sku": sku,
        "name": row["name"] if row else None,
        "size": size,
        "location": row["location"] if row else None,
        "qty_requested": requested,
        "qty_on_hand": qty_on_hand,
        "row_found": row is not None,
        "have_what_they_asked": have,
        "shortfall": shortfall,
    }


def _price(conn: sqlite3.Connection, sku: str) -> dict | None:
    row = conn.execute(
        "SELECT sku, unit_cost, list_price FROM pricing WHERE sku = ?",
        (sku,),
    ).fetchone()
    return dict(row) if row else None


def _payments_for(conn: sqlite3.Connection, ref_id: int) -> list[dict]:
    rows = conn.execute(
        """
        SELECT id, kind, ref_id, amount, account, paid_at, approved_by
        FROM payments
        WHERE ref_id = ?
        ORDER BY id
        """,
        (ref_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def _vendor_covers(specialty: str, sku: str, name: str) -> tuple[bool, str]:
    spec = specialty.lower()
    label = f"{sku} {name}".lower()
    apparel = any(word in label for word in ("hood", "tee", "shirt", "hat", "cap"))
    gift = any(word in label for word in ("mug", "gift"))
    if "apparel" in spec or "reprint" in spec:
        if apparel:
            return True, "Specialty is apparel reprint, which covers this garment."
        return False, "Specialty is apparel reprint, which does not cover this product."
    if "mug" in spec or "gift" in spec or "small good" in spec:
        if gift:
            return True, "Specialty is mugs and small goods, which covers this product."
        return False, "Specialty is mugs and small goods, which does not cover this product."
    if "courier" in spec:
        return False, "Specialty is local delivery, not supplying stock."
    return False, "Specialty on file does not match this product."


def _asking(ticket: dict, stock: dict, lease: dict | None) -> str:
    if ticket["type"] == "rent_notice" and lease:
        return (
            f"The shop rent for {lease['space_name']}: "
            f"${lease['monthly_rent']:.0f} due {lease['next_due']}."
        )
    if not stock["asks_for_product"]:
        return ticket["subject"]
    name = stock["name"] or stock["sku"]
    qty = stock["qty_requested"]
    label = f"{qty} × {name} ({stock['sku']}), size {stock['size']}"
    if ticket["type"] == "price_override":
        return f"A bulk discount on {label}."
    return label + "."


@mcp.tool
def assess_ticket_request(ticket_id: int) -> dict:
    """Assess one ticket before doing anything else.

    Says what the requester is asking the shop to provide, and which tables
    in data/campus_customs_new.db are the place to answer that request.
    """
    with _connect() as conn:
        ticket = _load_ticket(conn, ticket_id)
        if ticket is None:
            return _missing(ticket_id)
        stock = _stock(conn, ticket)
        lease = None
        if ticket.get("lease_id") is not None:
            row = conn.execute("SELECT * FROM leases WHERE id = ?", (ticket["lease_id"],)).fetchone()
            lease = dict(row) if row else None
        invoice = None
        vendor = None
        if ticket.get("invoice_id") is not None:
            row = conn.execute(
                "SELECT * FROM invoices WHERE id = ?",
                (ticket["invoice_id"],),
            ).fetchone()
            invoice = dict(row) if row else None
            if invoice is not None:
                vendor_row = conn.execute(
                    "SELECT * FROM vendors WHERE id = ?",
                    (invoice["vendor_id"],),
                ).fetchone()
                vendor = dict(vendor_row) if vendor_row else None
        price = _price(conn, ticket["sku"]) if ticket.get("sku") else None
        cash = [dict(row) for row in conn.execute("SELECT * FROM cash_accounts")]
        desk = dict(conn.execute("SELECT * FROM desk").fetchone())
        payments = _payments_for(conn, ticket_id)

    helpful: list[dict] = []
    if stock["asks_for_product"]:
        helpful.append(
            {
                "table": "inventory",
                "why": "This is the shelf count for the sku and size on the ticket.",
            }
        )
        helpful.append(
            {
                "table": "pricing",
                "why": "This is the list price and unit cost of that sku.",
            }
        )
    if invoice is not None:
        helpful.append(
            {
                "table": "invoices",
                "why": "The ticket points at a vendor bill that is part of filling the request.",
            }
        )
        helpful.append(
            {
                "table": "vendors",
                "why": "The bill names the provider who would reprint or restock the item.",
            }
        )
    if lease is not None:
        helpful.append(
            {
                "table": "leases",
                "why": "The ticket points at the shop lease, which is the rent being requested.",
            }
        )
        helpful.append(
            {
                "table": "cash_accounts",
                "why": "This is the cash the shop could use for that rent.",
            }
        )
        helpful.append(
            {
                "table": "desk",
                "why": "This is the shop date, so the agent can see how soon the rent is due.",
            }
        )
    helpful.append(
        {
            "table": "payments",
            "why": "This is where a recorded payment for the ticket would show up.",
        }
    )

    return {
        "ticket_id": ticket_id,
        "database_file": DB_FILE,
        "type": ticket["type"],
        "status": ticket["status"],
        "requester": ticket["requester"],
        "subject": ticket["subject"],
        "notes": ticket["notes"],
        "asking_us_to_provide": _asking(ticket, stock, lease),
        "helpful_tables": helpful,
        "inventory": stock if stock["asks_for_product"] else None,
        "pricing": price,
        "invoice": invoice,
        "vendor": vendor,
        "lease": lease,
        "cash_accounts": cash if lease is not None else None,
        "desk": desk if lease is not None else None,
        "payments": payments,
    }


@mcp.tool
def check_inventory_for_ticket(ticket_id: int) -> dict:
    """Check whether inventory can fill what the ticket is asking for.

    Compares the ticket sku, size, and quantity to the inventory row.
    A rent notice has no product, so the shelf cannot answer it.
    """
    with _connect() as conn:
        ticket = _load_ticket(conn, ticket_id)
        if ticket is None:
            return _missing(ticket_id)
        stock = _stock(conn, ticket)
    stock["ticket_id"] = ticket_id
    stock["database_file"] = DB_FILE
    return stock


@mcp.tool
def check_paid_in_full(ticket_id: int) -> dict:
    """If inventory can fill the ticket, say whether it was paid in full.

    Paid in full means payments for this ticket id cover list price times
    quantity. The payment check runs only when the shelf can fill the ask.
    A short shelf or a ticket with no product is not treated as paid.
    """
    with _connect() as conn:
        ticket = _load_ticket(conn, ticket_id)
        if ticket is None:
            return _missing(ticket_id)
        stock = _stock(conn, ticket)
        if not stock["have_what_they_asked"]:
            reason = stock["reason"] if not stock["asks_for_product"] else (
                "Inventory cannot fill this request, so payment is not accepted."
            )
            return {
                "ticket_id": ticket_id,
                "database_file": DB_FILE,
                "checked_payment": False,
                "paid_in_full": False,
                "accept_payment": False,
                "reason": reason,
                "inventory": stock,
            }
        price = _price(conn, ticket["sku"])
        payments = _payments_for(conn, ticket_id)
    if price is None:
        return {
            "ticket_id": ticket_id,
            "database_file": DB_FILE,
            "checked_payment": False,
            "paid_in_full": False,
            "reason": f"No pricing row for {ticket['sku']}.",
            "inventory": stock,
        }
    amount_due = round(float(price["list_price"]) * int(stock["qty_requested"]), 2)
    amount_paid = round(sum(float(row["amount"]) for row in payments), 2)
    paid = amount_paid >= amount_due
    result = {
        "ticket_id": ticket_id,
        "database_file": DB_FILE,
        "checked_payment": True,
        "paid_in_full": paid,
        "amount_due": amount_due,
        "amount_paid": amount_paid,
        "price_basis": "list_price",
        "payments": payments,
        "inventory": stock,
    }
    if ticket["type"] == "price_override":
        result["paid_in_full"] = False
        result["reason"] = (
            "A bulk discount has no agreed price on file, so list price is not a paid-in-full answer."
        )
    return result


@mcp.tool
def hold_payment_and_request_restock(ticket_id: int) -> dict:
    """If the shelf cannot fill the ticket, refuse payment and ask providers to restock.

    Returns the note for the requester: payment is not accepted, and the shop
    will contact them when the item is available. Then checks every vendor and
    returns a restock request for each one. Nothing is emailed and no payment
    row is written, because this server only reads the database.
    """
    with _connect() as conn:
        ticket = _load_ticket(conn, ticket_id)
        if ticket is None:
            return _missing(ticket_id)
        stock = _stock(conn, ticket)
        if not stock["asks_for_product"]:
            return {
                "ticket_id": ticket_id,
                "database_file": DB_FILE,
                "applies": False,
                "accept_payment": False,
                "reason": "This ticket is not a product request, so there is nothing to restock.",
                "customer_message": None,
                "providers": [],
            }
        if stock["have_what_they_asked"]:
            return {
                "ticket_id": ticket_id,
                "database_file": DB_FILE,
                "applies": False,
                "accept_payment": None,
                "reason": "Inventory can fill this request. Use check_paid_in_full instead of refusing payment.",
                "customer_message": None,
                "providers": [],
            }
        vendors = [dict(row) for row in conn.execute("SELECT * FROM vendors ORDER BY id")]
        invoices = [
            dict(row)
            for row in conn.execute(
                """
                SELECT id, vendor_id, amount, due_date, status, description
                FROM invoices
                WHERE id = ? OR description LIKE ?
                """,
                (ticket.get("invoice_id"), f"%{ticket['sku']}%"),
            )
        ]
    name = stock["name"] or stock["sku"]
    qty_on_hand = stock["qty_on_hand"]
    qty_requested = stock["qty_requested"]
    if qty_on_hand <= 0:
        held = f"We do not have {name} in size {stock['size']} in inventory."
    else:
        held = (
            f"We do not have enough {name} in size {stock['size']} in inventory "
            f"({qty_on_hand} on hand, {qty_requested} requested)."
        )
    customer_message = (
        f"Hello {ticket['requester']}. {held} "
        "We have not accepted your payment. "
        "We will contact you when the item becomes available."
    )
    shortfall = stock["shortfall"]
    providers = []
    for vendor in vendors:
        can, why = _vendor_covers(vendor["specialty"], stock["sku"], name)
        open_bills = [bill for bill in invoices if bill["vendor_id"] == vendor["id"]]
        bill_note = ""
        if open_bills:
            bill = open_bills[0]
            bill_note = (
                f" Invoice {bill['id']} is already {bill['status']} "
                f"for ${bill['amount']:.0f} ({bill['description']})."
            )
        if can:
            message = (
                f"Hello {vendor['name']}, can you restock {shortfall} × {name} "
                f"({stock['sku']}) in size {stock['size']} so we can meet ticket {ticket_id}? "
                f"Your lead time on file is {vendor['lead_days']} days.{bill_note}"
            )
        else:
            message = (
                f"Hello {vendor['name']}, we checked a restock of {shortfall} × {name} "
                f"({stock['sku']}) in size {stock['size']} for ticket {ticket_id}. "
                f"{why} No restock is requested."
            )
        providers.append(
            {
                "vendor_id": vendor["id"],
                "name": vendor["name"],
                "specialty": vendor["specialty"],
                "lead_days": vendor["lead_days"],
                "can_restock": can,
                "why": why,
                "open_invoices": open_bills,
                "message": message,
                "emailed": False,
            }
        )
    return {
        "ticket_id": ticket_id,
        "database_file": DB_FILE,
        "applies": True,
        "accept_payment": False,
        "payment_recorded": False,
        "emailed": False,
        "reason": "No email address is stored for this requester or for the vendors.",
        "customer_message": customer_message,
        "shortfall": shortfall,
        "inventory": stock,
        "providers": providers,
    }


@mcp.tool
def list_open_tickets() -> dict:
    """List every open ticket so the boss can decide who should take it."""
    with _connect() as conn:
        rows = [
            dict(row)
            for row in conn.execute(
                """
                SELECT id, type, requester, subject, sku, size, qty, lease_id,
                       invoice_id, status, notes, created_at
                FROM tickets
                WHERE status = 'open'
                ORDER BY id
                """
            )
        ]
    return {"database_file": DB_FILE, "count": len(rows), "tickets": rows}


@mcp.tool
def check_stock(sku: str, size: str = "") -> dict:
    """Read inventory for one sku. Pass size to read that size only."""
    with _connect() as conn:
        if size:
            row = _inventory_row(conn, sku, size)
            rows = [row] if row else []
        else:
            rows = [
                dict(row)
                for row in conn.execute(
                    """
                    SELECT sku, name, size, qty, location
                    FROM inventory
                    WHERE sku = ?
                    ORDER BY size
                    """,
                    (sku,),
                )
            ]
    return {
        "database_file": DB_FILE,
        "sku": sku,
        "size": size or None,
        "row_found": bool(rows),
        "rows": rows,
    }


@mcp.tool
def list_shortages() -> dict:
    """Show shelf rows at zero and open tickets the shelf cannot fill."""
    with _connect() as conn:
        shelf = [
            dict(row)
            for row in conn.execute(
                """
                SELECT sku, name, size, qty, location
                FROM inventory
                WHERE qty <= 0
                ORDER BY sku, size
                """
            )
        ]
        tickets = [
            dict(row)
            for row in conn.execute(
                """
                SELECT * FROM tickets
                WHERE status = 'open' AND sku IS NOT NULL
                ORDER BY id
                """
            )
        ]
        short = []
        for ticket in tickets:
            stock = _stock(conn, ticket)
            if stock.get("shortfall"):
                short.append({"ticket_id": ticket["id"], "requester": ticket["requester"], **stock})
    return {"database_file": DB_FILE, "shelf_at_zero": shelf, "ticket_shortages": short}


@mcp.tool
def recommend_vendor(sku: str, qty: int = 1) -> dict:
    """Pick the vendor whose specialty can restock a sku, and say who cannot."""
    with _connect() as conn:
        named = conn.execute(
            "SELECT name FROM inventory WHERE sku = ? LIMIT 1",
            (sku,),
        ).fetchone()
        name = named["name"] if named else sku
        vendors = [dict(row) for row in conn.execute("SELECT * FROM vendors ORDER BY id")]
    choices = []
    for vendor in vendors:
        can, why = _vendor_covers(vendor["specialty"], sku, name)
        choices.append(
            {
                "vendor_id": vendor["id"],
                "name": vendor["name"],
                "specialty": vendor["specialty"],
                "lead_days": vendor["lead_days"],
                "can_restock": can,
                "why": why,
            }
        )
    chosen = next((row for row in choices if row["can_restock"]), None)
    return {
        "database_file": DB_FILE,
        "sku": sku,
        "name": name,
        "qty": qty,
        "vendor": chosen,
        "vendors": choices,
        "ordered": False,
    }


@mcp.tool
def read_cash() -> dict:
    """Read the shop cash accounts."""
    with _connect() as conn:
        rows = [dict(row) for row in conn.execute("SELECT name, balance, date FROM cash_accounts")]
    return {"database_file": DB_FILE, "accounts": rows}


@mcp.tool
def list_invoices() -> dict:
    """Read vendor invoices and the vendor on each bill."""
    with _connect() as conn:
        rows = [
            dict(row)
            for row in conn.execute(
                """
                SELECT i.id, i.vendor_id, v.name AS vendor_name, v.specialty, v.lead_days,
                       i.amount, i.due_date, i.status, i.description
                FROM invoices AS i
                LEFT JOIN vendors AS v ON v.id = i.vendor_id
                ORDER BY i.id
                """
            )
        ]
    return {"database_file": DB_FILE, "invoices": rows}


@mcp.tool
def check_margin(sku: str = "") -> dict:
    """Read unit cost, list price, and the margin for one sku or every sku."""
    with _connect() as conn:
        if sku:
            rows = conn.execute(
                "SELECT sku, unit_cost, list_price FROM pricing WHERE sku = ?",
                (sku,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT sku, unit_cost, list_price FROM pricing ORDER BY sku"
            ).fetchall()
    priced = []
    for row in rows:
        cost = float(row["unit_cost"])
        list_price = float(row["list_price"])
        margin = round(list_price - cost, 2)
        priced.append(
            {
                "sku": row["sku"],
                "unit_cost": cost,
                "list_price": list_price,
                "margin": margin,
                "margin_rate": round(margin / list_price, 4) if list_price else None,
            }
        )
    return {"database_file": DB_FILE, "sku": sku or None, "prices": priced}


@mcp.tool
def prepare_payment_or_po(
    kind: str,
    ref_id: int = 0,
    sku: str = "",
    size: str = "",
    qty: int = 0,
) -> dict:
    """Draft a payment or purchase order for the owner to approve.

    kind is invoice_payment (ref_id is the invoice id), rent_payment (ref_id is
    the lease id), or purchase_order (sku, size, and qty). Nothing is posted.
    """
    draft = {
        "database_file": DB_FILE,
        "kind": kind,
        "status": "awaiting_human_approval",
        "posted": False,
        "money_moved": False,
        "requires_human_approval": True,
    }
    with _connect() as conn:
        cash = [dict(row) for row in conn.execute("SELECT name, balance, date FROM cash_accounts")]
        balance = float(cash[0]["balance"]) if cash else 0.0
        draft["cash_accounts"] = cash
        if kind == "invoice_payment":
            row = conn.execute("SELECT * FROM invoices WHERE id = ?", (ref_id,)).fetchone()
            if row is None:
                draft["error"] = f"No invoice {ref_id}."
                return draft
            invoice = dict(row)
            vendor = conn.execute("SELECT * FROM vendors WHERE id = ?", (invoice["vendor_id"],)).fetchone()
            amount = float(invoice["amount"])
            draft.update(
                invoice=invoice,
                vendor=dict(vendor) if vendor else None,
                amount=amount,
                pay_from="checking",
                cash_after=round(balance - amount, 2),
                cash_short=amount > balance,
            )
            return draft
        if kind == "rent_payment":
            row = conn.execute("SELECT * FROM leases WHERE id = ?", (ref_id,)).fetchone()
            if row is None:
                draft["error"] = f"No lease {ref_id}."
                return draft
            lease = dict(row)
            amount = float(lease["monthly_rent"])
            draft.update(
                lease=lease,
                amount=amount,
                pay_from="checking",
                cash_after=round(balance - amount, 2),
                cash_short=amount > balance,
            )
            return draft
        if kind == "purchase_order":
            if not sku or not size or qty <= 0:
                draft["error"] = "A purchase order needs sku, size, and a qty above zero."
                return draft
            price = _price(conn, sku)
            stock = _inventory_row(conn, sku, size)
            if price is None:
                draft["error"] = f"No pricing row for {sku}."
                return draft
            name = stock["name"] if stock else sku
            amount = round(float(price["unit_cost"]) * qty, 2)
            vendors = [dict(row) for row in conn.execute("SELECT * FROM vendors ORDER BY id")]
            chosen = None
            for vendor in vendors:
                can, why = _vendor_covers(vendor["specialty"], sku, name)
                if can:
                    chosen = {**vendor, "why": why}
                    break
            draft.update(
                sku=sku,
                size=size,
                qty=qty,
                name=name,
                unit_cost=float(price["unit_cost"]),
                amount=amount,
                vendor=chosen,
                cash_after=round(balance - amount, 2),
                cash_short=amount > balance,
            )
            return draft
    draft["error"] = "kind must be invoice_payment, rent_payment, or purchase_order."
    return draft


@mcp.tool
def read_shop_space() -> dict:
    """Read the lease, the shop date, and cash so rent can be compared with the balance."""
    from datetime import date

    with _connect() as conn:
        leases = [dict(row) for row in conn.execute("SELECT * FROM leases ORDER BY id")]
        desk = dict(conn.execute("SELECT date_today, notes FROM desk").fetchone())
        cash = [dict(row) for row in conn.execute("SELECT name, balance, date FROM cash_accounts")]
    today = date.fromisoformat(desk["date_today"])
    for lease in leases:
        due = date.fromisoformat(lease["next_due"])
        lease["days_until_due"] = (due - today).days
    return {"database_file": DB_FILE, "desk": desk, "leases": leases, "cash_accounts": cash}


@mcp.tool
def draft_customer_message(ticket_id: int) -> dict:
    """Draft a customer message for one ticket. It is not emailed or called.

    The owner has to check the draft before any email or phone call.
    """
    held = {
        "ticket_id": ticket_id,
        "database_file": DB_FILE,
        "requires_human_approval": True,
        "emailed": False,
        "called": False,
        "delivered": False,
    }
    with _connect() as conn:
        ticket = _load_ticket(conn, ticket_id)
        if ticket is None:
            return _missing(ticket_id) | held
        stock = _stock(conn, ticket)
    if not stock["asks_for_product"]:
        held.update(
            applies=False,
            draft=None,
            reason="This ticket is not a product request, so there is no customer-item message to send.",
        )
        return held
    name = stock["name"] or stock["sku"]
    if stock["have_what_they_asked"]:
        body = (
            f"Hello {ticket['requester']}. We have {stock['qty_requested']} "
            f"{name} in size {stock['size']} on hand."
        )
    elif stock["qty_on_hand"] <= 0:
        body = (
            f"Hello {ticket['requester']}. We do not have {name} in size {stock['size']} "
            "in inventory. We have not accepted your payment. "
            "We will contact you when the item becomes available."
        )
    else:
        body = (
            f"Hello {ticket['requester']}. We do not have enough {name} in size {stock['size']} "
            f"({stock['qty_on_hand']} on hand, {stock['qty_requested']} requested). "
            "We have not accepted your payment. "
            "We will contact you when the item becomes available."
        )
    held.update(
        applies=True,
        requester=ticket["requester"],
        draft=body,
        reason="Owner must check this draft before any email or phone call.",
        inventory=stock,
    )
    return held


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Campus Customs MCP server")
    parser.add_argument(
        "--http",
        action="store_true",
        help="Serve Streamable HTTP on port 8001",
    )
    args = parser.parse_args()
    if args.http:
        mcp.run(transport="http", host="127.0.0.1", port=8001)
    else:
        mcp.run()
