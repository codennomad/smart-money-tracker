"""
SSRF-hardened HTTP client.
Only domains listed in settings.ALLOWED_EXTERNAL_DOMAINS are reachable.
"""
from urllib.parse import urlparse
import httpx
from fastapi import HTTPException, status
from .config import get_settings

settings = get_settings()

_HEADERS = {
    "User-Agent": f"SmartMoney-Tracker {settings.EDGAR_CONTACT_EMAIL}",
    "Accept": "application/json, application/xml, text/xml",
}


def _assert_allowed(url: str) -> None:
    host = urlparse(url).hostname or ""
    allowed = any(host == d or host.endswith(f".{d}") for d in settings.ALLOWED_EXTERNAL_DOMAINS)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"External domain not in allowlist: {host}",
        )


async def fetch(url: str, **kwargs) -> httpx.Response:
    _assert_allowed(url)
    async with httpx.AsyncClient(
        headers=_HEADERS,
        follow_redirects=True,
        timeout=30.0,
        limits=httpx.Limits(max_connections=20),
    ) as client:
        resp = await client.get(url, **kwargs)
        resp.raise_for_status()
        return resp
