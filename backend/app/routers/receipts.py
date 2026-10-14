from __future__ import annotations

import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.db import get_session
from app.models import User, Service, Receipt, UserBalance, CreditTransaction

router = APIRouter(prefix="/receipts", tags=["receipts"])


@router.post("/create")
async def create_receipt(body: dict, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    sid = body.get("service_id")
    if not sid:
        raise HTTPException(400, "service_id required")
    svc = await session.get(Service, uuid.UUID(sid))
    if not svc or not svc.active:
        raise HTTPException(404, "service not found")
    from sqlalchemy import select as _select
    bal = (await session.execute(_select(UserBalance).where(UserBalance.user_id == user.id).with_for_update())).scalar_one_or_none()
    if bal is None:
        bal = UserBalance(user_id=user.id, balance_atomic=0)
        session.add(bal)
        await session.flush()
    if not bal or bal.balance_atomic < svc.price_atomic:
        raise HTTPException(402, "insufficient credits; top up first")

    # reserve
    bal.balance_atomic -= svc.price_atomic
    if bal.balance_atomic < 0:
        raise HTTPException(402, "insufficient credits; top up first")
    number = "rcpt_" + secrets.token_urlsafe(12)
    receipt = Receipt(user_id=user.id, service_id=svc.id, amount_atomic=svc.price_atomic,
                     receipt_number=number, status="reserved")
    session.add(receipt)
    session.add(CreditTransaction(user_id=user.id, amount_atomic=-svc.price_atomic, kind="debit",
                                 reference=f"reserve:{number}"))
    await session.commit()
    await session.refresh(receipt)
    return {"receipt_number": number, "amount_atomic": svc.price_atomic,
            "currency": svc.currency, "status": "reserved",
            "note": "Use receipt_number in /calls/invoke; failure voids and restores credits."}


@router.get("")
async def list_receipts(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(Receipt).where(Receipt.user_id == user.id).order_by(Receipt.created_at.desc()))
    rows = res.scalars().all()
    return [{"receipt_number": r.receipt_number, "service_id": str(r.service_id), "amount_atomic": r.amount_atomic,
             "status": r.status, "created_at": r.created_at.isoformat()} for r in rows]


@router.get("/{receipt_number}")
async def get_receipt(receipt_number: str, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(Receipt).where(Receipt.receipt_number == receipt_number))
    r = res.scalar_one_or_none()
    if not r or r.user_id != user.id:
        raise HTTPException(404, "not found")
    return {"receipt_number": r.receipt_number, "service_id": str(r.service_id),
            "amount_atomic": r.amount_atomic, "status": r.status,
            "created_at": r.created_at.isoformat(),
            "consumed_at": r.consumed_at.isoformat() if r.consumed_at else None,
            "voided_at": r.voided_at.isoformat() if r.voided_at else None}
