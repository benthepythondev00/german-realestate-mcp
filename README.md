# German Used Cars — MCP server

A free [MCP](https://modelcontextprotocol.io) server that gives your AI agent **structured
German used-car listings from mobile.de**. One tool, clean JSON, no scraping headaches.

mobile.de has no public API and blocks ordinary scrapers with Akamai bot protection — this
server is powered by a hardened Apify actor (Camoufox stealth browser + German residential
proxy) that gets the data reliably. That's the hard part; you just call a tool.

## Tool

### `search_used_cars`
Search listings by the usual filters and get back structured cars.

| Param | Type | Example |
|---|---|---|
| `make` | string | `"BMW"` |
| `model` | string | `"320d"` |
| `price_min` / `price_max` | int (EUR) | `15000` / `30000` |
| `year_min` | int | `2018` |
| `mileage_max` | int (km) | `120000` |
| `fuel` | string | `petrol`, `diesel`, `hybrid`, `electric`, `lpg`, `cng` |
| `transmission` | string | `manual`, `automatic`, `semi` |
| `zip_code` + `radius_km` | string + int | `"80331"`, `50` |
| `limit` | int | `10` (free tier capped) |

Returns `{ "listings": [ { make, model, year, mileage_km, price_eur, fuel, transmission, power_kw, location, url, ... } ], "note": "..." }`.

## Quick start (Claude Desktop / Cursor / any MCP client)

```bash
git clone <this repo> && cd cardata-mcp
python3.11 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
```

Add to your MCP client config (e.g. Claude Desktop `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "german-cars": {
      "command": "/absolute/path/cardata-mcp/venv/bin/python",
      "args": ["/absolute/path/cardata-mcp/src/server.py"],
      "env": {
        "APIFY_TOKEN": "your_apify_token",
        "CARDATA_ACTOR_ID": "your-username/mobile-de-scraper"
      }
    }
  }
}
```

Then ask your agent: *"Find me diesel BMW 3-series under €25k, max 120k km, near Munich."*

## Demo mode
Run it with **no** `APIFY_TOKEN` / `CARDATA_ACTOR_ID` and it returns realistic sample
listings — so you can wire it up and see the shape instantly before connecting live data.

## Live data
Live results come from an Apify actor you control:
1. Deploy the mobile.de actor to your Apify account (`apify push`).
2. Set `APIFY_TOKEN` and `CARDATA_ACTOR_ID` (e.g. `your-username/mobile-de-scraper`).

The actor uses Apify's German residential proxy + Camoufox to get past Akamai.

## Free tier & beyond
The free tier caps results per call (`CARDATA_FREE_LIMIT`, default 10). A paid API (full
pages, AutoScout24 as a second source, price history, higher limits) is the next step — the
free MCP server is the front door.

## Develop
```bash
pip install -r requirements-dev.txt
pytest
```

## Legal
Returns listing data only (make/model/price/mileage/etc.) — no seller personal data. Use in
line with mobile.de's terms and applicable law.
