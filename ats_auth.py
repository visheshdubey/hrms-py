"""Shared service-to-service auth for Hono → hrms-py calls."""
from __future__ import annotations

import os
from typing import Optional

from fastapi import Header, HTTPException


def require_ats_api_key(
    x_ats_api_key: Optional[str] = Header(default=None, alias="X-ATS-API-Key"),
) -> None:
    """When ATS_API_KEY is set, require matching X-ATS-API-Key header. Open if unset (local)."""
    expected = (os.environ.get("ATS_API_KEY") or "").strip()
    if not expected:
        return
    if not x_ats_api_key or x_ats_api_key.strip() != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing ATS API key")
