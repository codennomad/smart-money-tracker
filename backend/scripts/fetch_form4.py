#!/usr/bin/env python3
"""Standalone Form 4 fetch script — run by cron every 4 hours."""
import asyncio, sys, uuid, os
from datetime import datetime, timezone
sys.path.insert(0, '/Deploy/apps/smart-money-api')

async def main():
    from app.services.edgar import get_recent_form4_filings, get_form4_xml
    from app.parsers.form4 import parse_form4
    from app.core.database import AsyncSessionLocal
    from app.models.insider import InsiderTrade
    from sqlalchemy import select

    print(f"[{datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}] Fetching Form 4 (last 2 days)...")
    filings = await get_recent_form4_filings(days_back=2, max_results=100)
    print(f"  Got {len(filings)} RSS entries")

    inserted = 0
    seen_acc = set()
    async with AsyncSessionLocal() as db:
        for filing in filings:
            acc = filing['accessionNo']
            if acc in seen_acc:
                continue
            seen_acc.add(acc)
            filed_at = filing.get('filedAt') or datetime.now(timezone.utc)
            try:
                xml_bytes = await get_form4_xml(filing['cik'], acc)
                trades = parse_form4(xml_bytes, form_url=filing.get('indexUrl', ''))
                for trade in trades:
                    if not trade.get('ticker'):
                        continue
                    # Skip duplicates
                    existing = await db.execute(
                        select(InsiderTrade).where(
                            InsiderTrade.form_url == trade.get('form_url', ''),
                            InsiderTrade.ticker == trade['ticker'],
                            InsiderTrade.shares == trade['shares'],
                        )
                    )
                    if existing.scalar_one_or_none():
                        continue
                    trade['filed_at'] = filed_at
                    db.add(InsiderTrade(id=str(uuid.uuid4()), **trade))
                    inserted += 1
            except Exception as e:
                print(f"  skip {acc}: {type(e).__name__}: {str(e)[:80]}")
                continue
        await db.commit()

    print(f"  Done: {inserted} new trades inserted")

asyncio.run(main())
