from __future__ import annotations

from typing import Optional

import hashlib
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select, or_
from app.auth import get_current_user
from app.config import settings
from app.db import get_session
from app.models import Call, Service, User, Receipt, UserBalance, CreditTransaction, ApiKey
from app.schemas import CallRequest
from app.services.x402 import X402Client, X402PaymentRequirements, escrow_release_at, developer_share, platform_fee



from datetime import datetime, timezone, timedelta


async def _resolve_api_key(request: Request, session) -> Optional[ApiKey]:
    auth = request.headers.get("authorization", "")
    if not auth.lower().startswith("bearer "):
        return None
    key = auth[7:].strip()
    if not key.startswith("ak_"):
        return None
    prefix = key[:11]
    res = await session.execute(select(ApiKey).where(ApiKey.key_prefix == prefix, ApiKey.revoked.is_(False)))
    ak = res.scalar_one_or_none()
    if ak is None or __import__("hashlib").sha256(key.encode()).hexdigest() != ak.key_hash:
        return None
    return ak


def _period_now():
    return datetime.now(timezone.utc)


def _reset_api_key_periods(ak: ApiKey) -> None:
    now = _period_now()
    if not ak.spent_reset_daily_at or now >= ak.spent_reset_daily_at:
        ak.spent_daily_atomic = 0
        ak.spent_reset_daily_at = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
    if not ak.spent_reset_weekly_at or now >= ak.spent_reset_weekly_at:
        ak.spent_weekly_atomic = 0
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        while start.weekday() != 0:
            start -= timedelta(days=1)
        ak.spent_reset_weekly_at = start + timedelta(days=7)
    if not ak.spent_reset_monthly_at or now >= ak.spent_reset_monthly_at:
        ak.spent_monthly_atomic = 0
        if now.month == 12:
            ak.spent_reset_monthly_at = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            ak.spent_reset_monthly_at = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)


async def _budget_charge_api_key(request: Request, session, amount: int, service: Optional[Service] = None) -> None:
    ak = await _resolve_api_key(request, session)
    if ak is None:
        return
    if service is not None and ak.free_only and (service.price_atomic or 0) > 0:
        raise HTTPException(402, "API key is restricted to free services")
    _reset_api_key_periods(ak)
    if ak.spend_limit_atomic and (ak.spent_atomic or 0) + amount > ak.spend_limit_atomic:
        raise HTTPException(402, "API key lifetime spend limit exceeded")
    if ak.daily_cap_atomic and (ak.spent_daily_atomic or 0) + amount > ak.daily_cap_atomic:
        raise HTTPException(402, "API key daily budget exceeded")
    if ak.weekly_cap_atomic and (ak.spent_weekly_atomic or 0) + amount > ak.weekly_cap_atomic:
        raise HTTPException(402, "API key weekly budget exceeded")
    if ak.monthly_cap_atomic and (ak.spent_monthly_atomic or 0) + amount > ak.monthly_cap_atomic:
        raise HTTPException(402, "API key monthly budget exceeded")
    ak.spent_atomic = (ak.spent_atomic or 0) + amount
    ak.spent_daily_atomic = (ak.spent_daily_atomic or 0) + amount
    ak.spent_weekly_atomic = (ak.spent_weekly_atomic or 0) + amount
    ak.spent_monthly_atomic = (ak.spent_monthly_atomic or 0) + amount

router = APIRouter(prefix="/calls", tags=["calls"])


@router.post("/invoke")
async def invoke_service(request: Request, body: CallRequest, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    svc = await session.get(Service, uuid.UUID(body.service_id))
    if not svc or not svc.active:
        raise HTTPException(404, "service not found")

    api_key = await _resolve_api_key(request, session)
    if api_key is not None and api_key.free_only and (svc.price_atomic or 0) > 0:
        raise HTTPException(402, "API key is restricted to free services")

    # ---- Credits + receipt branch (web UI) ----
    if getattr(body, "receipt_number", None):
        res = await session.execute(select(Receipt).where(Receipt.receipt_number == body.receipt_number).with_for_update())
        receipt = res.scalar_one_or_none()
        if not receipt or receipt.user_id != user.id or receipt.service_id != svc.id:
            raise HTTPException(400, "invalid receipt")
        if receipt.status != "reserved":
            raise HTTPException(409, f"receipt already {receipt.status}")

        success = bool(getattr(body, "success", True))
        if not success:
            # void receipt -> restore credits
            bal = await session.execute(select(UserBalance).where(UserBalance.user_id == user.id).with_for_update())
            bal = bal.scalar_one_or_none()
            if bal:
                bal.balance_atomic += receipt.amount_atomic
            session.add(CreditTransaction(user_id=user.id, amount_atomic=receipt.amount_atomic,
                                         kind="void", reference=receipt.receipt_number))
            receipt.status = "voided"
            receipt.voided_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
            await session.commit()
            return {
                "call_id": None,
                "status": "voided",
                "receipt_number": receipt.receipt_number,
                "receipt_consumed": False,
                "mcp_endpoint": svc.mcp_endpoint,
                "note": "receipt voided; credits restored.",
            }

        # consume receipt
        receipt.status = "consumed"
        receipt.consumed_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
        req_hash = hashlib.sha256(json.dumps(body.request_payload, sort_keys=True).encode()).hexdigest()
        call = Call(
            service_id=svc.id,
            agent_id=body.agent_id or str(user.id),
            request_hash=req_hash,
            price_atomic=svc.price_atomic,
            tx_hash=f"credit:{receipt.receipt_number}",
            status="settled",
            escrow_release_at=escrow_release_at(),
        )
        session.add(call)
        # platform holds developer share in escrow (already collected from user credits on reservation)
        session.add(CreditTransaction(user_id=user.id, amount_atomic=0, kind="debit",
                                     reference=receipt.id and f"consume:{receipt.receipt_number}"))
        await _budget_charge_api_key(request, session, svc.price_atomic, svc)
        await session.commit()
        await session.refresh(call)
        return {
            "call_id": str(call.id),
            "status": "settled",
            "receipt_number": receipt.receipt_number,
            "receipt_consumed": True,
            "mcp_endpoint": svc.mcp_endpoint,
            "escrow_release_at": call.escrow_release_at.isoformat(),
            "platform_fee_atomic": platform_fee(svc.price_atomic),
            "developer_share_atomic": developer_share(svc.price_atomic),
            "note": "receipt consumed; 98% held in escrow 30d for cashback.",
        }

    # ---- x402 crypto branch (agents / wallet direct) ----
    if not settings.platform_wallet_address:
        raise HTTPException(503, "platform wallet not configured")
    requirements = X402PaymentRequirements(
        price_atomic=svc.price_atomic,
        currency=svc.currency,
        chain=svc.chain,
        pay_to=settings.platform_wallet_address,
    )
    x402 = X402Client()

    # No payment supplied -> 402 challenge
    if not body.payment_tx and not body.request_payload.get("_payment_payload"):
        return JSONResponse(
            status_code=402,
            content={
                "error": "payment required",
                "paymentRequirements": requirements.to_dict(),
                "service_id": str(svc.id),
                "price_atomic": svc.price_atomic,
                "currency": svc.currency,
                "chain": svc.chain,
            },
        )

    payment_payload = body.request_payload.get("_payment_payload") or {"txHash": body.payment_tx}

    try:
        vr = await x402.verify(payment_payload, requirements)
    except Exception as e:
        raise HTTPException(402, f"payment verification failed: {e}")
    if isinstance(vr, dict) and vr.get("isValid") is False:
        raise HTTPException(402, "payment verification failed: facilitator reports invalid payment")

    try:
        settle = await x402.settle(payment_payload, requirements)
    except Exception as e:
        raise HTTPException(402, f"payment settlement failed: {e}")

    tx_hash = settle.get("transactionHash") or settle.get("txHash") or (body.payment_tx or "")

    req_hash = hashlib.sha256(json.dumps(body.request_payload, sort_keys=True).encode()).hexdigest()
    call = Call(
        service_id=svc.id,
        agent_id=body.agent_id,
        request_hash=req_hash,
        price_atomic=svc.price_atomic,
        tx_hash=tx_hash,
        status="settled",
        escrow_release_at=escrow_release_at(),
    )
    session.add(call)
    await _budget_charge_api_key(request, session, svc.price_atomic, svc)
    await session.commit()
    await session.refresh(call)

    return {
        "call_id": str(call.id),
        "status": "settled",
        "receipt_consumed": None,
        "mcp_endpoint": svc.mcp_endpoint,
        "tx_hash": tx_hash,
        "escrow_release_at": call.escrow_release_at.isoformat(),
        "platform_fee_atomic": platform_fee(svc.price_atomic),
        "developer_share_atomic": developer_share(svc.price_atomic),
        "note": "98% held in escrow for 30 days for cashback guarantee; released after window.",
    }


@router.post("/{call_id}/refund")
async def refund_call(call_id: str, session: AsyncSession = Depends(get_session)):
    call = await session.get(Call, uuid.UUID(call_id))
    if not call:
        raise HTTPException(404, "not found")
    if call.status == "released":
        raise HTTPException(409, "already released to developer; refund via dispute")
    call.status = "refunded"
    await session.commit()
    return {"call_id": call_id, "status": "refunded"}


@router.get("")
async def list_calls(
    service_id: Optional[str] = None,
    limit: int = 50,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    from sqlalchemy import select

    from app.models import Publisher, Service

    limit = min(max(limit, 1), 200)
    q = select(Call)
    if service_id:
        q = q.where(Call.service_id == uuid.UUID(service_id))
    if user.role != "admin":
        publisher_ids = select(Publisher.id).where(Publisher.user_id == user.id)
        service_ids = select(Service.id).where(Service.publisher_id.in_(publisher_ids))
        q = q.where(or_(Call.agent_id == str(user.id), Call.service_id.in_(service_ids)))
    q = q.order_by(Call.created_at.desc()).limit(limit)
    res = await session.execute(q)
    rows = res.scalars().all()
    return [{"id": str(c.id), "service_id": str(c.service_id), "agent_id": c.agent_id,
             "price_atomic": c.price_atomic, "status": c.status, "tx_hash": c.tx_hash,
             "created_at": c.created_at.isoformat()} for c in rows]
