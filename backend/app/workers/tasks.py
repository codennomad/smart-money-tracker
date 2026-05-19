"""
Celery tasks — data pipeline orchestration.
Each task fetches → parses → upserts → triggers anomaly detection.
"""
import asyncio
import logging
from datetime import datetime, timezone

from celery import shared_task

from app.workers.celery_app import celery_app

log = logging.getLogger(__name__)


def _run(coro):
    """Run an async coroutine from a sync Celery task."""
    return asyncio.run(coro)


# ── Form 4 ────────────────────────────────────────────────────────────────────

@celery_app.task(bind=True, max_retries=3, default_retry_delay=120, name="app.workers.tasks.fetch_form4")
def fetch_form4(self):
    """Fetch and persist recent Form 4 insider trades from SEC EDGAR."""
    try:
        _run(_fetch_form4_async())
        log.info("fetch_form4 completed")
    except Exception as exc:
        log.error("fetch_form4 failed: %s", exc)
        raise self.retry(exc=exc)


async def _fetch_form4_async():
    from app.services.edgar import get_recent_form4_filings, get_form4_xml
    from app.parsers.form4 import parse_form4
    from app.core.database import AsyncSessionLocal
    from app.models.insider import InsiderTrade
    from sqlalchemy import select
    import uuid

    filings = await get_recent_form4_filings(days_back=1, max_results=100)
    log.info("Got %d Form 4 filings to process", len(filings))

    async with AsyncSessionLocal() as db:
        for filing in filings:
            cik = filing["cik"]
            accession = filing["accessionNo"]
            form_url = filing.get("indexUrl", "")

            try:
                xml_bytes = await get_form4_xml(cik, accession)
                trades = parse_form4(xml_bytes, form_url=form_url)
            except Exception as exc:
                log.warning("Skipping filing %s: %s", accession, exc)
                continue

            for trade in trades:
                # Dedup by accession + ticker + transaction_type + shares
                existing = await db.execute(
                    select(InsiderTrade).where(
                        InsiderTrade.form_url == form_url,
                        InsiderTrade.ticker == trade["ticker"],
                        InsiderTrade.shares == trade["shares"],
                    )
                )
                if existing.scalar_one_or_none():
                    continue

                trade["id"] = str(uuid.uuid4())
                trade["filed_at"] = filing["filedAt"]
                db.add(InsiderTrade(**trade))

        await db.commit()


# ── Congressional disclosures ─────────────────────────────────────────────────

@celery_app.task(bind=True, max_retries=3, default_retry_delay=300, name="app.workers.tasks.fetch_congress")
def fetch_congress(self):
    """Fetch and persist congressional STOCK Act disclosures."""
    try:
        _run(_fetch_congress_async())
        log.info("fetch_congress completed")
    except Exception as exc:
        log.error("fetch_congress failed: %s", exc)
        raise self.retry(exc=exc)


async def _fetch_congress_async():
    from app.core.http_client import fetch
    from app.parsers.congress import parse_house_zip, parse_senate_ptr_json
    from app.core.database import AsyncSessionLocal
    from app.models.congress import CongressTrade
    from sqlalchemy import select
    import uuid

    year = datetime.now(timezone.utc).year

    async with AsyncSessionLocal() as db:
        # House disclosures
        try:
            house_url = f"https://disclosures.house.gov/public_disc/financial-pdfs/{year}FD.zip"
            resp = await fetch(house_url)
            trades = parse_house_zip(resp.content)
            await _upsert_congress_trades(db, trades)
            log.info("House: %d trades parsed", len(trades))
        except Exception as exc:
            log.warning("House disclosures failed: %s", exc)

        # Senate PTR
        try:
            senate_url = (
                "https://efts.senate.gov/LATEST/search-index"
                "?type=ptr&filerType=senator&hits.hits.total.value=true"
            )
            resp = await fetch(senate_url)
            trades = parse_senate_ptr_json(resp.json())
            await _upsert_congress_trades(db, trades)
            log.info("Senate: %d trades parsed", len(trades))
        except Exception as exc:
            log.warning("Senate disclosures failed: %s", exc)

        await db.commit()


async def _upsert_congress_trades(db, trades: list[dict]):
    from app.models.congress import CongressTrade
    from sqlalchemy import select
    import uuid

    for trade in trades:
        existing = await db.execute(
            select(CongressTrade).where(
                CongressTrade.member == trade["member"],
                CongressTrade.ticker == trade["ticker"],
                CongressTrade.transaction_date == trade["transaction_date"],
                CongressTrade.transaction_type == trade["transaction_type"],
            )
        )
        if existing.scalar_one_or_none():
            continue
        trade["id"] = str(uuid.uuid4())
        db.add(CongressTrade(**trade))


# ── FINRA short interest ───────────────────────────────────────────────────────

@celery_app.task(bind=True, max_retries=3, default_retry_delay=300, name="app.workers.tasks.fetch_finra_short")
def fetch_finra_short(self):
    """Fetch and persist FINRA daily short sale volume data."""
    try:
        _run(_fetch_finra_async())
        log.info("fetch_finra_short completed")
    except Exception as exc:
        log.error("fetch_finra_short failed: %s", exc)
        raise self.retry(exc=exc)


async def _fetch_finra_async():
    from app.core.http_client import fetch
    from app.parsers.finra_short import parse_finra_short_file, finra_date_str
    from app.core.database import AsyncSessionLocal
    from app.models.darkpool import DarkPoolPrint
    from sqlalchemy import select
    import uuid

    today = datetime.now(timezone.utc)
    date_str = finra_date_str(today)
    url = f"https://www.finra.org/sites/default/files/data/markets/short-sale/CNMSshvol{date_str}.txt"

    try:
        resp = await fetch(url)
        prints = parse_finra_short_file(resp.text, report_date=today)
    except Exception as exc:
        log.warning("FINRA short file unavailable for %s: %s", date_str, exc)
        return

    async with AsyncSessionLocal() as db:
        for p in prints:
            existing = await db.execute(
                select(DarkPoolPrint).where(
                    DarkPoolPrint.ticker == p["ticker"],
                    DarkPoolPrint.report_date == p["report_date"],
                )
            )
            if existing.scalar_one_or_none():
                continue
            p["id"] = str(uuid.uuid4())
            db.add(DarkPoolPrint(**p))
        await db.commit()

    log.info("FINRA: %d short prints saved", len(prints))


# ── 13F ───────────────────────────────────────────────────────────────────────

@celery_app.task(bind=True, max_retries=2, default_retry_delay=600, name="app.workers.tasks.fetch_13f")
def fetch_13f(self):
    """Fetch and persist quarterly 13F institutional holdings."""
    try:
        _run(_fetch_13f_async())
        log.info("fetch_13f completed")
    except Exception as exc:
        log.error("fetch_13f failed: %s", exc)
        raise self.retry(exc=exc)


async def _fetch_13f_async():
    from app.services.edgar import get_recent_13f_filers
    # 13F enrichment is complex (CUSIP→ticker mapping needed)
    # This stub logs filers — full implementation requires CUSIP lookup table
    now = datetime.now(timezone.utc)
    # Last quarter end
    quarter_month = ((now.month - 1) // 3) * 3
    quarter_end = now.replace(month=quarter_month or 12, day=31 if quarter_month == 0 else 30)
    filers = await get_recent_13f_filers(quarter_end.strftime("%Y-%m-%d"), max_results=20)
    log.info("13F: found %d filers for period ending %s", len(filers), quarter_end.date())


# ── Anomaly detection ─────────────────────────────────────────────────────────

@celery_app.task(bind=True, max_retries=2, name="app.workers.tasks.run_anomaly_detection")
def run_anomaly_detection(self):
    """Run ML anomaly detection on recent insider + congress trades."""
    try:
        count = _run(_run_anomaly_async())
        log.info("Anomaly detection: %d alerts generated", count)
    except Exception as exc:
        log.error("Anomaly detection failed: %s", exc)
        raise self.retry(exc=exc)


async def _run_anomaly_async() -> int:
    from app.services.anomaly import detect_anomalies
    return await detect_anomalies()
