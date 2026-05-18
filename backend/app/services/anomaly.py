"""
ML anomaly detection — Isolation Forest on insider + congress flow.

Signals detected:
  1. cluster_buying    — multiple insiders buying same ticker within 5 days
  2. congress_options_combo — congress trade + unusual options flow on same ticker ≤3 days apart
  3. pre_earnings_flow  — large insider buy ≤30 days before earnings (future: enrich w/ calendar)
  4. unusual_volume     — total insider buy value > 3σ above 90-day mean for that ticker
"""
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np
from sklearn.ensemble import IsolationForest
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.insider import InsiderTrade
from app.models.congress import CongressTrade
from app.models.options import OptionsFlow
from app.models.alert import AnomalyAlert
from app.api.v1.routes.ws import broadcast

log = logging.getLogger(__name__)

_LOOKBACK_DAYS = 90
_CLUSTER_WINDOW_DAYS = 5
_COMBO_WINDOW_DAYS = 3


async def detect_anomalies() -> int:
    """Run all detectors. Returns count of new alerts persisted."""
    async with AsyncSessionLocal() as db:
        alerts: list[dict[str, Any]] = []
        alerts += await _detect_cluster_buying(db)
        alerts += await _detect_congress_options_combo(db)
        alerts += await _detect_unusual_volume_isolation_forest(db)

        new_count = 0
        for alert_data in alerts:
            # Dedup: same ticker + alert_type within 24h
            existing = await db.execute(
                select(AnomalyAlert).where(
                    AnomalyAlert.ticker == alert_data["ticker"],
                    AnomalyAlert.alert_type == alert_data["alert_type"],
                    AnomalyAlert.detected_at >= datetime.now(timezone.utc) - timedelta(hours=24),
                )
            )
            if existing.scalar_one_or_none():
                continue

            alert = AnomalyAlert(**alert_data)
            db.add(alert)
            new_count += 1

            # Broadcast to connected WebSocket clients
            await broadcast({
                "id": alert_data["id"],
                "ticker": alert_data["ticker"],
                "alertType": alert_data["alert_type"],
                "confidence": alert_data["confidence"],
                "description": alert_data["description"],
                "relatedIds": alert_data["related_ids"],
                "detectedAt": alert_data["detected_at"].isoformat(),
            })

        await db.commit()
        return new_count


async def _detect_cluster_buying(db: AsyncSession) -> list[dict[str, Any]]:
    """Flag tickers where ≥3 distinct insiders buy within 5 days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=_CLUSTER_WINDOW_DAYS)

    stmt = (
        select(
            InsiderTrade.ticker,
            func.count(func.distinct(InsiderTrade.insider_name)).label("insider_count"),
            func.sum(InsiderTrade.total_value).label("total_value"),
            func.array_agg(InsiderTrade.id).label("ids"),
        )
        .where(
            InsiderTrade.filed_at >= cutoff,
            InsiderTrade.transaction_type == "buy",
        )
        .group_by(InsiderTrade.ticker)
        .having(func.count(func.distinct(InsiderTrade.insider_name)) >= 3)
    )

    result = await db.execute(stmt)
    rows = result.fetchall()

    alerts = []
    for row in rows:
        confidence = min(0.95, 0.6 + (row.insider_count - 3) * 0.1)
        alerts.append({
            "id": str(uuid.uuid4()),
            "ticker": row.ticker,
            "alert_type": "cluster_buying",
            "confidence": confidence,
            "description": (
                f"{row.insider_count} insiders bought {row.ticker} "
                f"in the last {_CLUSTER_WINDOW_DAYS} days "
                f"(total ${row.total_value:,.0f})"
            ),
            "related_ids": list(row.ids) if row.ids else [],
            "detected_at": datetime.now(timezone.utc),
        })

    return alerts


async def _detect_congress_options_combo(db: AsyncSession) -> list[dict[str, Any]]:
    """
    Flag tickers where a Congress member traded AND unusual options
    appeared within 3 days of each other.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)

    congress_stmt = (
        select(CongressTrade.ticker, CongressTrade.transaction_date, CongressTrade.id)
        .where(CongressTrade.disclosed_at >= cutoff)
    )
    c_result = await db.execute(congress_stmt)
    congress_rows = c_result.fetchall()

    options_stmt = (
        select(OptionsFlow.ticker, OptionsFlow.detected_at, OptionsFlow.id)
        .where(
            OptionsFlow.unusual_score >= 0.7,
            OptionsFlow.detected_at >= cutoff,
        )
    )
    o_result = await db.execute(options_stmt)
    options_rows = o_result.fetchall()

    options_by_ticker: dict[str, list] = {}
    for o in options_rows:
        options_by_ticker.setdefault(o.ticker, []).append(o)

    alerts = []
    seen_tickers: set[str] = set()

    for c in congress_rows:
        if c.ticker in seen_tickers:
            continue
        o_list = options_by_ticker.get(c.ticker, [])
        for o in o_list:
            delta = abs((o.detected_at - c.transaction_date).days)
            if delta <= _COMBO_WINDOW_DAYS:
                seen_tickers.add(c.ticker)
                alerts.append({
                    "id": str(uuid.uuid4()),
                    "ticker": c.ticker,
                    "alert_type": "congress_options_combo",
                    "confidence": 0.85,
                    "description": (
                        f"Congressional trade on {c.ticker} and unusual options "
                        f"flow detected within {delta} day(s) of each other"
                    ),
                    "related_ids": [c.id, o.id],
                    "detected_at": datetime.now(timezone.utc),
                })
                break

    return alerts


async def _detect_unusual_volume_isolation_forest(db: AsyncSession) -> list[dict[str, Any]]:
    """
    Use Isolation Forest on the last 90 days of daily buy values per ticker.
    Flags tickers where today's buy volume is anomalous.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=_LOOKBACK_DAYS)
    today_cutoff = datetime.now(timezone.utc) - timedelta(days=1)

    stmt = (
        select(
            InsiderTrade.ticker,
            func.date_trunc("day", InsiderTrade.filed_at).label("day"),
            func.sum(InsiderTrade.total_value).label("daily_buy"),
            func.array_agg(InsiderTrade.id).label("ids"),
        )
        .where(
            InsiderTrade.filed_at >= cutoff,
            InsiderTrade.transaction_type == "buy",
        )
        .group_by(InsiderTrade.ticker, func.date_trunc("day", InsiderTrade.filed_at))
        .order_by(InsiderTrade.ticker, func.date_trunc("day", InsiderTrade.filed_at))
    )

    result = await db.execute(stmt)
    rows = result.fetchall()

    if not rows:
        return []

    # Group by ticker
    by_ticker: dict[str, list[dict]] = {}
    for row in rows:
        by_ticker.setdefault(row.ticker, []).append({
            "day": row.day,
            "daily_buy": float(row.daily_buy),
            "ids": list(row.ids) if row.ids else [],
        })

    alerts = []

    for ticker, days in by_ticker.items():
        if len(days) < 10:  # need enough history
            continue

        values = np.array([[d["daily_buy"]] for d in days])
        latest_day = days[-1]

        if latest_day["day"] < today_cutoff:
            continue  # no data from today/yesterday

        clf = IsolationForest(contamination=0.05, random_state=42, n_estimators=100)
        clf.fit(values[:-1])  # train on all but latest
        score = clf.decision_function([[latest_day["daily_buy"]]])[0]
        pred = clf.predict([[latest_day["daily_buy"]]])[0]

        if pred == -1:  # anomaly
            confidence = float(min(0.95, max(0.6, 0.75 + abs(score))))
            alerts.append({
                "id": str(uuid.uuid4()),
                "ticker": ticker,
                "alert_type": "unusual_volume",
                "confidence": round(confidence, 3),
                "description": (
                    f"Unusual insider buy volume on {ticker}: "
                    f"${latest_day['daily_buy']:,.0f} — anomalous vs. 90-day baseline"
                ),
                "related_ids": latest_day["ids"],
                "detected_at": datetime.now(timezone.utc),
            })

    return alerts
