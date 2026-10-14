from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.db import get_session
from app.models import User, UserBalance, CreditTransaction

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/balance")
async def balance(user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    bal = await session.get(UserBalance, user.id)
    if not bal:
        bal = UserBalance(user_id=user.id, balance_atomic=0)
        session.add(bal)
        await session.commit()
        await session.refresh(bal)
    return {"balance_atomic": bal.balance_atomic, "currency": bal.currency}


@router.post("/topup")
async def topup(body: dict, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    amt = int(body.get("amount_atomic", 0))
    if amt <= 0:
        raise HTTPException(400, "amount_atomic must be > 0")
    bal = await session.get(UserBalance, user.id)
    if not bal:
        bal = UserBalance(user_id=user.id, balance_atomic=0)
        session.add(bal)
        await session.flush()
    bal.balance_atomic += amt
    session.add(CreditTransaction(user_id=user.id, amount_atomic=amt, kind="topup",
                                 reference=body.get("reference") or "manual"))
    await session.commit()
    return {"balance_atomic": bal.balance_atomic, "currency": bal.currency}
