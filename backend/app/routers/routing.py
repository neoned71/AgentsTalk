from __future__ import annotations

import asyncio
import time
import uuid

import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.db import get_session
from app.models import Service, User

router = APIRouter(prefix="/routing", tags=["routing"])


async def _probe(endpoint: str) -> tuple[bool, int | None]:
    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            t0 = time.perf_counter()
            try:
                r = await client.head(endpoint)
            except Exception:
                r = await client.get(endpoint)
            dt = int((time.perf_counter() - t0) * 1000)
            # any HTTP response counts as reachable (even 4xx) because endpoint is alive
            return True, dt
    except Exception:
        return False, None


@router.post("/probe")
async def probe(body: dict, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    ids = body.get("service_ids") or []
    q = select(Service).where(Service.active.is_(True))
    if ids:
        try:
            uuids = [uuid.UUID(x) for x in ids]
        except Exception:
            raise HTTPException(400, "invalid service_ids")
        q = q.where(Service.id.in_(uuids))
    res = await session.execute(q)
    svcs = res.scalars().all()

    async def work(svc):
        ok, ms = await _probe(svc.mcp_endpoint)
        svc.last_latency_ms = ms
        svc.last_ping_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc) if ok else svc.last_ping_at
        return {"service_id": str(svc.id), "ok": ok, "latency_ms": ms, "endpoint": svc.mcp_endpoint}

    results = await asyncio.gather(*[work(s) for s in svcs])
    await session.commit()
    # sort: reachable first by latency, then unreachable
    def key(r):
        if not r["ok"] or r["latency_ms"] is None:
            return (1, 10**9)
        return (0, r["latency_ms"])
    results_sorted = sorted(results, key=key)
    return {"results": results_sorted, "best": results_sorted[0]["service_id"] if results_sorted and results_sorted[0]["ok"] else None}
