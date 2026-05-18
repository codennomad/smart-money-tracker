"""
SEC EDGAR Form 4 parser.

Form 4 = insider trades (officers, directors, >10% owners).
Must be filed within 2 business days of the transaction.

XML structure reference:
  https://www.sec.gov/Archives/edgar/data/{cik}/{accession}-index.htm
  Root element: <ownershipDocument>
    <issuer>
    <reportingOwner>
    <nonDerivativeTable> → <nonDerivativeTransaction>
    <derivativeTable>    → <derivativeTransaction>
"""
import re
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

import xmltodict

from app.parsers.base import safe_decimal, safe_int, safe_date, strip_text


# Maps SEC transaction codes to our domain model
_TRANSACTION_CODE_MAP = {
    "P": "buy",    # open market purchase
    "S": "sell",   # open market sale
    "A": "buy",    # grant / award
    "D": "sell",   # disposition to issuer
    "G": "buy",    # gift (incoming)
    "F": "sell",   # payment of exercise price
    "M": "buy",    # exercise of derivative
    "X": "buy",    # exercise of in-the-money derivative
    "C": "buy",    # conversion of derivative
    "E": "sell",   # expiration of short derivative
    "H": "sell",   # expiration of long derivative
}


def parse_form4(xml_bytes: bytes, form_url: str = "") -> list[dict[str, Any]]:
    """
    Parse raw Form 4 XML bytes.
    Returns a list of trade dicts ready for DB insertion.
    One XML may contain multiple transactions.
    """
    try:
        doc = xmltodict.parse(xml_bytes, force_list=("nonDerivativeTransaction", "derivativeTransaction"))
    except Exception as exc:
        raise ValueError(f"Failed to parse Form 4 XML: {exc}") from exc

    root = doc.get("ownershipDocument", {})
    issuer = root.get("issuer", {})
    owner = root.get("reportingOwner", {})

    ticker = strip_text(issuer.get("issuerTradingSymbol", ""))
    company = strip_text(issuer.get("issuerName", ""))

    owner_info = owner.get("reportingOwnerId", {}) if isinstance(owner, dict) else {}
    rel_info = owner.get("reportingOwnerRelationship", {}) if isinstance(owner, dict) else {}

    insider_name = strip_text(owner_info.get("rptOwnerName", "Unknown"))
    insider_title = _extract_title(rel_info)

    trades: list[dict[str, Any]] = []

    # Non-derivative transactions (common stock buys/sells)
    for txn in root.get("nonDerivativeTable", {}).get("nonDerivativeTransaction") or []:
        trade = _parse_non_derivative(txn, ticker, company, insider_name, insider_title, form_url)
        if trade:
            trades.append(trade)

    # Derivative transactions (options, warrants, convertibles)
    for txn in root.get("derivativeTable", {}).get("derivativeTransaction") or []:
        trade = _parse_derivative(txn, ticker, company, insider_name, insider_title, form_url)
        if trade:
            trades.append(trade)

    return trades


def _extract_title(rel: dict) -> str:
    parts = []
    if rel.get("isDirector") == "1":
        parts.append("Director")
    if rel.get("isOfficer") == "1":
        title = strip_text(rel.get("officerTitle", "Officer"))
        parts.append(title)
    if rel.get("isTenPercentOwner") == "1":
        parts.append("10% Owner")
    return ", ".join(parts) or "Insider"


def _parse_non_derivative(
    txn: dict, ticker: str, company: str,
    insider_name: str, insider_title: str, form_url: str
) -> dict | None:
    code = strip_text(
        txn.get("transactionCoding", {}).get("transactionCode", "")
    )
    transaction_type = _TRANSACTION_CODE_MAP.get(code)
    if not transaction_type or not ticker:
        return None

    amounts = txn.get("transactionAmounts", {})
    shares = safe_decimal(amounts.get("transactionShares", {}).get("#text") or
                          amounts.get("transactionShares"))
    price = safe_decimal(amounts.get("transactionPricePerShare", {}).get("#text") or
                         amounts.get("transactionPricePerShare"))
    txn_date = safe_date(txn.get("transactionDate", {}).get("value") or
                         txn.get("transactionDate"))

    if shares is None or shares <= 0:
        return None

    total_value = float(shares * (price or Decimal("0")))

    return {
        "ticker": ticker.upper(),
        "company": company,
        "insider_name": insider_name,
        "insider_title": insider_title,
        "transaction_type": transaction_type,
        "shares": int(shares),
        "price_per_share": float(price or 0),
        "total_value": total_value,
        "transaction_date": txn_date or datetime.now(timezone.utc),
        "source": "form4",
        "form_url": form_url,
    }


def _parse_derivative(
    txn: dict, ticker: str, company: str,
    insider_name: str, insider_title: str, form_url: str
) -> dict | None:
    code = strip_text(
        txn.get("transactionCoding", {}).get("transactionCode", "")
    )
    transaction_type = _TRANSACTION_CODE_MAP.get(code)
    if not transaction_type or not ticker:
        return None

    amounts = txn.get("transactionAmounts", {})
    shares = safe_decimal(
        txn.get("transactionAmounts", {}).get("transactionShares", {}).get("#text") or
        amounts.get("transactionShares")
    )
    price = safe_decimal(amounts.get("transactionPricePerShare", {}).get("#text") or
                         amounts.get("transactionPricePerShare") or "0")
    txn_date = safe_date(txn.get("transactionDate", {}).get("value") or
                         txn.get("transactionDate"))

    if shares is None or shares <= 0:
        return None

    underlying = txn.get("underlyingSecurityShares", {})
    underlying_shares = safe_decimal(
        underlying.get("#text") if isinstance(underlying, dict) else underlying
    )
    total_value = float((underlying_shares or shares) * (price or Decimal("0")))

    return {
        "ticker": ticker.upper(),
        "company": company,
        "insider_name": insider_name,
        "insider_title": insider_title,
        "transaction_type": f"option_{transaction_type}",
        "shares": int(shares),
        "price_per_share": float(price or 0),
        "total_value": total_value,
        "transaction_date": txn_date or datetime.now(timezone.utc),
        "source": "form4",
        "form_url": form_url,
    }
