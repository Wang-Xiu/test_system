import os
from celery import Celery

# Get Redis URL from environment variable or use default
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6385/0")

celery_app = Celery(
    "auto_test_scheduler",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["backend.scheduler.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
)
