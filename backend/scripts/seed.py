"""
Seed script — populates dev.db with realistic fake data.
Usage: python scripts/seed.py
"""
import asyncio
import sys
import uuid
from datetime import datetime, timedelta, timezone, date
from pathlib import Path
import random

# Ensure backend/ is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.models.insider import InsiderTrade
from app.models.congress import CongressTrade
from app.models.options import OptionsFlow
from app.models.darkpool import DarkPoolPrint
from app.models.alert import AnomalyAlert

DB_URL = "sqlite+aiosqlite:///./dev.db"

# ── realistic data sets ────────────────────────────────────────────────────────

TICKERS = [
    ("AAPL", "Apple Inc."),
    ("MSFT", "Microsoft Corporation"),
    ("NVDA", "NVIDIA Corporation"),
    ("TSLA", "Tesla Inc."),
    ("AMZN", "Amazon.com Inc."),
    ("META", "Meta Platforms Inc."),
    ("GOOGL", "Alphabet Inc."),
    ("JPM", "JPMorgan Chase & Co."),
    ("BAC", "Bank of America Corporation"),
    ("XOM", "Exxon Mobil Corporation"),
]

INSIDERS = [
    ("Timothy Cook", "Chief Executive Officer"),
    ("Luca Maestri", "Chief Financial Officer"),
    ("Katherine Adams", "Senior VP General Counsel"),
    ("Craig Federighi", "Senior VP Software Engineering"),
    ("Sundar Pichai", "Chief Executive Officer"),
    ("Satya Nadella", "Chief Executive Officer"),
    ("Jensen Huang", "President & CEO"),
    ("Elon Musk", "Chief Executive Officer"),
    ("Andy Jassy", "President & CEO"),
    ("Mark Zuckerberg", "Chairman & CEO"),
    ("Jamie Dimon", "Chairman & CEO"),
    ("Brian Moynihan", "President & CEO"),
]

CONGRESS_MEMBERS = [
    ("Nancy Pelosi", "D", "house"),
    ("Paul Ryan", "R", "house"),
    ("Mitch McConnell", "R", "senate"),
    ("Chuck Schumer", "D", "senate"),
    ("Kevin McCarthy", "R", "house"),
    ("Alexandria Ocasio-Cortez", "D", "house"),
    ("Rand Paul", "R", "senate"),
    ("Elizabeth Warren", "D", "senate"),
]

AMOUNT_BRACKETS = [
    (1_001, 15_000),
    (15_001, 50_000),
    (50_001, 100_000),
    (100_001, 250_000),
    (250_001, 500_000),
    (500_001, 1_000_000),
]


def rnd_date(days_back_max: int = 90) -> datetime:
    delta = timedelta(days=random.randint(0, days_back_max), hours=random.randint(9, 16))
    return datetime.now(timezone.utc) - delta


def rnd_id() -> str:
    return str(uuid.uuid4())


# ── generators ─────────────────────────────────────────────────────────────────

def gen_insider_trades(n: int = 80) -> list[InsiderTrade]:
    trades = []
    for _ in range(n):
        ticker, company = random.choice(TICKERS)
        insider_name, insider_title = random.choice(INSIDERS)
        is_buy = random.random() > 0.35
        txn_type = "buy" if is_buy else "sell"
        shares = random.randint(1_000, 500_000)
        price = round(random.uniform(50, 800), 2)
        total = round(shares * price, 2)
        filed_at = rnd_date(30)
        txn_date = filed_at - timedelta(days=random.randint(1, 2))
        anomaly = round(random.uniform(0.0, 0.4), 3)
        # 20% chance of being anomalous
        if random.random() > 0.8:
            anomaly = round(random.uniform(0.7, 0.98), 3)

        trades.append(InsiderTrade(
            id=rnd_id(),
            ticker=ticker,
            company=company,
            insider_name=insider_name,
            insider_title=insider_title,
            transaction_type=txn_type,
            shares=shares,
            price_per_share=price,
            total_value=total,
            filed_at=filed_at,
            transaction_date=txn_date,
            source="form4",
            form_url=f"https://www.sec.gov/Archives/edgar/data/320193/{rnd_id().replace('-', '')}.xml",
            anomaly_score=anomaly,
        ))

    # Force a cluster: 4 insiders buy NVDA within 2 days
    cluster_base = datetime.now(timezone.utc) - timedelta(days=1)
    for i in range(4):
        trades.append(InsiderTrade(
            id=rnd_id(),
            ticker="NVDA",
            company="NVIDIA Corporation",
            insider_name=INSIDERS[i][0],
            insider_title=INSIDERS[i][1],
            transaction_type="buy",
            shares=random.randint(10_000, 100_000),
            price_per_share=round(random.uniform(800, 950), 2),
            total_value=round(random.randint(10_000, 100_000) * 880, 2),
            filed_at=cluster_base - timedelta(hours=i * 6),
            transaction_date=cluster_base - timedelta(days=1, hours=i * 6),
            source="form4",
            form_url=f"https://www.sec.gov/Archives/edgar/data/1045810/{rnd_id().replace('-', '')}.xml",
            anomaly_score=0.91,
        ))

    return trades


def gen_congress_trades(n: int = 40) -> list[CongressTrade]:
    trades = []
    for _ in range(n):
        ticker, company = random.choice(TICKERS)
        member, party, chamber = random.choice(CONGRESS_MEMBERS)
        is_buy = random.random() > 0.4
        txn_type = "buy" if is_buy else "sell"
        amt_min, amt_max = random.choice(AMOUNT_BRACKETS)
        txn_date = rnd_date(60)
        days_delay = random.randint(1, 45)
        disclosed_at = txn_date + timedelta(days=days_delay)

        trades.append(CongressTrade(
            id=rnd_id(),
            member=member,
            party=party,
            chamber=chamber,
            ticker=ticker,
            company=company,
            transaction_type=txn_type,
            amount_min=amt_min,
            amount_max=amt_max,
            transaction_date=txn_date,
            disclosed_at=disclosed_at,
            days_to_disclose=days_delay,
        ))

    return trades


def gen_options_flow(n: int = 30) -> list[OptionsFlow]:
    flows = []
    for _ in range(n):
        ticker, _ = random.choice(TICKERS)
        days_out = random.choice([7, 14, 21, 30, 45, 60])
        expiry = date.today() + timedelta(days=days_out)
        call_put = random.choice(["call", "put"])
        strike = round(random.uniform(100, 1000), 0)
        volume = random.randint(500, 50_000)
        oi = random.randint(100, volume)
        vol_oi = round(volume / max(oi, 1), 2)
        premium = round(random.uniform(0.5, 25.0), 2) * 100 * volume
        score = round(random.uniform(0.5, 0.99), 3)

        flows.append(OptionsFlow(
            id=rnd_id(),
            ticker=ticker,
            expiry=expiry,
            strike=strike,
            call_put=call_put,
            premium=premium,
            volume=volume,
            open_interest=oi,
            vol_oi_ratio=vol_oi,
            unusual_score=score,
            detected_at=rnd_date(7),
        ))

    return flows


def gen_darkpool_prints(n: int = 50) -> list[DarkPoolPrint]:
    prints = []
    for _ in range(n):
        ticker, _ = random.choice(TICKERS)
        total_vol = random.randint(100_000, 5_000_000)
        short_vol = int(total_vol * random.uniform(0.2, 0.65))
        short_exempt = int(short_vol * random.uniform(0, 0.05))
        price = round(random.uniform(50, 900), 2)
        rpt_date = date.today() - timedelta(days=random.randint(0, 30))

        prints.append(DarkPoolPrint(
            id=rnd_id(),
            ticker=ticker,
            shares=short_vol,
            price=price,
            total_value=round(short_vol * price, 2),
            short_volume=short_vol,
            short_exempt_volume=short_exempt,
            total_volume=total_vol,
            short_pct=round((short_vol / total_vol) * 100, 4),
            report_date=rpt_date,
        ))

    return prints


def gen_alerts(insider_ids: list[str], congress_ids: list[str]) -> list[AnomalyAlert]:
    alerts = []

    # Cluster buying on NVDA
    alerts.append(AnomalyAlert(
        id=rnd_id(),
        ticker="NVDA",
        alert_type="cluster_buying",
        confidence=0.91,
        description="4 insiders bought NVDA in the last 2 days (total $47.2M)",
        related_ids=random.sample(insider_ids, min(4, len(insider_ids))),
        detected_at=datetime.now(timezone.utc) - timedelta(hours=2),
    ))

    # Congress + options combo
    alerts.append(AnomalyAlert(
        id=rnd_id(),
        ticker="TSLA",
        alert_type="congress_options_combo",
        confidence=0.85,
        description="Congressional trade on TSLA and unusual options flow detected within 1 day of each other",
        related_ids=random.sample(congress_ids, min(2, len(congress_ids))),
        detected_at=datetime.now(timezone.utc) - timedelta(hours=5),
    ))

    # Unusual volume
    alerts.append(AnomalyAlert(
        id=rnd_id(),
        ticker="AAPL",
        alert_type="unusual_volume",
        confidence=0.78,
        description="Unusual insider buy volume on AAPL: $24.5M — anomalous vs. 90-day baseline",
        related_ids=random.sample(insider_ids, min(2, len(insider_ids))),
        detected_at=datetime.now(timezone.utc) - timedelta(hours=1),
    ))

    return alerts


# ── main ───────────────────────────────────────────────────────────────────────

async def seed():
    engine = create_async_engine(DB_URL, echo=False)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with factory() as db:
        print("Seeding insider trades...")
        insiders = gen_insider_trades(80)
        db.add_all(insiders)
        await db.flush()

        print("Seeding congress trades...")
        congress = gen_congress_trades(40)
        db.add_all(congress)
        await db.flush()

        print("Seeding options flow...")
        options = gen_options_flow(30)
        db.add_all(options)
        await db.flush()

        print("Seeding dark pool prints...")
        darkpool = gen_darkpool_prints(50)
        db.add_all(darkpool)
        await db.flush()

        print("Seeding anomaly alerts...")
        insider_ids = [t.id for t in insiders]
        congress_ids = [t.id for t in congress]
        alerts = gen_alerts(insider_ids, congress_ids)
        db.add_all(alerts)

        await db.commit()

    await engine.dispose()
    print(f"\nSeed complete:")
    print(f"  {len(insiders)} insider trades")
    print(f"  {len(congress)} congress trades")
    print(f"  {len(options)} options flows")
    print(f"  {len(darkpool)} dark pool prints")
    print(f"  {len(alerts)} anomaly alerts")


if __name__ == "__main__":
    asyncio.run(seed())
