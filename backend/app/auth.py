from __future__ import annotations

from typing import Optional

import os
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, Request, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_session
from app.models import User, ApiKey
from sqlalchemy import select

import bcrypt

ALG = "HS256"


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(user_id: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_exp_minutes)
    payload = {"sub": user_id, "exp": exp}
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALG)


def decode_token(token: str) -> Optional[str]:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALG])
        return payload.get("sub")
    except JWTError:
        return None


def set_auth_cookie(response, token: str):
    response.set_cookie(
        key="access_token", value=token, httponly=True, samesite="lax",
        max_age=settings.jwt_exp_minutes * 60, secure=bool(settings.secure_cookies), path="/",
    )


def clear_auth_cookie(response):
    response.delete_cookie("access_token", path="/")


def verify_siwe_signature(message: str, signature: str) -> Optional[str]:
    """Returns recovered address (lowercased) or None."""
    try:
        from eth_account import Account
        from eth_account.messages import encode_defunct

        # SIWE messages: verify EIP-191 signed message
        msg = encode_defunct(text=message)
        addr = Account.recover_message(msg, signature=signature)
        return addr.lower() if addr else None
    except Exception:
        return None


async def _user_from_jwt(token: str, session: AsyncSession) -> Optional[User]:
    sub = decode_token(token)
    if not sub:
        return None
    try:
        uid = __import__("uuid").UUID(sub)
    except Exception:
        return None
    user = await session.get(User, uid)
    return user


async def _user_from_api_key(key: str, session: AsyncSession) -> Optional[User]:
    # key format: ak_<prefix>_<secret>
    if not key.startswith("ak_"):
        return None
    prefix = key[:11]  # 'ak_' + 8 chars
    res = await session.execute(select(ApiKey).where(ApiKey.key_prefix == prefix, ApiKey.revoked.is_(False)))
    ak = res.scalar_one_or_none()
    if not ak:
        return None
    # hash check
    import hashlib
    if hashlib.sha256(key.encode()).hexdigest() != ak.key_hash:
        return None
    if ak.spend_limit_atomic and ak.spent_atomic >= ak.spend_limit_atomic:
        return None
    user = await session.get(User, ak.user_id)
    return user


async def get_current_user_optional(request: Request, session: AsyncSession = Depends(get_session)) -> Optional[User]:
    # 1. cookie JWT
    token = request.cookies.get("access_token")
    if token:
        u = await _user_from_jwt(token, session)
        if u:
            return u
    # 2. Authorization: Bearer
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        key = auth[7:].strip()
        # could be JWT or API key
        u = await _user_from_jwt(key, session)
        if u:
            return u
        u = await _user_from_api_key(key, session)
        if u:
            return u
    return None


async def get_current_user(request: Request, session: AsyncSession = Depends(get_session)) -> User:
    u = await get_current_user_optional(request, session)
    if not u:
        raise HTTPException(status_code=401, detail="authentication required")
    return u


def make_api_key_value() -> str:
    secret = secrets.token_urlsafe(24)
    return f"ak_{secret[:8]}_{secret[8:]}"


def hash_api_key(key: str) -> str:
    import hashlib
    return hashlib.sha256(key.encode()).hexdigest()


def prefix_of(key: str) -> str:
    return key[:11]
