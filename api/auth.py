"""
api/auth.py — Server-side authentication utilities for TRack-AI.

Provides:
  - Password verification via bcrypt (passlib)
  - JWT creation and validation (python-jose)
  - FastAPI dependency get_current_user() that reads the httpOnly cookie
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from fastapi import Cookie, HTTPException, status
from jose import JWTError, jwt
from dotenv import load_dotenv

load_dotenv()

# ── Configuration (read once at import time) ──────────────────────────────────

SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "480"))

ADMIN_EMAIL: str = os.getenv("ADMIN_EMAIL", "")
ADMIN_PASSWORD_HASH: str = os.getenv("ADMIN_PASSWORD_HASH", "")

if not SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY is not set. Add it to your .env file before starting the server."
    )
if not ADMIN_EMAIL or not ADMIN_PASSWORD_HASH:
    raise RuntimeError(
        "ADMIN_EMAIL and ADMIN_PASSWORD_HASH must be set in .env. "
        "Never store the plaintext password — only the bcrypt hash."
    )

# ── Password hashing ──────────────────────────────────────────────────────────


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if *plain_password* matches *hashed_password* (bcrypt)."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def authenticate_admin(email: str, password: str) -> bool:
    """
    Validate email + password against the single admin account stored in env.

    Performs a constant-time comparison for the email to avoid timing oracle,
    and delegates to bcrypt for the password check.
    """
    import hmac as _hmac

    # Constant-time email compare to prevent user-enumeration timing attacks
    email_match = _hmac.compare_digest(
        email.strip().lower(), ADMIN_EMAIL.strip().lower()
    )
    if not email_match:
        # Still run the bcrypt verify against a dummy hash so timing is uniform
        verify_password(password, ADMIN_PASSWORD_HASH)
        return False

    return verify_password(password, ADMIN_PASSWORD_HASH)


# ── Token creation ────────────────────────────────────────────────────────────

def create_access_token(
    data: dict, expires_delta: Optional[timedelta] = None
) -> str:
    """Return a signed JWT string."""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta if expires_delta else timedelta(minutes=EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ── FastAPI dependency ────────────────────────────────────────────────────────

COOKIE_NAME = "trackai_session"


def get_current_user(
    trackai_session: Optional[str] = Cookie(default=None),
) -> dict:
    """
    FastAPI dependency.  Reads the httpOnly session cookie, validates the JWT,
    and returns the payload dict ({"sub": email, ...}).

    Raises HTTP 401 if the cookie is absent, expired, or tampered with.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if trackai_session is None:
        raise credentials_exception

    try:
        payload = jwt.decode(trackai_session, SECRET_KEY, algorithms=[ALGORITHM])
        subject: Optional[str] = payload.get("sub")
        if subject is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    return {"email": subject}
