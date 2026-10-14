from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.db import get_session
from app.models import Call, Payout, Service, User
from app.services.x402 import developer_share

router = APIRouter(prefix="/payouts", tags=["payouts"])


async def release_due(session: AsyncSession) -> dict:
    now = datetime.now(timezone.utc)
    q = select(Call).where(Call.status == "settled", Call.escrow_release_at <= now)
    res = await session.execute(q)
    calls = res.scalars().all()

    # aggregate by publisher via service
    by_publisher: dict[uuid.UUID, int] = {}
    for c in calls:
        svc = await session.get(Service, c.service_id)
        if svc is None:
            continue
        by_publisher[svc.publisher_id] = by_publisher.get(svc.publisher_id, 0) + developer_share(c.price_atomic)
        c.status = "released"

    payouts_created = 0
    for pid, amt in by_publisher.items():
        if amt <= 0:
            continue
        p = Payout(publisher_id=pid, amount_atomic=amt, status="pending")
        session.add(p)
        payouts_created += 1

    await session.commit()
    return {"released_calls": len(calls), "payouts_created": payouts_created}


@router.post("/release-due")
async def trigger_release(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    return await release_due(session)


@router.get("")
async def list_payouts(limit: int = 50, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(Payout).limit(limit))
    rows = res.scalars().all()
    return [{"id": str(p.id), "publisher_id": str(p.publisher_id),
             "amount_atomic": p.amount_atomic, "status": p.status, "tx_hash": p.tx_hash,
             "created_at": p.created_at.isoformat()} for p in rows]
