#!/usr/bin/env python3
"""
Willys scraper — interacts with the Willys supermarket account via REST API.

Usage:
    python3 willys.py cart
    python3 willys.py orders
    python3 willys.py search --query "mjölk"
    python3 willys.py slots
    python3 willys.py profile

Credentials are read from env vars WILLYS_EMAIL / WILLYS_PASSWORD.
Optional: WILLYS_POSTAL_CODE for delivery slot lookup.
"""

import argparse
import json
import os
import sys

try:
    import requests
except ImportError as e:
    print(json.dumps({"error": f"Missing dependency: {e}. Run: pip install requests"}))
    sys.exit(1)

BASE = "https://www.willys.se"
API = f"{BASE}/axfood/rest"


def authenticate(session: requests.Session, email: str, password: str) -> None:
    resp = session.post(
        f"{BASE}/login",
        json={"j_username": email, "j_password": password, "j_remember_me": True},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("login_successful") != "true":
        raise ValueError(f"Authentication failed — invalid credentials")


def get_cart(session: requests.Session) -> dict:
    resp = session.get(f"{API}/cart", timeout=15)
    resp.raise_for_status()
    data = resp.json()

    entries = []
    for entry in data.get("products", []):
        entries.append({
            "name": entry.get("name", ""),
            "quantity": entry.get("quantity", 1),
            "price": entry.get("priceValue", 0),
            "price_formatted": entry.get("price", ""),
        })

    return {
        "entries": entries,
        "total": data.get("totalPrice", ""),
        "item_count": data.get("totalItems", len(entries)),
    }


def get_orders(session: requests.Session) -> list:
    resp = session.get(f"{API}/account/orders", timeout=15)
    resp.raise_for_status()
    data = resp.json()

    raw = data if isinstance(data, list) else data.get("orders", [])
    orders = []
    for order in raw:
        orders.append({
            "id": order.get("orderNumber", order.get("code", "")),
            "date": order.get("formattedOrderDate", ""),
            "total": order.get("reservedAmount", ""),
            "status": order.get("statusDisplay", order.get("completedStatus", "")),
        })
    return orders


def search_products(session: requests.Session, query: str) -> list:
    resp = session.get(
        f"{BASE}/search",
        params={"q": query, "size": 20},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    products = []
    for product in data.get("results", []):
        products.append({
            "name": product.get("name", ""),
            "price": product.get("price", ""),
            "price_value": product.get("priceValue", 0),
            "unit": product.get("comparePriceUnit", ""),
            "code": product.get("code", ""),
        })
    return products


def get_delivery_slots(session: requests.Session, postal_code: str) -> list:
    resp = session.get(
        f"{BASE}/tms/delivery-slots",
        params={"postalCode": postal_code},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    slots = []
    raw_slots = data if isinstance(data, list) else data.get("slots", data.get("deliverySlots", []))
    for slot in raw_slots:
        slots.append({
            "date": slot.get("date", slot.get("deliveryDate", "")),
            "start": slot.get("startTime", slot.get("start", "")),
            "end": slot.get("endTime", slot.get("end", "")),
            "available": slot.get("available", slot.get("status", "") != "FULL"),
            "status": slot.get("status", ""),
        })
    return slots


def get_profile(session: requests.Session) -> dict:
    resp = session.get(f"{API}/customer", timeout=15)
    resp.raise_for_status()
    data = resp.json()

    address = {}
    addresses = data.get("addresses", [])
    if addresses:
        addr = addresses[0]
        address = {
            "street": addr.get("line1", ""),
            "city": addr.get("town", ""),
            "postal_code": addr.get("postalCode", ""),
        }

    loyalty = data.get("loyaltyCardDetails", data.get("loyalty", {}))
    points = loyalty.get("points", loyalty.get("balance", 0)) if isinstance(loyalty, dict) else 0
    level = loyalty.get("tierName", loyalty.get("level", "")) if isinstance(loyalty, dict) else ""

    return {
        "name": f"{data.get('firstName', '')} {data.get('lastName', '')}".strip(),
        "email": data.get("email", data.get("uid", "")),
        "points": points,
        "level": level,
        "address": address,
    }


def main():
    parser = argparse.ArgumentParser(description="Willys account scraper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("cart", help="Show current cart")
    subparsers.add_parser("orders", help="Show order history")

    search_parser = subparsers.add_parser("search", help="Search for products")
    search_parser.add_argument("--query", required=True, help="Search term")

    subparsers.add_parser("slots", help="Show delivery slots")
    subparsers.add_parser("profile", help="Show customer profile")

    args = parser.parse_args()

    email = os.environ.get("WILLYS_EMAIL", "")
    password = os.environ.get("WILLYS_PASSWORD", "")

    if not email or not password:
        print(json.dumps({"error": "Missing credentials. Set WILLYS_EMAIL and WILLYS_PASSWORD environment variables."}))
        sys.exit(1)

    if args.command == "slots":
        postal_code = os.environ.get("WILLYS_POSTAL_CODE", "")
        if not postal_code:
            print(json.dumps({"error": "Set WILLYS_POSTAL_CODE environment variable to use delivery slots."}))
            sys.exit(1)

    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    })

    try:
        authenticate(session, email, password)

        if args.command == "cart":
            result = get_cart(session)
        elif args.command == "orders":
            result = {"orders": get_orders(session)}
        elif args.command == "search":
            result = {"query": args.query, "products": search_products(session, args.query)}
        elif args.command == "slots":
            postal_code = os.environ.get("WILLYS_POSTAL_CODE", "")
            result = {"postal_code": postal_code, "slots": get_delivery_slots(session, postal_code)}
        elif args.command == "profile":
            result = get_profile(session)

        print(json.dumps(result, ensure_ascii=False, indent=2))

    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
