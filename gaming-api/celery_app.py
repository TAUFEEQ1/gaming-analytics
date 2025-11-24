from celery import Celery
from celery.schedules import crontab
import os
from dotenv import load_dotenv

load_dotenv()

# Configure Celery
celery_app = Celery(
    'gaming_analytics',
    broker=os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/3'),
    backend=os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/3')
)

# Celery configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Schedule periodic tasks
celery_app.conf.beat_schedule = {
    'detect-anomalies-every-5-minutes': {
        'task': 'tasks.detect_anomalies_task',
        'schedule': crontab(minute='*/5'),  # Run every 5 minutes
    },
}
