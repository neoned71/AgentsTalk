from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, get_current_user_optional
from app.db import get_session
from app.models import Publisher, User
from app.services.wellknown import fetch_manifests, normalize_services

router = APIRouter(prefix="/publishers", tags=["publishers"])


@router.post("", status_code=201)
async def create_publisher(body: dict, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    domain = body.get("domain")
    wallet = body.get("wallet_address")
    display_name = body.get("display_name") or domain
    if not domain or not wallet:
        raise HTTPException(400, "domain and wallet_address required")
    existing = await session.execute(select(Publisher).where(Publisher.domain == domain))
    if existing.scalar_one_or_none():
        raise HTTPException(409, "publisher domain already exists")
    p = Publisher(user_id=user.id, domain=domain, wallet_address=wallet, display_name=display_name)
    session.add(p)
    await session.commit()
    await session.refresh(p)
    return {"id": str(p.id), "domain": p.domain, "verified": p.verified}


@router.get("/mine")
async def my_publishers(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    q = select(Publisher)
    if user.role != "admin":
        q = q.where(Publisher.user_id == user.id)
    res = await session.execute(q)
    rows = res.scalars().all()
    return [{"id": str(p.id), "domain": p.domain, "display_name": p.display_name, "verified": p.verified,
             "wallet_address": p.wallet_address} for p in rows]


@router.get("/{publisher_id}")
async def get_publisher(publisher_id: str,
                        caller: Optional[User] = Depends(get_current_user_optional),
                        session: AsyncSession = Depends(get_session)):
    p = await session.get(Publisher, uuid.UUID(publisher_id))
    if not p:
        raise HTTPException(404, "not found")
    expose_wallet = (caller is not None and (caller.role == "admin" or caller.id == p.user_id))
    return {
        "id": str(p.id),
        "domain": p.domain,
        "display_name": p.display_name,
        "verified": p.verified,
        "wallet_address": p.wallet_address if expose_wallet else None,
    }


@router.post("/import-domain")
async def import_domain(body: dict, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    domain = body.get("domain")
    wallet = body.get("wallet_address")
    if not domain:
        raise HTTPException(400, "domain required")
    manifests = await fetch_manifests(domain)
    drafts = normalize_services(manifests)

    # create or reuse publisher; mark verified only if at least one manifest was fetched
    verified = manifests.get("mcp") is not None or manifests.get("agentshub") is not None

    existing = await session.execute(select(Publisher).where(Publisher.domain == domain))
    pub = existing.scalar_one_or_none()
    if not pub:
        if not wallet:
            raise HTTPException(400, "wallet_address required for new publisher")
        pub = Publisher(user_id=user.id, domain=domain, wallet_address=wallet, display_name=domain, verified=verified)
        session.add(pub)
    else:
        pub.verified = pub.verified or verified
    await session.commit()
    await session.refresh(pub)

    return {
        "publisher_id": str(pub.id),
        "domain": pub.domain,
        "verified": pub.verified,
        "manifests": manifests,
        "service_drafts": drafts,
        "note": "Review drafts; publish via POST /services with chosen fields. Prices may need adjusting.",
    }
