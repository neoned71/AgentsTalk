from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user_optional
from app.db import get_session
from app.models import User
from app.services.search import search_services

router = APIRouter(prefix="/search", tags=["search"])


@router.post("")
async def search(body: dict, user: User = Depends(get_current_user_optional), session: AsyncSession = Depends(get_session)):
    query = body.get("query", "")
    limit = int(body.get("limit", 20))
    min_similarity = float(body.get("min_similarity", 0.25))
    rows = await search_services(session, query, limit, min_similarity)
    out = []
    for svc, score, kind in rows:
        out.append({
            "id": str(svc.id),
            "name": svc.name,
            "description": svc.description,
            "price_atomic": svc.price_atomic,
            "currency": svc.currency,
            "chain": svc.chain,
            "mcp_endpoint": svc.mcp_endpoint,
            "match": kind,
            "score": round(float(score), 4),
        })
    return {"results": out, "count": len(out)}
