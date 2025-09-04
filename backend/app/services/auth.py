import json
from fastapi import HTTPException, Depends, Header
from jose import jwt
import requests
from functools import lru_cache
from typing import Optional
from ..core.config import get_settings

@lru_cache
def _get_jwks(jwks_url: str):
    r = requests.get(jwks_url, timeout=5)
    r.raise_for_status()
    return r.json()

async def get_current_user(authorization: Optional[str] = Header(default=None)) -> dict:
    settings = get_settings()
    if settings.api_auth_bypass:
        return {"sub": "dev-user", "role": "authenticated"}

    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header")

    token = parts[1]
    if not settings.supabase_jwks_url:
        raise HTTPException(status_code=500, detail="Auth not configured")

    jwks = _get_jwks(settings.supabase_jwks_url)
    header = jwt.get_unverified_header(token)
    kid = header.get("kid")
    key = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
    if not key:
        raise HTTPException(status_code=401, detail="Public key not found")

    try:
        payload = jwt.decode(
            token,
            key,
            algorithms=[key.get("alg", "RS256")],
            audience=settings.supabase_jwt_aud,
            options={"verify_aud": True},
        )
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
