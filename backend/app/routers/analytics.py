from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import AnalyticsEvent


router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.post("/event")
async def track_event(body: dict, session: AsyncSession = Depends(get_session)):
    visitor_id = str(body.get("visitor_id") or "anonymous")[:128]
    path = str(body.get("path") or "/")[:512]
    event = str(body.get("event") or "page_view")[:32]
    duration_ms = int(body.get("duration_ms") or 0)
    if duration_ms < 0 or duration_ms > 1000 * 60 * 60 * 24:
        duration_ms = 0
    referrer = body.get("referrer")
    user_agent = body.get("user_agent")
    ev = AnalyticsEvent(
        visitor_id=visitor_id,
        path=path,
        event=event,
        duration_ms=duration_ms,
        referrer=referrer,
        user_agent=user_agent,
    )
    session.add(ev)
    await session.commit()
    return {"ok": True}


@router.get("/summary")
async def analytics_summary(days: int = 7, session: AsyncSession = Depends(get_session)):
    since = datetime.now(timezone.utc) - timedelta(days=max(1, min(days, 90)))
    q = select(
        AnalyticsEvent.path,
        func.count(AnalyticsEvent.id).label("views"),
        func.count(func.distinct(AnalyticsEvent.visitor_id)).label("visitors"),
        func.coalesce(func.sum(AnalyticsEvent.duration_ms), 0).label("total_duration_ms"),
    ).where(AnalyticsEvent.created_at >= since).group_by(AnalyticsEvent.path).order_by(func.count(AnalyticsEvent.id).desc())
    rows = (await session.execute(q)).all()
    return {
        "period_days": days,
        "pages": [
            {
                "path": row.path,
                "views": row.views,
                "visitors": row.visitors,
                "total_duration_ms": row.total_duration_ms,
                "avg_duration_ms": int(row.total_duration_ms / row.views) if row.views else 0,
            }
            for row in rows
        ],
    }
