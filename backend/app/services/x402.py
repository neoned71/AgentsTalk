from __future__ import annotations

from typing import Optional

import httpx
from datetime import datetime, timedelta, timezone

from app.config import settings


class X402PaymentRequirements:
    def __init__(self, price_atomic: int, currency: str, chain: str, pay_to: str):
        self.price_atomic = price_atomic
        self.currency = currency
        self.chain = chain
        self.pay_to = pay_to

    def to_dict(self) -> dict:
        return {
            "scheme": "exact",
            "network": self.chain,
            "maxAmountRequired": str(self.price_atomic),
            "resource": None,
            "description": "AgentTalk service call",
            "mimeType": "application/json",
            "payTo": self.pay_to,
            "maxTimeoutSeconds": 300,
            "asset": self.currency,
            "extra": {"name": "USDC", "version": "2"},
        }


class X402Client:
    """Adapter around an x402 facilitator (verify + settle)."""

    def __init__(self, facilitator_url: Optional[str] = None):
        self.facilitator_url = (facilitator_url or settings.x402_facilitator_url).rstrip("/")

    async def verify(self, payment_payload: dict, requirements: X402PaymentRequirements) -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                f"{self.facilitator_url}/verify",
                json={"paymentPayload": payment_payload, "paymentRequirements": requirements.to_dict()},
            )
            r.raise_for_status()
            return r.json()

    async def settle(self, payment_payload: dict, requirements: X402PaymentRequirements) -> dict:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                f"{self.facilitator_url}/settle",
                json={"paymentPayload": payment_payload, "paymentRequirements": requirements.to_dict()},
            )
            r.raise_for_status()
            data = r.json()
            if not data.get("success"):
                raise RuntimeError(f"x402 settle failed: {data}")
            return data


def escrow_release_at() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=settings.escrow_hold_days)


def developer_share(price_atomic: int) -> int:
    fee = price_atomic * settings.platform_fee_bps // 10000
    return price_atomic - fee


def platform_fee(price_atomic: int) -> int:
    return price_atomic * settings.platform_fee_bps // 10000
