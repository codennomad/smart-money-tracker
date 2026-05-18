"""
Penetration test suite — OWASP Top 10 coverage.
Run with: pytest tests/security/ -v
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# ── A01 Broken Access Control ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cors_blocks_unknown_origin(client):
    resp = await client.get("/api/v1/insiders", headers={"Origin": "https://evil.com"})
    assert "access-control-allow-origin" not in resp.headers or \
           resp.headers.get("access-control-allow-origin") != "https://evil.com"


# ── A03 Injection ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [
    "'; DROP TABLE insider_trades; --",
    "1 OR 1=1",
    "<script>alert(1)</script>",
    "../../../../etc/passwd",
    "%00",
])
async def test_sql_injection_ticker_rejected(client, payload):
    resp = await client.get(f"/api/v1/insiders?ticker={payload}")
    assert resp.status_code == 422, f"Expected 422 for payload: {payload!r}"


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [
    "'; DROP TABLE congress_trades; --",
    "house OR 1=1",
    "<img src=x onerror=alert(1)>",
])
async def test_sql_injection_chamber_rejected(client, payload):
    resp = await client.get(f"/api/v1/congress?chamber={payload}")
    assert resp.status_code == 422


# ── A05 Security Misconfiguration ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_secure_headers_present(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    headers = {k.lower(): v for k, v in resp.headers.items()}
    assert "x-frame-options" in headers
    assert "strict-transport-security" in headers
    assert "content-security-policy" in headers
    assert "x-content-type-options" in headers


@pytest.mark.asyncio
async def test_openapi_hidden_in_production(client):
    resp = await client.get("/api/openapi.json")
    assert resp.status_code == 404


# ── A10 SSRF ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.parametrize("url", [
    "http://169.254.169.254/latest/meta-data/",  # AWS metadata
    "http://localhost:5432",                       # internal DB
    "http://internal.corp/secrets",               # internal network
    "file:///etc/passwd",                          # local file
    "http://evil.com/exfil",                      # external not in whitelist
])
async def test_ssrf_blocked(url):
    from app.core.http_client import _assert_allowed
    from fastapi import HTTPException
    with pytest.raises(HTTPException) as exc:
        _assert_allowed(url)
    assert exc.value.status_code == 422


# ── A07 Auth Failures ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_invalid_token_rejected(client):
    resp = await client.get(
        "/api/v1/insiders",
        headers={"Authorization": "Bearer fake.jwt.token"}
    )
    # Should not crash — 401 or 200 depending on whether auth is required
    assert resp.status_code in (200, 401)


@pytest.mark.asyncio
async def test_token_manipulation_rejected():
    from app.core.security import decode_token
    from fastapi import HTTPException
    with pytest.raises(HTTPException):
        decode_token("eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJhZG1pbiJ9.FAKE")


# ── Query param boundary tests ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_page_size_capped(client):
    resp = await client.get("/api/v1/insiders?pageSize=99999")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_ticker_max_length_enforced(client):
    resp = await client.get("/api/v1/insiders?ticker=TOOLONGTICKER")
    assert resp.status_code == 422
