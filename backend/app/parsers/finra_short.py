"""
FINRA OTC Transparency — short sale volume parser.

Source: https://api.finra.org/data/group/otcMarket/name/weeklySummary
        https://www.finra.org/finra-data/browse-catalog/short-sale-volume-data/daily-short-sale-volume-files

Daily flat file format (pipe-delimited):
  Date|Symbol|ShortVolume|ShortExemptVolume|TotalVolume|Market

We download the daily file and parse each line.
"""
from datetime import datetime, timezone
from typing import Any

from app.parsers.base import strip_text, safe_int, safe_date


# FINRA daily short sale URL template
FINRA_SHORT_URL = (
    "https://api.finra.org/data/group/otcMarket/name/weeklySummary"
    "?limit=50&offset=0&compareFilters=date%3Aeq%3A{date}"
)

FINRA_DAILY_FILE_URL = (
    "https://www.finra.org/sites/default/files/data/markets/short-sale/CNMSshvol{date}.txt"
)


def parse_finra_short_file(text: str, report_date: datetime | None = None) -> list[dict[str, Any]]:
    """
    Parse FINRA daily short sale volume flat file.

    File header: Date|Symbol|ShortVolume|ShortExemptVolume|TotalVolume|Market
    Last line is a totals row starting with 'Date' — skip it.
    """
    lines = text.strip().splitlines()
    if not lines:
        return []

    # Skip header line
    start = 1 if lines[0].startswith("Date") else 0
    results: list[dict[str, Any]] = []

    for line in lines[start:]:
        line = line.strip()
        if not line or line.startswith("Date"):
            continue

        parts = line.split("|")
        if len(parts) < 5:
            parts = line.split("\t")
        if len(parts) < 5:
            continue

        date_raw, symbol, short_vol, short_exempt, total_vol = parts[:5]

        ticker = strip_text(symbol).upper()
        if not ticker or len(ticker) > 10:
            continue

        short_volume = safe_int(short_vol) or 0
        short_exempt_volume = safe_int(short_exempt) or 0
        total_volume = safe_int(total_vol) or 0

        if total_volume <= 0:
            continue

        short_pct = (short_volume / total_volume) * 100 if total_volume > 0 else 0.0
        parsed_date = safe_date(date_raw) or report_date or datetime.now(timezone.utc)

        results.append({
            "ticker": ticker,
            "shares": short_volume,
            "price": 0.0,             # price not in this dataset
            "total_value": 0.0,       # enriched later via price lookup
            "short_volume": short_volume,
            "short_exempt_volume": short_exempt_volume,
            "total_volume": total_volume,
            "short_pct": round(short_pct, 4),
            "report_date": parsed_date.date() if hasattr(parsed_date, "date") else parsed_date,
        })

    return results


def finra_date_str(dt: datetime) -> str:
    """Format date as YYYYMMDD for FINRA URLs."""
    return dt.strftime("%Y%m%d")
