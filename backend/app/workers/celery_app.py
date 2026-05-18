from celery import Celery
from celery.schedules import crontab
from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "smart_money_tracker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # Retry failed tasks up to 3 times with exponential backoff
    task_max_retries=3,
    task_default_retry_delay=60,
)

celery_app.conf.beat_schedule = {
    # Form 4 — every 30 minutes during market hours (Mon–Fri)
    "fetch-form4-every-30min": {
        "task": "app.workers.tasks.fetch_form4",
        "schedule": crontab(minute="*/30", hour="9-20", day_of_week="1-5"),
    },
    # Congressional disclosures — daily at 8 AM UTC
    "fetch-congress-daily": {
        "task": "app.workers.tasks.fetch_congress",
        "schedule": crontab(hour=8, minute=0),
    },
    # FINRA short interest — daily at 9 PM UTC (after market close)
    "fetch-finra-short-daily": {
        "task": "app.workers.tasks.fetch_finra_short",
        "schedule": crontab(hour=21, minute=0, day_of_week="1-5"),
    },
    # Anomaly detection — every hour
    "run-anomaly-detection-hourly": {
        "task": "app.workers.tasks.run_anomaly_detection",
        "schedule": crontab(minute=0),
    },
    # 13F — quarterly, run on the 46th day after quarter end
    "fetch-13f-quarterly": {
        "task": "app.workers.tasks.fetch_13f",
        "schedule": crontab(hour=6, minute=0, day_of_month="15", month_of_year="2,5,8,11"),
    },
}
