"""
Congressional STOCK Act disclosures parser.

Sources:
  House:  https://disclosures.house.gov/public_disc/financial-pdfs/{year}FD.zip
          XML inside ZIP → <Member_Financial_Disclosure_Filing>
  Senate: https://efts.senate.gov/LATEST/search-index?type=ptr&filerType=senator
          Returns JSON with PDF links (harder — PDFs need OCR or regex extraction)

We parse the House XML (structured) and do best-effort Senate JSON.
"""
import re
import zipfile
import io
from datetime import datetime, timezone
from typing import Any

import xmltodict

from app.parsers.base import strip_text, safe_decimal, safe_date, business_days_between


# Amount range brackets as published by the House
_AMOUNT_BRACKETS: list[tuple[str, int, int]] = [
    ("$1,001 - $15,000",        1_001,     15_000),
    ("$15,001 - $50,000",      15_001,     50_000),
    ("$50,001 - $100,000",     50_001,    100_000),
    ("$100,001 - $250,000",   100_001,    250_000),
    ("$250,001 - $500,000",   250_001,    500_000),
    ("$500,001 - $1,000,000", 500_001,  1_000_000),
    ("$1,000,001 - $5,000,000", 1_000_001, 5_000_000),
    ("Over $5,000,000",       5_000_001, 25_000_000),
]


def parse_amount_bracket(raw: str) -> tuple[int, int]:
    """Return (min, max) from a bracket string like '$15,001 - $50,000'."""
    normalized = raw.strip()
    for label, lo, hi in _AMOUNT_BRACKETS:
        if normalized.lower() == label.lower():
            return lo, hi
    # Fallback: try to extract numbers
    nums = re.findall(r"[\d,]+", normalized.replace("$", ""))
    cleaned = [int(n.replace(",", "")) for n in nums if n]
    if len(cleaned) >= 2:
        return cleaned[0], cleaned[1]
    if len(cleaned) == 1:
        return cleaned[0], cleaned[0]
    return 0, 0


def parse_house_xml(xml_bytes: bytes) -> list[dict[str, Any]]:
    """
    Parse House financial disclosure XML.
    One XML file covers all members for a given year.
    """
    try:
        doc = xmltodict.parse(xml_bytes, force_list=("Transaction",))
    except Exception as exc:
        raise ValueError(f"Failed to parse House XML: {exc}") from exc

    members = []
    filing_root = doc.get("FinancialDisclosure") or doc.get("Member_Financial_Disclosure_Filing") or {}
    transactions_root = filing_root.get("Transactions") or {}
    raw_txns = transactions_root.get("Transaction") or []

    for txn in raw_txns:
        member_name = strip_text(txn.get("MemberLastName", "")) + ", " + strip_text(txn.get("MemberFirstName", ""))
        member_name = member_name.strip(", ")
        party = strip_text(txn.get("Party", ""))[:1].upper()
        district = strip_text(txn.get("District", ""))
        ticker = strip_text(txn.get("Ticker", "")).upper()
        asset_name = strip_text(txn.get("Asset", ""))
        txn_type_raw = strip_text(txn.get("Type", "")).lower()
        amount_raw = strip_text(txn.get("Amount", ""))
        txn_date = safe_date(txn.get("TransactionDate"))
        filed_date = safe_date(txn.get("FilingDate"))

        if not ticker or ticker in ("N/A", "--", ""):
            continue

        if "purchase" in txn_type_raw or "buy" in txn_type_raw:
            transaction_type = "buy"
        elif "sale" in txn_type_raw or "sell" in txn_type_raw:
            transaction_type = "sell"
        else:
            continue  # skip exchanges, gifts, etc.

        amount_min, amount_max = parse_amount_bracket(amount_raw)
        days_to_disclose = 0
        if txn_date and filed_date:
            days_to_disclose = business_days_between(txn_date, filed_date)

        members.append({
            "member": member_name,
            "party": party or "I",
            "chamber": "house",
            "ticker": ticker,
            "company": asset_name,
            "transaction_type": transaction_type,
            "amount_min": amount_min,
            "amount_max": amount_max,
            "transaction_date": txn_date or datetime.now(timezone.utc),
            "disclosed_at": filed_date or datetime.now(timezone.utc),
            "days_to_disclose": days_to_disclose,
        })

    return members


def parse_house_zip(zip_bytes: bytes) -> list[dict[str, Any]]:
    """Extract and parse the XML inside the House annual ZIP file."""
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        xml_files = [n for n in zf.namelist() if n.endswith(".xml")]
        if not xml_files:
            raise ValueError("No XML found in House disclosure ZIP")
        xml_bytes = zf.read(xml_files[0])
    return parse_house_xml(xml_bytes)


def parse_senate_ptr_json(json_data: dict) -> list[dict[str, Any]]:
    """
    Parse Senate periodic transaction report search results.
    Senate JSON is less structured — best effort extraction.
    """
    trades = []
    hits = json_data.get("hits", {}).get("hits", [])

    for hit in hits:
        source = hit.get("_source", {})
        first = strip_text(source.get("first_name", ""))
        last = strip_text(source.get("last_name", ""))
        member_name = f"{first} {last}".strip()
        party = strip_text(source.get("party", ""))[:1].upper()
        ticker = strip_text(source.get("ticker", "")).upper()
        asset = strip_text(source.get("asset_description", ""))
        txn_type_raw = strip_text(source.get("transaction_date", "")).lower()
        amount_raw = strip_text(source.get("amount", ""))
        txn_date = safe_date(source.get("transaction_date"))
        filed_date = safe_date(source.get("date_received"))

        if not ticker or not member_name:
            continue

        txn_type_raw2 = strip_text(source.get("type", "")).lower()
        if "purchase" in txn_type_raw2:
            transaction_type = "buy"
        elif "sale" in txn_type_raw2:
            transaction_type = "sell"
        else:
            continue

        amount_min, amount_max = parse_amount_bracket(amount_raw)
        days = business_days_between(txn_date, filed_date) if txn_date and filed_date else 0

        trades.append({
            "member": member_name,
            "party": party or "I",
            "chamber": "senate",
            "ticker": ticker,
            "company": asset,
            "transaction_type": transaction_type,
            "amount_min": amount_min,
            "amount_max": amount_max,
            "transaction_date": txn_date or datetime.now(timezone.utc),
            "disclosed_at": filed_date or datetime.now(timezone.utc),
            "days_to_disclose": days,
        })

    return trades
