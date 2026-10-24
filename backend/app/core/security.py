"""Cryptographic security, JWT join token issuance, and single-use jti verification."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
import uuid
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.core.config import get_settings


class SecurityError(Exception):
    """Base exception for security and authentication failures."""


class TokenValidationError(SecurityError):
    """Token is malformed or invalid."""


class TokenExpiredError(TokenValidationError):
    """Token expiration timestamp has elapsed."""


class TokenReplayError(TokenValidationError):
    """Token jti has already been consumed (single-use invariant)."""


class InvalidSignatureError(TokenValidationError):
    """Token cryptographic signature does not match secret key."""


class TokenPayload(BaseModel):
    """Payload attributes of signed session join token."""

    model_config = ConfigDict(extra="ignore")

    sub: str = Field(description="Participant ID (e.g. agent-4029, cust-812)")
    session_id: str = Field(description="Target session ID")
    role: Literal["customer", "agent", "system"] = Field(description="Participant role")
    exp: int = Field(description="Expiration epoch timestamp (seconds)")
    iat: int = Field(description="Issued at epoch timestamp (seconds)")
    jti: str = Field(description="Unique single-use token ID")


def _b64url_encode(data: bytes) -> str:
    """Encode bytes using base64url format without padding."""
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64url_decode(s: str) -> bytes:
    """Decode base64url formatted string with padding restoration."""
    padding = 4 - (len(s) % 4)
    if padding < 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s.encode("ascii"))


class SecurityManager:
    """Manages session token generation, HMAC-SHA256 signing, and single-use jti tracking."""

    def __init__(self, secret_key: str | None = None, redis_client: Any | None = None) -> None:
        settings = get_settings()
        self.secret_key = (secret_key or settings.SECRET_KEY).encode("utf-8")
        self.default_ttl = settings.JWT_EXPIRATION_SECONDS
        self._redis = redis_client
        # In-memory single-use jti store fallback (jti -> expire_at)
        self._consumed_jtis: dict[str, float] = {}

    def _cleanup_expired_jtis(self) -> None:
        """Purge expired jti entries from in-memory fallback."""
        now = time.time()
        expired = [k for k, exp in self._consumed_jtis.items() if exp <= now]
        for k in expired:
            self._consumed_jtis.pop(k, None)

    def create_join_token(
        self,
        session_id: str,
        participant_id: str,
        role: Literal["customer", "agent", "system"],
        ttl_seconds: int | None = None,
    ) -> str:
        """Create signed compact JWT join token bound to session_id and role with single-use jti."""
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        now = int(time.time())
        exp = now + ttl
        jti = uuid.uuid4().hex

        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "sub": participant_id,
            "session_id": session_id,
            "role": role,
            "exp": exp,
            "iat": now,
            "jti": jti,
        }

        header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
        payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        signing_input = f"{header_b64}.{payload_b64}".encode()

        sig = hmac.new(self.secret_key, signing_input, hashlib.sha256).digest()
        sig_b64 = _b64url_encode(sig)

        return f"{header_b64}.{payload_b64}.{sig_b64}"

    async def verify_join_token(
        self,
        token: str,
        expected_session_id: str | None = None,
        check_single_use: bool = True,
    ) -> TokenPayload:
        """Verify HMAC-SHA256 signature, expiry, session binding, and enforce single-use jti."""
        parts = token.strip().split(".")
        if len(parts) != 3:
            raise TokenValidationError("Token must be a 3-part compact JWT string.")

        header_b64, payload_b64, sig_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}".encode()

        # Verify signature
        expected_sig = hmac.new(self.secret_key, signing_input, hashlib.sha256).digest()
        try:
            actual_sig = _b64url_decode(sig_b64)
        except Exception as e:
            raise TokenValidationError(f"Invalid signature encoding: {e}") from e

        if not hmac.compare_digest(expected_sig, actual_sig):
            raise InvalidSignatureError("HMAC-SHA256 signature mismatch.")

        # Decode payload
        try:
            payload_raw = json.loads(_b64url_decode(payload_b64).decode("utf-8"))
        except Exception as e:
            raise TokenValidationError(f"Malformed token payload: {e}") from e

        payload = TokenPayload.model_validate(payload_raw)

        # Verify expiry
        now = int(time.time())
        if payload.exp < now:
            raise TokenExpiredError(f"Token expired at {payload.exp} (current time: {now}).")

        # Verify session binding if provided
        if expected_session_id and payload.session_id != expected_session_id:
            raise TokenValidationError(
                f"Token session_id '{payload.session_id}' does not match expected '{expected_session_id}'."
            )

        # Single-use jti enforcement
        if check_single_use:
            await self._consume_jti(payload.jti, payload.exp)

        return payload

    async def _consume_jti(self, jti: str, exp: int) -> None:
        """Atomically record jti consumption to block replays."""
        now = time.time()
        ttl_remaining = max(1, int(exp - now))

        if self._redis is not None:
            try:
                key = f"cc:jti:{jti}"
                # Redis SET with NX=True ensures key is only set if it does not already exist
                was_set = await self._redis.set(key, "1", ex=ttl_remaining, nx=True)
                if not was_set:
                    raise TokenReplayError(f"Token jti '{jti}' has already been consumed.")
                return
            except TokenReplayError:
                raise
            except Exception:
                # Fallback to local memory if Redis connection fails
                pass

        # In-memory single-use enforcement
        self._cleanup_expired_jtis()
        if jti in self._consumed_jtis:
            raise TokenReplayError(f"Token jti '{jti}' has already been consumed.")
        self._consumed_jtis[jti] = float(exp)


_default_security_manager: SecurityManager | None = None


def get_security_manager() -> SecurityManager:
    """Return singleton SecurityManager instance."""
    global _default_security_manager
    if _default_security_manager is None:
        _default_security_manager = SecurityManager()
    return _default_security_manager
