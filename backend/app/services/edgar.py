"""
SEC EDGAR API client.

Endpoints used:
  - Submissions:  https://data.sec.gov/submissions/CIK{cik10}.json
  - Recent 4s:    https://efts.sec.gov/LATEST/search-index?forms=4&dateRange=custom&startdt={}&enddt={}
  - Filing doc:   https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{doc}.xml
  - CUSIP map:    https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company=&CIK=...

EDGAR rate limit: ~10 req/s per IP. We use 0.15s delay between requests.
"""
import asyncio
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.http_client import fetch

EDGAR_BASE = "https://data.sec.gov"
EDGAR_ARCHIVES = "https://www.sec.gov/Archives/edgar/data"
EFTS_BASE = "https://efts.sec.gov/LATEST/search-index"

_RATE_DELAY = 0.15  # seconds between requests (EDGAR asks < 10 req/s)


async def get_recent_form4_filings(
    days_back: int = 1,
    max_results: int = 100,
) -> list[dict[str, Any]]:
    """
    Fetch recent Form 4 filing metadata from EDGAR full-text search.
    Returns list of {accessionNo, cik, filedAt, formUrl}.
    """
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days_back)
    start_str = start.strftime("%Y-%m-%d")
    end_str = end.strftime("%Y-%m-%d")

    url = (
        f"{EFTS_BASE}?forms=4"
        f"&dateRange=custom&startdt={start_str}&enddt={end_str}"
        f"&hits.hits._source=period_of_report,file_date,period_of_report"
        f"&hits.hits.total.value=true"
        f"&hits.hits._source.entity_id=true"
        f"&_source=period_of_report,file_date,entity_id,file_num"
        f"&hits.hits.highlight.enabled=false"
        f"&dateRange=custom&startdt={start_str}&enddt={end_str}"
        f"&hits.hits.total=true&category=form-type&forms=4"
        f"&hits.hits.highlight=false"
    )

    # Simpler, working EDGAR search endpoint
    search_url = (
        f"https://efts.sec.gov/LATEST/search-index?q=%22%22&dateRange=custom"
        f"&startdt={start_str}&enddt={end_str}&forms=4"
        f"&hits.hits._source=period_of_report,file_date,entity_id,accession_no"
    )

    # Use the submissions RSS feed — more reliable for recent Form 4
    rss_url = (
        "https://www.sec.gov/cgi-bin/browse-edgar"
        f"?action=getcurrent&type=4&dateb=&owner=include"
        f"&count={min(max_results, 40)}&search_text=&output=atom"
    )

    await asyncio.sleep(_RATE_DELAY)
    resp = await fetch(rss_url)
    return _parse_form4_rss(resp.text)


def _parse_form4_rss(atom_xml: str) -> list[dict[str, Any]]:
    """Parse EDGAR Atom RSS feed for Form 4 entries."""
    import xml.etree.ElementTree as ET

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    try:
        root = ET.fromstring(atom_xml)
    except ET.ParseError:
        return []

    filings = []
    for entry in root.findall("atom:entry", ns):
        title_el = entry.find("atom:title", ns)
        link_el = entry.find("atom:link", ns)
        updated_el = entry.find("atom:updated", ns)
        summary_el = entry.find("atom:summary", ns)

        if link_el is None:
            continue

        href = link_el.get("href", "")
        # Extract CIK and accession from URL
        m = re.search(r"/data/(\d+)/(\d{18})", href.replace("-", ""))
        if not m:
            continue

        cik = m.group(1)
        accession_raw = m.group(2)
        accession = f"{accession_raw[:10]}-{accession_raw[10:12]}-{accession_raw[12:]}"

        filed_at = None
        if updated_el is not None and updated_el.text:
            try:
                filed_at = datetime.fromisoformat(updated_el.text.replace("Z", "+00:00"))
            except ValueError:
                pass

        filings.append({
            "cik": cik,
            "accessionNo": accession,
            "filedAt": filed_at or datetime.now(timezone.utc),
            "indexUrl": href,
        })

    return filings


async def get_form4_xml(cik: str, accession_no: str) -> bytes:
    """
    Download the Form 4 primary XML document.
    Accession format: 0001234567-24-000001
    """
    acc_clean = accession_no.replace("-", "")
    index_url = f"{EDGAR_ARCHIVES}/{cik}/{acc_clean}/{accession_no}-index.json"

    await asyncio.sleep(_RATE_DELAY)
    try:
        resp = await fetch(index_url)
        index = resp.json()
        docs = index.get("documents", [])
        xml_doc = next(
            (d for d in docs if d.get("type") == "4" and d.get("document", "").endswith(".xml")),
            None,
        )
        if xml_doc:
            xml_url = f"{EDGAR_ARCHIVES}/{cik}/{acc_clean}/{xml_doc['document']}"
            await asyncio.sleep(_RATE_DELAY)
            xml_resp = await fetch(xml_url)
            return xml_resp.content
    except Exception:
        pass

    # Fallback: try primary doc directly
    fallback_url = f"{EDGAR_ARCHIVES}/{cik}/{acc_clean}/{accession_no}.xml"
    await asyncio.sleep(_RATE_DELAY)
    resp = await fetch(fallback_url)
    return resp.content


async def get_recent_13f_filers(quarter_end: str, max_results: int = 50) -> list[dict[str, Any]]:
    """
    Return recent 13F-HR filers for a given quarter end date (YYYY-MM-DD).
    """
    search_url = (
        f"https://efts.sec.gov/LATEST/search-index?forms=13F-HR"
        f"&dateRange=custom&startdt={quarter_end}&enddt={quarter_end}"
    )
    await asyncio.sleep(_RATE_DELAY)
    resp = await fetch(search_url)
    data = resp.json()
    hits = data.get("hits", {}).get("hits", [])
    return [
        {
            "cik": h["_source"].get("entity_id", ""),
            "name": h["_source"].get("display_names", [""])[0],
            "accessionNo": h["_source"].get("accession_no", ""),
            "filedAt": h["_source"].get("file_date", ""),
        }
        for h in hits[:max_results]
    ]
