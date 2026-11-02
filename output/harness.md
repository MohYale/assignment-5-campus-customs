# Harness

The agents read `data/campus_customs.db`. The shop date in `desk` is 2026-08-31. These nine tables are what the agents can use. A working copy of the original file is `data/campus_customs_new.db`.

## tickets

`tickets` is the work queue: each open row is one request an agent has to resolve, and it points at the product, lease, or invoice involved.

Fields: `id`, `type`, `requester`, `subject`, `sku`, `size`, `qty`, `lease_id`, `invoice_id`, `status`, `notes`, `created_at`.

## inventory

`inventory` is the stock on the shelf, so an agent can tell whether a requested size can be filled.

Fields: `sku`, `name`, `size`, `qty`, `location`.

## pricing

`pricing` is the cost and the list price of each product, so an agent can judge a discount or a reorder against margin.

Fields: `sku`, `unit_cost`, `list_price`.

## invoices

`invoices` is money the shop still owes a vendor, so an agent can see the bill attached to a ticket and whether it is already due.

Fields: `id`, `vendor_id`, `amount`, `due_date`, `status`, `description`.

## vendors

`vendors` is who supplies a bill and how long they take, so an agent can plan a reprint or a restock.

Fields: `id`, `name`, `specialty`, `lead_days`.

## leases

`leases` is the shop's rent, so an agent can act on a rent notice before the due date.

Fields: `id`, `space_name`, `landlord`, `monthly_rent`, `next_due`, `notes`.

## payments

`payments` is money an agent has already sent, tied to a bill or a lease and drawn from a cash account.

Fields: `id`, `kind`, `ref_id`, `amount`, `account`, `paid_at`, `approved_by`.

## cash_accounts

`cash_accounts` is the shop's cash, so an agent can tell whether a payment can be made.

Fields: `name`, `balance`, `date`.

## desk

`desk` is the date the shop is operating on, so an agent can judge what is due today and what is still ahead.

Fields: `date_today`, `notes`.

## MCP tools

The agents call the server in `mcp_server/`. That server reads `data/campus_customs_new.db` and does not write to it.

### assess_ticket_request

Reads `tickets`. A product ticket also reads `inventory` and `pricing`. A linked bill also reads `invoices` and `vendors`. A lease also reads `leases`, `cash_accounts`, and `desk`. It always reads `payments`.

- Ticket 101: This is the right first tool because the order asks for one size-S Bulldog tee, and the answer sits in inventory plus the open reprint invoice.
- Ticket 102: This is the right first tool because the notice asks for Chapel Street rent, and the answer sits in the lease rather than on a shelf.
- Ticket 103: This is the right first tool because the club asks for a bulk discount on 20 medium hoodies, and the answer sits in inventory and pricing.

### check_inventory_for_ticket

Reads `tickets` and `inventory`.

- Ticket 101: This is the right stock tool because the tee they want is size S and that row has quantity 0.
- Ticket 102: This tool tells the agent to leave the shelf alone because the rent notice has no sku.
- Ticket 103: This is the right stock tool because the club wants 20 medium hoodies and the shelf has 8.

### check_paid_in_full

Reads `tickets`, `inventory`, `pricing`, and `payments`.

- Ticket 101: This is the right payment tool for a tee the shop could sell, and it withholds payment because size S is not in stock.
- Ticket 102: This tool does not unlock the rent notice because there is no item on the ticket to have been paid for.
- Ticket 103: This is the right payment tool for the hoodie order, and it withholds a paid-in-full answer because 8 on hand do not cover 20.

### hold_payment_and_request_restock

Reads `tickets`, `inventory`, `vendors`, and `invoices`.

- Ticket 101: This is the right tool because the tee is out of stock, so payment stays unaccepted, the customer is told we will write when it is back, and Bulldog Print Co is the apparel provider to restock it.
- Ticket 102: This tool does not unlock the rent notice because a lease is not a product a vendor restocks.
- Ticket 103: This is the right tool because 20 medium hoodies are not on the shelf, so payment stays unaccepted and the apparel provider is asked to cover the shortfall of 12.

### list_open_tickets

Reads `tickets`.

The boss uses this to see the open work before choosing a specialist.

### check_stock

Reads `inventory`.

The inventory agent uses this to read one sku, or one sku and size.

### list_shortages

Reads `inventory` and `tickets`.

The inventory agent uses this to see shelf rows at zero and open tickets the shelf cannot fill.

### recommend_vendor

Reads `vendors` and `inventory`.

The inventory agent uses this to match a short sku to the vendor whose specialty covers it.

### read_cash

Reads `cash_accounts`.

The accounting agent uses this to see the checking balance before a draft.

### list_invoices

Reads `invoices` and `vendors`.

The accounting agent uses this to see which vendor bills are still open.

### check_margin

Reads `pricing`.

The accounting agent uses this to compare unit cost with list price.

### prepare_payment_or_po

Reads `cash_accounts`. An invoice draft also reads `invoices` and `vendors`. A rent draft also reads `leases`. A purchase order also reads `pricing`, `inventory`, and `vendors`.

The accounting agent uses this to draft an invoice payment, a rent payment, or a purchase order. The draft is not posted.

### read_shop_space

Reads `leases`, `desk`, and `cash_accounts`.

The facilities agent uses this to compare the rent due date and amount with the shop date and the cash balance.

### draft_customer_message

Reads `tickets` and `inventory`.

The customer-service agent uses this to draft a message. The draft is not emailed or called.

## Agents

The team is in `backend/`. The loop is `backend/team.py`. Any agent can hand a task to any other agent. The next agent still reads shop facts from the MCP server. The loop does not open the database.

### Boss

`backend/boss.py`. Reads each open ticket, chooses the specialist, and makes the final call.

MCP tools: `list_open_tickets` (`tickets`), `assess_ticket_request` (`tickets`, plus the `inventory`, `pricing`, `invoices`, `vendors`, `leases`, `cash_accounts`, `payments`, and `desk` rows that ticket points at).

### Inventory

`backend/inventory.py`. Checks stock by SKU and size, names shortages, and picks the vendor for a restock.

MCP tools: `check_stock` (`inventory`), `list_shortages` (`inventory`, `tickets`), `recommend_vendor` (`vendors`, `inventory`), `check_inventory_for_ticket` (`tickets`, `inventory`).

### Accounting

`backend/accounting.py`. Watches cash and invoices, checks margins, and prepares a payment or purchase order for approval.

MCP tools: `read_cash` (`cash_accounts`), `list_invoices` (`invoices`, `vendors`), `check_margin` (`pricing`), `check_paid_in_full` (`tickets`, `inventory`, `pricing`, `payments`), `prepare_payment_or_po` (`cash_accounts`, plus `invoices` and `vendors`, or `leases`, or `pricing`, `inventory`, and `vendors`).

### Facilities

`backend/facilities.py`. Handles the shop space: the lease, the rent, and the shop date.

MCP tools: `read_shop_space` (`leases`, `desk`, `cash_accounts`), `assess_ticket_request` (`tickets` and the lease tables that ticket points at).

### Customer service

`backend/customer_service.py`. Drafts messages for the requester.

MCP tools: `draft_customer_message` (`tickets`, `inventory`), `hold_payment_and_request_restock` (`tickets`, `inventory`, `vendors`, `invoices`).

## Safety

Check with you before any transaction or money movement is completed. `prepare_payment_or_po` only returns a draft with status `awaiting_human_approval`. The MCP server still opens the database read-only. `POST /api/approve` is the human click that posts the payment and changes the checking balance.

No email or phone call goes to a customer, a landlord, or a vendor without checking with you. `draft_customer_message` and `hold_payment_and_request_restock` return wording only. The shop tables do not store an email address or a phone number, and these tools do not send either one.

## Routes

- `GET /api/tickets` — returns the three tickets and whether each is open or resolved.
- `POST /api/tickets/{ticket_id}/run` — runs the agent team on that one ticket and marks the ticket resolved when the run finishes.
- `GET /api/events` — returns recent agent steps: who called whom, what each agent thought and said, and which tools it used.
- `POST /api/approve` — after a human approves, posts the prepared payment or purchase and changes checking cash.
- `GET /api/cash` — returns the current checking balance from `cash_accounts`.
- `POST /api/reset` — copies `data/campus_customs.db` back over `data/campus_customs_new.db` for a fresh run.

## Dashboard

The board is the React, Vite, and TypeScript app in `frontend/`. `npm run dev` serves it at `http://localhost:5173`, and the page calls `http://localhost:8000`. The API allows that origin.

The board lists tickets 101, 102, and 103, starts the team on the selected ticket, and polls `GET /api/events` while the run is going. Each step shows who called whom, what the agent thought and said, and which tools ran. When the run finishes, `POST /api/tickets/{ticket_id}/run` marks that ticket resolved and the card updates. A short summary collects the last reply from each agent who spoke. Approving a prepared payment or purchase posts `POST /api/approve` and the checking figure updates from the new balance. Splinter stands for the boss. Leonardo, Donatello, Raphael, and Michelangelo stand for inventory, accounting, facilities, and customer service. The look is written in `output/design.md`.

Real runs append to `output/audit_trail.json`. A reset does not clear that file.
