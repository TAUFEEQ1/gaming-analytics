# Gaming Analytics API - Celery Setup

## Installation

Install additional dependencies:

```bash
pip install -r requirements.txt
```

## Running Celery

### 1. Start Redis Server

Make sure Redis is installed and running:

```bash
# On macOS with Homebrew
brew install redis
brew services start redis

# Or run directly
redis-server
```

### 2. Create the Notifications Table

Before starting Celery, create the notifications table:

```bash
cd gaming-api
python create_notifications_table.py
```

### 3. Populate Test Notifications (Optional)

Since the Celery task looks for data from the last 10 minutes and your data is from 2021, you can populate test notifications from historical data:

```bash
cd gaming-api
python test_celery_task.py
```

This will scan all historical data and create notifications for anomalies with Z-score > 3.

### 4. Start Celery Worker

In a separate terminal:

```bash
cd gaming-api
celery -A celery_app worker --loglevel=info
```

### 4. Start Celery Beat (Scheduler)

In another terminal:

```bash
cd gaming-api
celery -A celery_app beat --loglevel=info
```

### 5. Start FastAPI Server

```bash
cd gaming-api
uvicorn main:app --reload
```

## Notification API Endpoints

### Get Notifications

```bash
# Get all notifications
GET /api/notifications/

# Get unread notifications only
GET /api/notifications/?unread_only=true

# Pagination
GET /api/notifications/?limit=20&offset=0
```

### Mark Notification as Read

```bash
PATCH /api/notifications/{notification_id}/read
```

### Mark All Notifications as Read

```bash
PATCH /api/notifications/mark-all-read
```

### Delete Notification

```bash
DELETE /api/notifications/{notification_id}
```

## Celery Task Schedule

The anomaly detection task runs every 5 minutes automatically:

- Scans the last 10 minutes of data
- Detects anomalies with |Z-score| > 3
- Creates notifications for new anomalies
- Avoids duplicate notifications

## Manual Task Execution

You can manually trigger the anomaly detection task:

```python
from tasks import detect_anomalies_task
result = detect_anomalies_task.delay()
```

## Monitoring Celery

### Flower (Web-based monitoring tool)

```bash
pip install flower
celery -A celery_app flower
```

Then visit <http://localhost:5555>
