# Gaming Dashboard - API Integration

## Overview

The gaming dashboard has been successfully integrated with the gaming-api backend to display real-time anomaly detection data for stakes and payouts.

## API Endpoints Used

### 1. Stakes/Payouts Chart

- **Endpoint**: `GET /api/analytics/stakes-payouts/{chart_type}`
- **Parameters**:
  - `chart_type`: Either 'stakes' or 'payouts'
  - `hours`: Number of records to retrieve (default: 100)
- **Response**: Chart data with anomalies, bounds, mean, and standard deviation

### 2. Statistics (Future)

- **Endpoint**: `GET /api/stats/summary`
- **Response**: Summary statistics

### 3. Anomalies List (Future)

- **Endpoint**: `GET /api/anomalies`
- **Parameters**:
  - `threshold`: Z-score threshold (default: 3)
  - `limit`: Number of records (default: 100)
- **Response**: List of anomaly records

## Components Updated

### 1. StakesPayoutsChart.vue

- Now fetches real data from the API
- Displays stakes or payouts based on selected chart type
- Shows anomaly markers (red diamonds) for Z-scores > 3
- Displays upper bound threshold only (mean + 3σ) since stakes/payouts cannot be negative

### 2. Dashboard.vue

- Integrated API data fetching on mount
- Computes stats from real API responses
- Generates anomaly notifications from API data
- Creates anomaly table from combined stakes/payouts anomalies

## Configuration

### Environment Variables

Create a `.env` file in the dashboard root:

```env
VITE_API_BASE_URL=http://localhost:8000
```

For production, update this to your production API URL.

## Running the Application

### 1. Start the API Backend

```bash
cd gaming-api
uvicorn main:app --reload
```

The API will be available at <http://localhost:8000>

### 2. Start the Dashboard

```bash
cd gaming-dashboard
npm install
npm run dev
```

The dashboard will be available at <http://localhost:5173>

## Features Implemented

✅ Real-time stakes anomaly detection chart  
✅ Real-time payouts anomaly detection chart  
✅ Dynamic statistics from API data  
✅ Anomaly notifications sidebar  
✅ Anomaly data table with severity levels  
✅ Loading states and error handling  
✅ Responsive charts with Plotly.js

## Data Flow

1. **Dashboard loads** → Fetches stakes and payouts data in parallel
2. **Chart selection** → Renders appropriate chart with API data
3. **Anomaly detection** → API calculates Z-scores using global statistics
4. **Visualization** → Plotly renders interactive charts with anomaly markers
5. **Stats computation** → Dashboard derives statistics from API responses
6. **Table generation** → Combines stakes and payouts anomalies by timestamp

## API Data Structure

### Stakes/Payouts Response

```typescript
{
  chartType: 'stakes' | 'payouts',
  data: {
    timestamps: string[],
    values: number[],
    anomalies: Array<{
      x: string,
      y: number,
      index: number,
      zScore: number
    }>,
    bounds: {
      upper: number[],
      lower: number[],
      mean: number[]
    }
  },
  mean: number,
  std: number
}
```

### Turnover Response

```typescript
{
  timestamps: string[],
  turnover: number[],
  threshold: number,
  breachPoints: Array<{
    x: string,
    y: number
  }>
}
```

## Error Handling

- API connection failures display error messages in charts
- Loading states show spinners during data fetch
- Fallback values prevent crashes when data is unavailable

## Future Enhancements

- [ ] Real-time WebSocket updates for live data
- [ ] Configurable anomaly threshold in UI
- [ ] Export anomaly reports
- [ ] Historical data comparison
- [ ] Custom date range selection
- [ ] Alert configuration and notifications
