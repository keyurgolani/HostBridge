"""Admin API endpoints."""

import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Response, Cookie, Depends
from pydantic import BaseModel

from src.config import Config
from src.audit import AuditLogger
from src.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/admin/api", tags=["admin"])

# Simple session storage (in-memory for MVP)
active_sessions: dict[str, datetime] = {}


class LoginRequest(BaseModel):
    """Login request."""
    password: str


class LoginResponse(BaseModel):
    """Login response."""
    token: str


class SystemHealthResponse(BaseModel):
    """System health response."""
    uptime: int
    pending_hitl: int
    tools_executed: int
    error_rate: float


# Dependency to check authentication
async def require_auth(session_token: Optional[str] = Cookie(None)):
    """Require authentication."""
    if not session_token or session_token not in active_sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check if session is expired (24 hours)
    session_time = active_sessions[session_token]
    if datetime.now(timezone.utc) - session_time > timedelta(hours=24):
        del active_sessions[session_token]
        raise HTTPException(status_code=401, detail="Session expired")
    
    return session_token


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, response: Response, config: Config = Depends(lambda: None)):
    """Admin login endpoint."""
    # Get config from global state (will be injected properly)
    from src.main import config as global_config
    
    if request.password != global_config.auth.admin_password:
        logger.warning("failed_login_attempt")
        raise HTTPException(status_code=401, detail="Invalid password")
    
    # Generate session token
    import secrets
    session_token = secrets.token_urlsafe(32)
    active_sessions[session_token] = datetime.now(timezone.utc)
    
    # Set httponly cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=86400,  # 24 hours
    )
    
    logger.info("admin_login_successful")
    
    return LoginResponse(token=session_token)


@router.post("/logout")
async def logout(
    response: Response,
    session_token: str = Depends(require_auth)
):
    """Admin logout endpoint."""
    if session_token in active_sessions:
        del active_sessions[session_token]
    
    response.delete_cookie("session_token")
    logger.info("admin_logout")
    
    return {"message": "Logged out successfully"}


@router.get("/audit")
async def get_audit_logs(
    limit: int = 100,
    session_token: str = Depends(require_auth)
):
    """Get audit logs."""
    from src.main import audit_logger
    
    logs = await audit_logger.get_recent_logs(limit)
    return logs


@router.get("/health", response_model=SystemHealthResponse)
async def get_system_health(session_token: str = Depends(require_auth)):
    """Get system health metrics."""
    from src.main import db, hitl_manager

    # Calculate uptime
    from src.main import app
    start_time = getattr(app.state, 'start_time', time.time())
    uptime = int(time.time() - start_time)

    # Get pending HITL count
    pending_hitl = len(hitl_manager.get_pending_requests())

    # Get total tools executed from audit log
    cursor = await db.connection.execute(
        "SELECT COUNT(*) as count FROM audit_log"
    )
    row = await cursor.fetchone()
    tools_executed = row["count"] if row else 0

    # Calculate error rate
    cursor = await db.connection.execute(
        """
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as errors
        FROM audit_log
        WHERE timestamp > datetime('now', '-1 hour')
        """
    )
    row = await cursor.fetchone()
    total = row["total"] if row and row["total"] else 0
    errors = row["errors"] if row and row["errors"] else 0
    error_rate = errors / total if total > 0 else 0.0

    return SystemHealthResponse(
        uptime=uptime,
        pending_hitl=pending_hitl,
        tools_executed=tools_executed,
        error_rate=error_rate,
    )


# ---------------------------------------------------------------------------
# Secrets management endpoints
# ---------------------------------------------------------------------------

class SecretsInfoResponse(BaseModel):
    """Secrets info response."""
    keys: list[str]
    count: int
    secrets_file: str


@router.get("/secrets", response_model=SecretsInfoResponse)
async def list_secrets(session_token: str = Depends(require_auth)):
    """List configured secret keys (admin view).

    Returns key names only — values are never exposed.
    """
    from src.main import secret_manager

    return SecretsInfoResponse(
        keys=secret_manager.list_keys(),
        count=secret_manager.count(),
        secrets_file=str(secret_manager.secrets_file),
    )


@router.post("/secrets/reload")
async def reload_secrets(session_token: str = Depends(require_auth)):
    """Reload secrets from the secrets file.

    Useful after adding or updating secrets without restarting the server.
    """
    from src.main import secret_manager, workspace_tools

    count = secret_manager.reload()
    logger.info("secrets_reloaded_via_admin", count=count)

    return {
        "message": f"Secrets reloaded successfully. {count} secret(s) loaded.",
        "count": count,
        "secrets_file": str(secret_manager.secrets_file),
    }
