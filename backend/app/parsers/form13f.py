"""
SEC EDGAR Form 13F parser.

13F = quarterly portfolio holdings of institutional managers with >$100M AUM.
Filed within 45 days after each quarter end.

XML structure (13F-HR):
  <informationTable>
    <infoTable>
      <nameOfIssuer>
      <titleOfClass>
      <cusip>
      <value>          ← in thousands of USD
      <shrsOrPrnAmt>
        <sshPrnamt>
        <sshPrnamtType> ← SH (shares) | PRN (principal amount)
      <investmentDiscretion>
      <votingAuthority>
"""
from typing import Any
import xmltodict

from app.parsers.base import strip_text, safe_decimal, safe_int


# CUSIP → ticker lookup is done externally (SEC provides a mapping file)
# Here we store raw CUSIP and enrich later via a lookup table.

def parse_form13f(xml_bytes: bytes, filer_cik: str, filer_name: str, period_of_report: str) -> list[dict[str, Any]]:
    """
    Parse 13F-HR information table XML.
    Returns list of holding dicts.
    """
    try:
        doc = xmltodict.parse(xml_bytes, force_list=("infoTable",))
    except Exception as exc:
        raise ValueError(f"Failed to parse 13F XML: {exc}") from exc

    # Root may be wrapped differently across filers
    root = (
        doc.get("informationTable")
        or doc.get("ns1:informationTable")
        or doc.get("com:informationTable")
        or {}
    )

    rows = root.get("infoTable") or root.get("ns1:infoTable") or []
    if not rows:
        return []

    holdings: list[dict[str, Any]] = []

    for row in rows:
        name = strip_text(row.get("nameOfIssuer") or row.get("ns1:nameOfIssuer"))
        cusip = strip_text(row.get("cusip") or row.get("ns1:cusip", "")).upper()

        value_raw = row.get("value") or row.get("ns1:value")
        value_thousands = safe_decimal(value_raw)
        value_usd = float(value_thousands * 1000) if value_thousands else 0.0

        shrs_node = row.get("shrsOrPrnAmt") or row.get("ns1:shrsOrPrnAmt") or {}
        shares = safe_int(shrs_node.get("sshPrnamt") or shrs_node.get("ns1:sshPrnamt"))
        share_type = strip_text(shrs_node.get("sshPrnamtType") or shrs_node.get("ns1:sshPrnamtType"))

        if not cusip or value_usd <= 0:
            continue

        holdings.append({
            "filer_cik": filer_cik,
            "filer_name": filer_name,
            "period_of_report": period_of_report,
            "issuer_name": name,
            "cusip": cusip,
            "value_usd": value_usd,
            "shares": shares or 0,
            "share_type": share_type or "SH",
        })

    return holdings


def cusip_to_ticker_map(mapping_csv_text: str) -> dict[str, str]:
    """
    Build CUSIP→ticker dict from SEC's CUSIP mapping file.
    Format: CUSIP,ticker,companyName (CSV, no header)
    """
    result: dict[str, str] = {}
    for line in mapping_csv_text.splitlines():
        parts = line.split(",")
        if len(parts) >= 2:
            cusip = parts[0].strip().upper()
            ticker = parts[1].strip().upper()
            if cusip and ticker:
                result[cusip] = ticker
    return result
