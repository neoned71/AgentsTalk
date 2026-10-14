from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (create_access_token, hash_password, verify_password, set_auth_cookie,
                      clear_auth_cookie, verify_siwe_signature, get_current_user, get_current_user_optional)
from app.db import get_session
from app.models import User, ApiKey



from collections import defaultdict
from time import time as _now
_rate_buckets: dict[str, list[float]] = defaultdict(list)
def _rate_limit(key: str, limit: int, window: int = 60):
    now = _now()
    b = _rate_buckets[key]
    while b and b[0] < now - window:
        b.pop(0)
    if len(b) >= limit:
        from fastapi import HTTPException
        raise HTTPException(429, "too many requests")
    b.append(now)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201)
async def register(request: Request, body: dict, response: Response, session: AsyncSession = Depends(get_session)):
    _rate_limit(f"register:{request.client.host}", 10)
    email = body.get("email")
    password = body.get("password")
    display_name = body.get("display_name") or email
    if not email or not password:
        raise HTTPException(400, "email and password required")
    existing = await session.execute(select(User).where(User.email == email))
    if existing.scalar_one_or_none():
        raise HTTPException(409, "email already registered")
    user = User(email=email, password_hash=hash_password(password), display_name=display_name)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    token = create_access_token(str(user.id))
    set_auth_cookie(response, token)
    return {"id": str(user.id), "email": user.email, "display_name": user.display_name, "role": user.role}


@router.post("/login")
async def login(request: Request, body: dict, response: Response, session: AsyncSession = Depends(get_session)):
    _rate_limit(f"login:{request.client.host}", 10)
    email = body.get("email")
    password = body.get("password")
    if not email or not password:
        raise HTTPException(400, "email and password required")
    res = await session.execute(select(User).where(User.email == email))
    user = res.scalar_one_or_none()
    if not user or not user.password_hash or not verify_password(password, user.password_hash):
        raise HTTPException(401, "invalid credentials")
    token = create_access_token(str(user.id))
    set_auth_cookie(response, token)
    return {"id": str(user.id), "email": user.email, "display_name": user.display_name, "role": user.role, "wallet_address": user.wallet_address}


@router.post("/logout")
async def logout(response: Response):
    clear_auth_cookie(response)
    return {"ok": True}


@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    return {"id": str(user.id), "email": user.email, "display_name": user.display_name,
            "role": user.role, "wallet_address": user.wallet_address}


@router.post("/wallet/challenge")
async def wallet_challenge(body: dict, request: Request, response: Response):
    _rate_limit(f"challenge:{request.client.host}", 20)
    address = (body.get("address") or "").lower()
    if not address:
        raise HTTPException(400, "address required")
    from datetime import datetime, timezone, timedelta
    nonce = str(uuid.uuid4())
    expires = datetime.now(timezone.utc) + timedelta(minutes=5)
    message = (
        "AgentTalk wants you to sign in with your wallet.\n\n"
        f"Address: {address}\n"
        f"Nonce: {nonce}\n"
        "Domain: agentshub.local\n"
        f"Issued At: {datetime.now(timezone.utc).isoformat()}\n"
        f"Expires At: {expires.isoformat()}\n"
        "Statement: Sign in to AgentTalk."
    )
    response.set_cookie("siwe_nonce", nonce, httponly=True, samesite="lax", max_age=300, path="/")
    response.set_cookie("siwe_address", address, httponly=True, samesite="lax", max_age=300, path="/")
    response.set_cookie("siwe_expires", str(int(expires.timestamp())), httponly=True, samesite="lax", max_age=300, path="/")
    return {"message": message, "nonce": nonce}


@router.post("/wallet/verify")
async def wallet_verify(body: dict, request: Request, response: Response, session: AsyncSession = Depends(get_session)):
    address = (body.get("address") or "").lower()
    signature = body.get("signature")
    message = body.get("message")
    nonce = request.cookies.get("siwe_nonce")
    addr_cookie = request.cookies.get("siwe_address")
    expires_cookie = request.cookies.get("siwe_expires")
    if not address or not signature or not message or not nonce or addr_cookie != address or not expires_cookie:
        raise HTTPException(400, "invalid challenge state")
    try:
        if int(expires_cookie) < int(datetime.now(timezone.utc).timestamp()):
            raise HTTPException(400, "challenge expired")
    except Exception:
        raise HTTPException(400, "invalid expiry")
    if nonce not in message or "agentshub.local" not in message:
        raise HTTPException(400, "nonce mismatch")
    recovered = verify_siwe_signature(message, signature)
    if recovered != address:
        raise HTTPException(401, "signature verification failed")

    # find or create user
    res = await session.execute(select(User).where(User.wallet_address == address))
    user = res.scalar_one_or_none()
    if not user:
        user = User(wallet_address=address, display_name=address[:8], role="consumer")
        session.add(user)
        await session.commit()
        await session.refresh(user)

    token = create_access_token(str(user.id))
    set_auth_cookie(response, token)
    clear_siwe = True
    if clear_siwe:
        response.delete_cookie("siwe_nonce", path="/")
        response.delete_cookie("siwe_address", path="/")
        response.delete_cookie("siwe_expires", path="/")
    return {"id": str(user.id), "wallet_address": user.wallet_address, "role": user.role}


@router.post("/pairing/redeem")
async def redeem_pairing(body: dict, session: AsyncSession = Depends(get_session)):
    # Agents redeem a short-lived pairing code (created in dashboard) for an API key.
    code = body.get("code")
    if not code:
        raise HTTPException(400, "code required")
    # Pairing codes stored in a simple pairing_codes table? For MVP, reuse ApiKey? 
    # We'll implement a lightweight in-memory-ish via a dedicated table. For now 501.
    raise HTTPException(501, "pairing not implemented; use /settings/keys")
