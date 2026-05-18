"""
Shared helpers for all parsers.
SEC filings are notoriously inconsistent — these helpers absorb the variance.
"""
import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any


def strip_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        # xmltodict wraps text nodes in various ways
        value = value.get("#text") or value.get("value") or value.get("#cdata-section") or ""
    return re.sub(r"\s+", " ", str(value)).strip()


def _unwrap(value: Any) -> str:
    """Unwrap xmltodict nested value patterns: {'value': '...'} or {'#text': '...'}."""
    if value is None:
        return ""
    if isinstance(value, dict):
        for key in ("#text", "value", "#cdata-section"):
            if key in value:
                return str(value[key])
        return ""
    return str(value)


def safe_decimal(value: Any) -> Decimal | None:
    raw = _unwrap(value).replace(",", "").replace("$", "").strip()
    if not raw or raw in ("-", "N/A", ""):
        return None
    try:
        return Decimal(raw)
    except InvalidOperation:
        return None


def safe_int(value: Any) -> int | None:
    d = safe_decimal(value)
    return int(d) if d is not None else None


def safe_date(value: Any) -> datetime | None:
    raw = _unwrap(value).strip() if isinstance(value, dict) else str(value or "").strip()
    if not raw:
        return None
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y%m%d", "%d-%b-%Y"):
        try:
            return datetime.strptime(raw, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def normalize_ticker(raw: str) -> str:
    ticker = re.sub(r"[^A-Z0-9\.]", "", raw.upper().strip())
    return ticker[:10]


def business_days_between(start: datetime, end: datetime) -> int:
    """Approximate business days (Mon–Fri), ignoring holidays."""
    delta = (end.date() - start.date()).days
    if delta <= 0:
        return 0
    full_weeks, remainder = divmod(delta, 7)
    start_dow = start.weekday()
    extra = sum(1 for i in range(remainder) if (start_dow + i) % 7 < 5)
    return full_weeks * 5 + extra
