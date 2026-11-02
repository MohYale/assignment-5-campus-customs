# Campus Customs MCP server

This server is the tool layer for every agent in Assignment 5. Agents call these tools instead of opening the database themselves.

Database file: `data/campus_customs_new.db`. The server only reads that file. The five agents in `backend/` call these tools. A payment or purchase-order tool returns a draft for the owner to check. A message tool returns wording only. Nothing is paid, emailed, or called.

## Tools

1. `assess_ticket_request` — what the ticket is asking the shop to provide, and which tables can answer it.
2. `check_inventory_for_ticket` — whether the shelf has the sku, size, and quantity on the ticket.
3. `check_paid_in_full` — if the shelf can fill the request, whether `payments` covers list price times quantity.
4. `hold_payment_and_request_restock` — if the shelf cannot fill the request, refuse payment and return the customer note and the provider requests. Nothing is sent.
5. `list_open_tickets` — every ticket whose status is open.
6. `check_stock` — inventory rows for a sku, or for one sku and size.
7. `list_shortages` — shelf rows at zero, and open tickets the shelf cannot fill.
8. `recommend_vendor` — which vendor's specialty can restock a sku, and which cannot.
9. `read_cash` — the shop cash accounts.
10. `list_invoices` — vendor invoices and the vendor on each bill.
11. `check_margin` — unit cost, list price, and margin for one sku or every sku.
12. `prepare_payment_or_po` — a draft invoice payment, rent payment, or purchase order. Status stays `awaiting_human_approval`. Nothing is posted.
13. `read_shop_space` — the lease, the shop date, and cash, so rent can be compared with the balance.
14. `draft_customer_message` — a customer draft for one ticket. It is not emailed or called. The owner checks it first.

Run from this folder after `pip install -r requirements.txt`:

```
python mcp_server.py
python mcp_server.py --http
```

HTTP URL: `http://127.0.0.1:8001/mcp`
