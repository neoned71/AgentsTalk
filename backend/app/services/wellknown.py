from __future__ import annotations

import httpx
from typing import Any

WELL_KNOWN_PATHS = ["/.well-known/agentshub.json", "/.well-known/mcp.json"]


async def fetch_manifests(domain: str) -> dict[str, Any]:
    from app.services.security import validate_public_host
    ok, host = validate_public_host(domain)
    if not ok:
        return {"domain": domain, "mcp": None, "agentshub": None, "errors": [f"invalid domain: {host}"]}
    domain = host
    base = f"https://{domain}"
    results: dict[str, Any] = {"domain": domain, "mcp": None, "agentshub": None, "errors": []}
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True, max_redirects=3) as client:
        for path in WELL_KNOWN_PATHS:
            url = base + path
            try:
                r = await client.get(url)
                if r.status_code == 200:
                    data = r.json()
                    if path.endswith("mcp.json"):
                        results["mcp"] = data
                    else:
                        results["agentshub"] = data
                else:
                    results["errors"].append(f"{path}: HTTP {r.status_code}")
            except Exception as e:
                results["errors"].append(f"{path}: {e}")
    return results


def normalize_services(manifests: dict[str, Any]) -> list[dict[str, Any]]:
    """Best-effort extraction of service drafts from discovered manifests."""
    drafts: list[dict[str, Any]] = []
    ah = manifests.get("agentshub") or {}
    mcp = manifests.get("mcp") or {}

    # agentshub manifest: { publisher, service, pricing, ... }
    if isinstance(ah, dict) and ah.get("service"):
        s = ah["service"]
        pricing = ah.get("pricing") or {}
        # crude atomic price parse
        price_str = str(pricing.get("amount", "0"))
        try:
            price_atomic = int(float(price_str) * 1_000_000)
        except Exception:
            price_atomic = 0
        drafts.append({
            "name": s.get("name", manifests["domain"]),
            "description": s.get("description", ""),
            "mcp_endpoint": s.get("mcp_endpoint") or s.get("endpoint", ""),
            "version": s.get("version", "1.0.0"),
            "tool_schemas": s.get("tools", []),
            "price_atomic": price_atomic,
            "currency": pricing.get("currency", "USDC"),
            "chain": pricing.get("chain", "base"),
            "manifest": ah,
            "source": "agentshub.json",
        })

    # mcp registry style: { servers: [ { name, description, endpoint, ... } ] }
    servers = None
    if isinstance(mcp, dict):
        servers = mcp.get("servers")
    if isinstance(servers, list):
        for s in servers:
            drafts.append({
                "name": s.get("name", manifests["domain"]),
                "description": s.get("description", ""),
                "mcp_endpoint": s.get("endpoint", ""),
                "version": s.get("version", "1.0.0"),
                "tool_schemas": [],
                "price_atomic": 0,
                "currency": "USDC",
                "chain": "base",
                "manifest": s,
                "source": "mcp.json",
            })
    return drafts
