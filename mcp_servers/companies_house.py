"""Companies House (UK): company search, profile, officers and filing history.
Needs COMPANIES_HOUSE_API_KEY (free; developer.company-information.service.gov.uk). Read-only.
Rate limit: 600 requests per 5 minutes."""
from __future__ import annotations

import base64
import os

from mcp.server.fastmcp import FastMCP

from _common import fetch_json, out

API = "https://api.company-information.service.gov.uk"
mcp = FastMCP("companies_house")


def get(path: str, params: dict | None = None) -> dict:
    token = base64.b64encode(f"{os.environ['COMPANIES_HOUSE_API_KEY']}:".encode()).decode()
    return fetch_json(API + path, params, {"Authorization": f"Basic {token}"})


@mcp.tool()
def search_companies(query: str, limit: int = 5) -> str:
    """Search UK companies by name. Returns company numbers to use with the other tools."""
    items = get("/search/companies", {"q": query, "items_per_page": min(limit, 20)}).get("items", [])
    return out("Companies House", [{"number": i["company_number"], "name": i["title"], "status": i.get("company_status"),
                                    "incorporated": i.get("date_of_creation"), "address": i.get("address_snippet")} for i in items])


@mcp.tool()
def company_profile(company_number: str) -> str:
    """Registered details for one company: status, type, SIC codes, accounts and confirmation statement dates."""
    d = get(f"/company/{company_number}")
    keep = ("company_name", "company_number", "company_status", "type", "date_of_creation", "sic_codes",
            "registered_office_address", "accounts", "confirmation_statement", "has_insolvency_history")
    return out("Companies House", {k: d.get(k) for k in keep})


@mcp.tool()
def company_officers(company_number: str, limit: int = 20) -> str:
    """Current and former officers (directors, secretaries) of one company."""
    items = get(f"/company/{company_number}/officers", {"items_per_page": min(limit, 50)}).get("items", [])
    return out("Companies House", [{"name": i.get("name"), "role": i.get("officer_role"), "appointed": i.get("appointed_on"),
                                    "resigned": i.get("resigned_on"), "nationality": i.get("nationality")} for i in items])


@mcp.tool()
def filing_history(company_number: str, limit: int = 10, category: str = "") -> str:
    """Most recent filings for one company. category can be 'accounts', 'confirmation-statement', 'officers', etc."""
    items = get(f"/company/{company_number}/filing-history",
                {"items_per_page": min(limit, 50), "category": category or None}).get("items", [])
    return out("Companies House", [{"date": i.get("date"), "type": i.get("type"), "category": i.get("category"),
                                    "description": i.get("description")} for i in items])


if __name__ == "__main__":
    mcp.run()
