from __future__ import annotations

from typing import Optional

import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Service
from app.services.embeddings import get_embedder


PLATFORM_FEE_BPS = None  # set from config at runtime


async def exact_matches(session: AsyncSession, q: str, limit: int) -> list[Service]:
    tokens = [t for t in q.split() if t]
    if not tokens:
        tokens = [q]
    conditions = []
    for t in tokens:
        p = f"%{t}%"
        conditions.append(Service.name.ilike(p))
        conditions.append(Service.description.ilike(p))
    stmt = (
        select(Service)
        .where(Service.active.is_(True))
        .where(or_(*conditions))
        .order_by(Service.created_at.desc())
        .limit(limit)
    )
    res = await session.execute(stmt)
    return list(res.scalars().all())


async def semantic_matches(session: AsyncSession, vec: list[float], limit: int, min_similarity: float) -> list[tuple[Service, float]]:
    # cosine distance; similarity = 1 - distance
    distance = Service.embedding.cosine_distance(vec)
    stmt = (
        select(Service, (1 - distance).label("sim"))
        .where(Service.active.is_(True))
        .where(Service.embedding.is_not(None))
        .order_by(distance)
        .limit(limit * 2)
    )
    res = await session.execute(stmt)
    rows = res.all()
    out = []
    for svc, sim in rows:
        if float(sim) >= min_similarity:
            out.append((svc, float(sim)))
        if len(out) >= limit:
            break
    return out


async def search_services(session: AsyncSession, query: str, limit: int = 20, min_similarity: float = 0.25):
    # stage 1: exact/trgm+tsv
    exact = await exact_matches(session, query, limit)
    exact_ids = {s.id for s in exact}

    # stage 2: embedding (gracefully degrade if embedder unavailable)
    embedder = None
    try:
        embedder = get_embedder()
    except Exception:
        embedder = None

    semantic: list[tuple[Service, float]] = []
    if embedder is not None:
        try:
            vec = await embedder.embed(query)
            semantic = await semantic_matches(session, vec, limit, min_similarity)
        except Exception:
            semantic = []

    merged: list[tuple[Service, Optional[float], str]] = []
    # exact first
    for s in exact:
        merged.append((s, None, "exact"))
    # then similar (not already exact)
    for svc, sim in semantic:
        if svc.id in exact_ids:
            continue
        merged.append((svc, sim, "similar"))
        if len(merged) >= limit:
            break

    # trim
    merged = merged[:limit]

    # attach scores for similar
    result = []
    for svc, sim, kind in merged:
        score = 1.0 if kind == "exact" else (sim or 0.0)
        result.append((svc, score, kind))
    return result
