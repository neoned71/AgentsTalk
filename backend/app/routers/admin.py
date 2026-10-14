from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import require_admin
from app.db import get_session
from app.models import User, Publisher, Service, Call, Receipt, UserBalance, AnalyticsEvent

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/overview")
async def admin_overview(user=Depends(require_admin), session: AsyncSession = Depends(get_session)):
    users = (await session.execute(select(func.count(User.id)))).scalar_one()
    publishers = (await session.execute(select(func.count(Publisher.id)))).scalar_one()
    services = (await session.execute(select(func.count(Service.id)))).scalar_one()
    calls = (await session.execute(select(func.count(Call.id)))).scalar_one()
    receipts = (await session.execute(select(func.count(Receipt.id)))).scalar_one()
    reserved_credits = (await session.execute(select(func.coalesce(func.sum(UserBalance.balance_atomic), 0)))).scalar_one()
    total_call_value = (await session.execute(select(func.coalesce(func.sum(Call.price_atomic), 0)))).scalar_one()
    unique_visitors = (await session.execute(select(func.count(func.distinct(AnalyticsEvent.visitor_id))))).scalar_one()
    page_views = (await session.execute(select(func.count(AnalyticsEvent.id)))).scalar_one()
    return {
        "user": {"id": str(user.id), "email": user.email, "role": user.role},
        "totals": {
            "users": users,
            "publishers": publishers,
            "services": services,
            "calls": calls,
            "receipts": receipts,
            "reserved_credits_atomic": int(reserved_credits),
            "total_call_value_atomic": int(total_call_value),
            "unique_visitors": unique_visitors,
            "page_views": page_views,
        },
    }
