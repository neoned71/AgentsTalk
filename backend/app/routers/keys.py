from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, make_api_key_value, hash_api_key, prefix_of
from app.db import get_session
from app.models import User, ApiKey

router = APIRouter(prefix="/keys", tags=["keys"])


@router.get("")
async def list_keys(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(ApiKey).where(ApiKey.user_id == user.id))
    rows = res.scalars().all()
    return [{"id": str(k.id), "name": k.name, "prefix": k.key_prefix, "free_only": k.free_only,
             "spend_limit_atomic": k.spend_limit_atomic, "daily_cap_atomic": k.daily_cap_atomic,
             "weekly_cap_atomic": k.weekly_cap_atomic, "monthly_cap_atomic": k.monthly_cap_atomic,
             "spent_atomic": k.spent_atomic, "spent_daily_atomic": k.spent_daily_atomic,
             "spent_weekly_atomic": k.spent_weekly_atomic, "spent_monthly_atomic": k.spent_monthly_atomic,
             "revoked": k.revoked, "created_at": k.created_at.isoformat()} for k in rows]


@router.post("", status_code=201)
async def create_key(body: dict, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    name = body.get("name") or "default"
    free_only = bool(body.get("free_only", False))
    spend_limit = int(body.get("spend_limit_atomic", 0))
    daily_cap = int(body.get("daily_cap_atomic", 0))
    weekly_cap = int(body.get("weekly_cap_atomic", 0))
    monthly_cap = int(body.get("monthly_cap_atomic", 0))
    key = make_api_key_value()
    ak = ApiKey(user_id=user.id, name=name, key_prefix=prefix_of(key),
                key_hash=hash_api_key(key), free_only=free_only,
                spend_limit_atomic=spend_limit, daily_cap_atomic=daily_cap,
                weekly_cap_atomic=weekly_cap, monthly_cap_atomic=monthly_cap)
    session.add(ak)
    await session.commit()
    await session.refresh(ak)
    return {"id": str(ak.id), "name": ak.name, "key": key,
            "note": "Store this key securely; it will not be shown again."}


@router.post("/{key_id}/revoke")
async def revoke_key(key_id: str, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    ak = await session.get(ApiKey, uuid.UUID(key_id))
    if not ak or ak.user_id != user.id:
        raise HTTPException(404, "not found")
    ak.revoked = True
    await session.commit()
    return {"id": key_id, "revoked": True}
