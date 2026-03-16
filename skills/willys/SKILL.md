---
name: willys
description: Interact with your Willys supermarket account — cart, orders, product search, delivery slots, and profile.
metadata: {"openclaw":{"emoji":"🛒","requires":{"bins":["python3"],"env":["WILLYS_EMAIL","WILLYS_PASSWORD"]}}}
---

## What it does

Authenticates with the Willys Swedish supermarket site (https://www.willys.se) and provides:
- Current shopping cart contents and totals
- Order history
- Product search by keyword
- Available delivery slots (requires postal code)
- Customer profile with loyalty points and addresses

Data is fetched live from `www.willys.se` on every invocation. Nothing is cached.

## Inputs

| Source | Name | Required | Description |
|--------|------|----------|-------------|
| env | `WILLYS_EMAIL` | yes | Willys account email address |
| env | `WILLYS_PASSWORD` | yes | Willys account password |
| env | `WILLYS_POSTAL_CODE` | no | Postal code for delivery slot lookup (e.g. `11234`) |

Credentials must be set as environment variables before invoking this skill. They are never stored in chat output.

## Workflow

1. **Verify env vars** — check that `WILLYS_EMAIL` and `WILLYS_PASSWORD` are set. If either is missing, abort immediately with:
   > "Willys credentials not configured. Please set WILLYS_EMAIL and WILLYS_PASSWORD environment variables."

2. **Run scraper** — find this skill's directory and execute the appropriate subcommand:
   ```bash
   python3 "$SKILL_DIR/willys.py cart
   python3 "$SKILL_DIR/willys.py orders
   python3 "$SKILL_DIR/willys.py search --query "<term>"
   python3 "$SKILL_DIR/willys.py slots
   python3 "$SKILL_DIR/willys.py profile
   ```
   Credentials are picked up automatically from the environment.

3. **Parse JSON output** — the script prints a single JSON object to stdout. If the top-level key is `"error"`, treat it as a failure (see Failure handling).

4. **Format summary** — present the data as a human-readable summary (see Output format).

## Subcommands

| User intent | Subcommand | Notes |
|-------------|------------|-------|
| "what's in my cart" | `cart` | Items, quantities, totals |
| "show my orders" | `orders` | List of past orders |
| "search for X" | `search --query "X"` | Product search by keyword |
| "delivery slots" | `slots` | Requires `WILLYS_POSTAL_CODE` |
| "my profile / points" | `profile` | Name, loyalty points, addresses |

## Output format

### Cart (`cart`)
```
🛒 Willys — Cart

  2x  Arla Mellanmjölk 1.5% 1L          39.90 kr
  1x  Pågen Frukostfranska               24.90 kr
  ...
─────────────────────────────────────────────────
Total: 64.80 kr  (3 items)
```
- One line per item: quantity, name, line price
- Show subtotal and total at the bottom
- If cart is empty: "Your cart is empty."

### Orders (`orders`)
```
📦 Willys — Order History

  2024-11-20  Order #4521890   198.50 kr   Delivered
  2024-11-13  Order #4498201   312.00 kr   Delivered
  ...
```
- One line per order: date, order ID, total, status
- Most recent first
- If no orders: "No order history found."

### Search (`search`)
```
🔍 Willys — Search: "mjölk"

  Arla Mellanmjölk 1.5% 1L              19.95 kr
  Arla Ekologisk Mellanmjölk 1L          24.95 kr
  Oatly Havredryck Naturell 1L           22.95 kr
  ...
```
- Name and price per result
- Show up to 20 results
- If no results: "No products found for '<query>'."

### Delivery slots (`slots`)
```
🚚 Willys — Delivery Slots (postal code: 11234)

  Mon 25 Nov  08:00–12:00   Available
  Mon 25 Nov  12:00–16:00   Available
  Mon 25 Nov  16:00–20:00   Full
  ...
```
- Date, time window, availability
- If no slots: "No delivery slots available for postal code <code>."
- If `WILLYS_POSTAL_CODE` not set: "Set WILLYS_POSTAL_CODE to look up delivery slots."

### Profile (`profile`)
```
👤 Willys — Profile

  Name:    Anna Andersson
  Email:   anna@example.com
  Points:  1 250 p
  Level:   Guld
  Address: Storgatan 1, 112 34 Stockholm
```
- Omit fields that are empty or unavailable

## Guardrails

- **Read-only** — this skill only reads data. Cart mutations (add/remove items, place orders) are not supported because Willys blocks write operations from non-browser sessions at the server level — the API returns HTTP 500 for all add-to-cart attempts regardless of correct request format. A real browser session (Puppeteer/Playwright) would be required for write operations.
- **No credential leakage** — never echo, log, or include credentials in the chat summary.
- **No fabrication** — if a field is missing or empty, say so. Never invent product or order data.
- **Single source of truth** — all data comes directly from the scraper output. Do not supplement with guesses.

## Python dependencies

The skill requires only the `requests` package (standard in most Python 3 environments).

If missing:
```
pip install requests
```

## Failure handling

| Scenario | Action |
|----------|--------|
| Missing env vars | Abort before running the script; show the message from step 1 |
| Auth failure (HTTP 401 / "Authentication failed") | Show the raw error message and advise: "Check your WILLYS_EMAIL and WILLYS_PASSWORD." |
| `python3` not found | Advise: "python3 is required. Install it with your package manager." |
| Missing `requests` package | The script self-reports: "Run: pip install requests" |
| Missing `WILLYS_POSTAL_CODE` for slots | Report: "Set WILLYS_POSTAL_CODE environment variable to use delivery slots." |
| Any other exception | Show the error text verbatim; do not retry automatically. |
