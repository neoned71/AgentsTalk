from __future__ import annotations

from typing import Optional

import hashlib
import json
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_user
from app.config import settings
from app.db import get_session
from app.models import Call, Service, User, Receipt, UserBalance, CreditTransaction
from app.schemas import CallRequest
from app.services.x402 import X402Client, X402PaymentRequirements, escrow_release_at, developer_share, platform_fee

router = APIRouter(prefix="/calls", tags=["calls"])


@router.post("/invoke")
async def invoke_service(body: CallRequest, user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)):
    svc = await session.get(Service, uuid.UUID(body.service_id))
    if not svc or not svc.active:
        raise HTTPException(404, "service not found")

    # ---- Credits + receipt branch (web UI) ----
    if getattr(body, "receipt_number", None):
        res = await session.execute(select(Receipt).where(Receipt.receipt_number == body.receipt_number))
        receipt = res.scalar_one_or_none()
        if not receipt or receipt.user_id != user.id or receipt.service_id != svc.id:
            raise HTTPException(400, "invalid receipt")
        if receipt.status != "reserved":
            raise HTTPException(409, f"receipt already {receipt.status}")

        success = bool(getattr(body, "success", True))
        if not success:
            # void receipt -> restore credits
            bal = await session.get(UserBalance, user.id)
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
    requirements = X402PaymentRequirements(
        price_atomic=svc.price_atomic,
        currency=svc.currency,
        chain=svc.chain,
        pay_to=settings.platform_wallet_address or "PLATFORM_WALLET_UNSET",
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
        await x402.verify(payment_payload, requirements)
    except Exception as e:
        raise HTTPException(402, f"payment verification failed: {e}")

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
async def list_calls(service_id: Optional[str] = None, limit: int = 50, session: AsyncSession = Depends(get_session)):
    from sqlalchemy import select

    q = select(Call)
    if service_id:
        q = q.where(Call.service_id == uuid.UUID(service_id))
    q = q.limit(limit)
    res = await session.execute(q)
    rows = res.scalars().all()
    return [{"id": str(c.id), "service_id": str(c.service_id), "agent_id": c.agent_id,
             "price_atomic": c.price_atomic, "status": c.status, "tx_hash": c.tx_hash,
             "created_at": c.created_at.isoformat()} for c in rows]
