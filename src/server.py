"""German Used-Car Listings — free MCP server.

Exposes one tool, `search_used_cars`, returning structured used-car listings from
mobile.de. Powered by an Apify actor (Camoufox + DE residential proxy) that bypasses
mobile.de's Akamai bot protection — which is what makes this data hard to get and
worth an API.

Free tier: results are capped. Set APIFY_TOKEN + CARDATA_ACTOR_ID for live data;
without them the server runs in demo mode with sample listings so it works instantly.
"""
from __future__ import annotations

import os
from typing import Any

from mcp.server.fastmcp import FastMCP

APIFY_TOKEN = os.environ.get("APIFY_TOKEN", "")
ACTOR_ID = os.environ.get("CARDATA_ACTOR_ID", "")
FREE_LIMIT = int(os.environ.get("CARDATA_FREE_LIMIT", "10"))
UPGRADE_URL = os.environ.get("CARDATA_UPGRADE_URL", "https://example.com")

mcp = FastMCP("German Used Cars")

_FUEL_MAP = {
    "petrol": "PETROL", "benzin": "PETROL", "gas": "PETROL",
    "diesel": "DIESEL",
    "hybrid": "HYBRID",
    "electric": "ELECTRICITY", "ev": "ELECTRICITY", "elektro": "ELECTRICITY",
    "lpg": "LPG", "cng": "CNG",
}
_TRANS_MAP = {
    "manual": "MANUAL_GEAR", "schaltgetriebe": "MANUAL_GEAR",
    "automatic": "AUTOMATIC_GEAR", "automatik": "AUTOMATIC_GEAR", "auto": "AUTOMATIC_GEAR",
    "semi": "SEMIAUTOMATIC_GEAR", "semiautomatic": "SEMIAUTOMATIC_GEAR",
}

_FIELDS = (
    "title", "make", "model", "year", "first_registration", "mileage_km",
    "price_eur", "fuel", "transmission", "power_kw", "power_ps", "location", "url",
)


def _normalize(item: dict[str, Any]) -> dict[str, Any]:
    return {k: item.get(k) for k in _FIELDS if item.get(k) is not None}


def _demo(limit: int) -> list[dict[str, Any]]:
    base = [
        {"title": "BMW 320d Touring M Sport", "make": "BMW", "model": "320d", "year": 2019,
         "mileage_km": 98000, "price_eur": 21900, "fuel": "Diesel", "transmission": "Automatik",
         "power_kw": 140, "power_ps": 190, "location": "80331 München",
         "url": "https://suchen.mobile.de/auto/inserat/demo-1"},
        {"title": "Audi A4 Avant 40 TDI quattro", "make": "Audi", "model": "A4", "year": 2020,
         "mileage_km": 76500, "price_eur": 25450, "fuel": "Diesel", "transmission": "Automatik",
         "power_kw": 150, "power_ps": 204, "location": "10115 Berlin",
         "url": "https://suchen.mobile.de/auto/inserat/demo-2"},
        {"title": "VW Golf VIII 1.5 TSI Life", "make": "Volkswagen", "model": "Golf", "year": 2021,
         "mileage_km": 42300, "price_eur": 22990, "fuel": "Benzin", "transmission": "Schaltgetriebe",
         "power_kw": 110, "power_ps": 150, "location": "50667 Köln",
         "url": "https://suchen.mobile.de/auto/inserat/demo-3"},
    ]
    return (base * (limit // len(base) + 1))[:limit]


def _search(
    make: str | None = None,
    model: str | None = None,
    price_min: int | None = None,
    price_max: int | None = None,
    year_min: int | None = None,
    mileage_max: int | None = None,
    fuel: str | None = None,
    transmission: str | None = None,
    zip_code: str | None = None,
    radius_km: int = 0,
    limit: int = 10,
) -> dict[str, Any]:
    capped = max(1, min(limit or FREE_LIMIT, FREE_LIMIT))

    if not APIFY_TOKEN or not ACTOR_ID:
        return {
            "listings": _demo(capped),
            "demo": True,
            "note": (
                "Demo data (APIFY_TOKEN / CARDATA_ACTOR_ID not set). "
                "Configure them to return live mobile.de listings."
            ),
        }

    from apify_client import ApifyClient  # lazy: demo mode needs no extra deps

    run_input: dict[str, Any] = {
        "maxResults": capped,
        "radiusKm": radius_km or 0,
        "proxyConfiguration": {
            "useApifyProxy": True,
            "apifyProxyGroups": ["RESIDENTIAL"],
            "apifyProxyCountry": "DE",
        },
    }
    if make:
        run_input["make"] = make
    if model:
        run_input["model"] = model
    if price_min is not None:
        run_input["minPrice"] = price_min
    if price_max is not None:
        run_input["maxPrice"] = price_max
    if year_min is not None:
        run_input["minYear"] = year_min
    if mileage_max is not None:
        run_input["maxMileage"] = mileage_max
    if fuel:
        run_input["fuel"] = _FUEL_MAP.get(fuel.lower(), "")
    if transmission:
        run_input["transmission"] = _TRANS_MAP.get(transmission.lower(), "")
    if zip_code:
        run_input["zipCode"] = zip_code

    client = ApifyClient(APIFY_TOKEN)
    run = client.actor(ACTOR_ID).call(run_input=run_input)
    if not run or not run.get("defaultDatasetId"):
        return {"listings": [], "note": "No results (actor run failed)."}
    items = client.dataset(run["defaultDatasetId"]).list_items(limit=capped).items
    listings = [_normalize(i) for i in items][:capped]
    return {
        "listings": listings,
        "count": len(listings),
        "note": (
            f"Free tier: up to {FREE_LIMIT} results from mobile.de. "
            f"Full pages + AutoScout24 + price history → {UPGRADE_URL}"
        ),
    }


@mcp.tool()
def search_used_cars(
    make: str | None = None,
    model: str | None = None,
    price_min: int | None = None,
    price_max: int | None = None,
    year_min: int | None = None,
    mileage_max: int | None = None,
    fuel: str | None = None,
    transmission: str | None = None,
    zip_code: str | None = None,
    radius_km: int = 0,
    limit: int = 10,
) -> dict[str, Any]:
    """Search German used-car listings from mobile.de and return structured results.

    Args:
        make: Manufacturer, e.g. "BMW", "Audi", "Volkswagen".
        model: Model, e.g. "320d", "A4", "Golf".
        price_min: Minimum price in EUR.
        price_max: Maximum price in EUR.
        year_min: Earliest first-registration year, e.g. 2018.
        mileage_max: Maximum mileage in km.
        fuel: petrol, diesel, hybrid, electric, lpg or cng.
        transmission: manual, automatic or semi.
        zip_code: German postal code (PLZ) for a radius search.
        radius_km: Search radius around zip_code in km (0 = nationwide).
        limit: Max listings to return (free tier is capped).
    """
    return _search(
        make=make, model=model, price_min=price_min, price_max=price_max,
        year_min=year_min, mileage_max=mileage_max, fuel=fuel,
        transmission=transmission, zip_code=zip_code, radius_km=radius_km, limit=limit,
    )


def run() -> None:
    mcp.run()


if __name__ == "__main__":
    run()
