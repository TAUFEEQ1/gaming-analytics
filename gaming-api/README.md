# Gaming Analytics API

FastAPI backend for the Gaming Dashboard application, providing real-time analytics and anomaly detection for casino gaming data.

## Features

- 📊 **Analytics Endpoints**: Stakes and payouts time-series data with anomaly detection
- 🚨 **Anomaly Detection**: Real-time anomaly notifications and historical records
- 📈 **Statistics**: Dashboard summary cards and system metrics
- 🔄 **CORS Support**: Configured for frontend integration
- 📝 **API Documentation**: Auto-generated Swagger/OpenAPI docs

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env` and adjust settings as needed:

```env
DATABASE_URL=sqlite:///./gaming_metrics.db
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
API_HOST=0.0.0.0
API_PORT=8000
```

### 3. Run the Server

```bash
python main.py
```

Or with uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### Analytics

- `GET /api/analytics/stakes-payouts/{chart_type}` - Get stakes or payouts chart data
  - Parameters: `chart_type` (stakes|payouts), `hours` (10-1000)
- `GET /api/analytics/turnover` - Get turnover threshold monitoring data
  - Parameters: `days` (7-365)

### Anomalies

- `GET /api/anomalies/notifications` - Get recent anomaly alerts
  - Parameters: `limit` (1-50)
- `GET /api/anomalies/table` - Get anomaly table records
  - Parameters: `limit` (1-100), `severity` (all|critical|high|medium|low)
- `GET /api/anomalies/count` - Get anomaly counts by type and severity
  - Parameters: `hours` (1-168)

### Stats

- `GET /api/stats/cards` - Get dashboard stat cards
- `GET /api/stats/summary` - Get complete dashboard summary
- `GET /api/stats/metrics` - Get current system metrics

### Health

- `GET /health` - Health check endpoint
- `GET /` - API information

## API Documentation

Once the server is running, visit:

- Swagger UI: <http://localhost:8000/docs>
- ReDoc: <http://localhost:8000/redoc>

## Integration with Frontend

Update your Vue.js dashboard to fetch data from these endpoints:

```typescript
// Example API calls
const API_BASE = 'http://localhost:8000/api'

// Get stakes chart data
const stakesData = await fetch(`${API_BASE}/analytics/stakes-payouts/stakes`)

// Get anomaly notifications
const notifications = await fetch(`${API_BASE}/anomalies/notifications?limit=5`)

// Get dashboard stats
const stats = await fetch(`${API_BASE}/stats/cards`)
```

## Development

The API uses sample/mock data generators. To integrate with a real database:

1. Update the database models in `models/`
2. Implement actual data queries in the routers
3. Configure SQLAlchemy connection in `main.py`
4. Add database migration support (e.g., Alembic)

## Project Structure

```env
gaming-api/
├── main.py              # FastAPI application entry point
├── requirements.txt     # Python dependencies
├── .env                 # Environment configuration
├── models/
│   └── schemas.py      # Pydantic models
└── routers/
    ├── analytics.py    # Analytics endpoints
    ├── anomalies.py    # Anomaly detection endpoints
    └── stats.py        # Statistics endpoints
```

## Next Steps

- [ ] Connect to actual database
- [ ] Implement real anomaly detection algorithm (Z-score, isolation forest, etc.)
- [ ] Add authentication/authorization
- [ ] Add rate limiting
- [ ] Implement WebSocket support for real-time updates
- [ ] Add caching layer (Redis)
- [ ] Add logging and monitoring
