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
    return [{"id": str(k.id), "name": k.name, "prefix": k.key_prefix, "spend_limit_atomic": k.spend_limit_atomic,
             "spent_atomic": k.spent_atomic, "revoked": k.revoked, "created_at": k.created_at.isoformat()} for k in rows]


@router.post("", status_code=201)
async def create_key(body: dict, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    name = body.get("name") or "default"
    spend_limit = int(body.get("spend_limit_atomic", 0))
    key = make_api_key_value()
    ak = ApiKey(user_id=user.id, name=name, key_prefix=prefix_of(key),
                key_hash=hash_api_key(key), spend_limit_atomic=spend_limit)
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
