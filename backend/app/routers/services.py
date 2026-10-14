from __future__ import annotations

from typing import Optional

import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user, get_current_user_optional
from app.db import get_session
from app.models import Publisher, Service, User
from app.schemas import ServiceCreate, ServiceOut
from app.services.embeddings import get_embedder

router = APIRouter(prefix="/services", tags=["services"])


@router.post("", status_code=201)
async def publish_service(body: dict, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    pub = await session.get(Publisher, uuid.UUID(body.get("publisher_id")))
    if not pub:
        raise HTTPException(404, "publisher not found")
    if pub.user_id and pub.user_id != user.id and user.role != "admin":
        raise HTTPException(403, "not your publisher")
    svc = Service(
        publisher_id=pub.id,
        name=body.get("name"),
        description=body.get("description"),
        version=body.get("version", "1.0.0"),
        mcp_endpoint=body.get("mcp_endpoint"),
        tool_schemas=body.get("tool_schemas", []),
        price_atomic=int(body.get("price_atomic", 0)),
        currency=body.get("currency", "USDC"),
        chain=body.get("chain", "base"),
        manifest=body.get("manifest", {}),
    )
    # embed
    tools = svc.tool_schemas or []
    text_for_embed = f"{svc.name}\n{svc.description}\n" + "\n".join(
        f"{(t or {}).get('name','')}: {(t or {}).get('description','')}" for t in tools
    )
    try:
        embedder = get_embedder()
        svc.embedding = await embedder.embed(text_for_embed)
    except Exception as e:
        # allow publish without embedding; search degrades
        svc.embedding = None

    session.add(svc)
    await session.commit()
    await session.refresh(svc)
    return {"id": str(svc.id), "name": svc.name, "embedding_set": svc.embedding is not None}


@router.get("/{service_id}")
async def get_service(service_id: str, user: User = Depends(get_current_user_optional), session: AsyncSession = Depends(get_session)):
    svc = await session.get(Service, uuid.UUID(service_id))
    if not svc or not svc.active:
        raise HTTPException(404, "not found")
    return {
        "id": str(svc.id),
        "publisher_id": str(svc.publisher_id),
        "name": svc.name,
        "description": svc.description,
        "version": svc.version,
        "mcp_endpoint": svc.mcp_endpoint,
        "tool_schemas": svc.tool_schemas,
        "price_atomic": svc.price_atomic,
        "currency": svc.currency,
        "chain": svc.chain,
        "manifest": svc.manifest,
    }


@router.get("")
async def list_services(limit: int = 50, publisher_id: Optional[str] = None, user: User = Depends(get_current_user_optional), session: AsyncSession = Depends(get_session)):
    q = select(Service).where(Service.active.is_(True))
    if publisher_id:
        q = q.where(Service.publisher_id == uuid.UUID(publisher_id))
    q = q.limit(limit)
    res = await session.execute(q)
    rows = res.scalars().all()
    return [{"id": str(s.id), "name": s.name, "description": s.description,
             "price_atomic": s.price_atomic, "currency": s.currency, "chain": s.chain} for s in rows]
