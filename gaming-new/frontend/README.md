# Gaming Fraud Detection Dashboard

A modern React TypeScript dashboard for real-time gaming fraud detection and analytics.

## Features

- **Real-time Monitoring**: Live fraud detection with auto-refresh capabilities
- **Interactive Visualizations**: Charts and graphs using Recharts
- **Responsive Design**: Mobile-friendly interface using Tailwind CSS
- **Government-Grade UI**: Professional interface designed for regulatory oversight
- **Multi-Algorithm Detection**: Integration with backend fraud detection algorithms
- **Operator Analysis**: Detailed profiles and risk assessment for gaming operators

## Technology Stack

- **Frontend**: React 18 + TypeScript
- **Styling**: Tailwind CSS
- **Charts**: Recharts
- **Icons**: Lucide React
- **HTTP Client**: Fetch API
- **State Management**: React Context

## Installation

1. Navigate to the dashboard directory:
```bash
cd frontend/fraud-detection-dashboard
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
```bash
cp .env.development .env.local
# Edit .env.local with your API URL
```

## Development

Start the development server:
```bash
npm start
```

The dashboard will be available at `http://localhost:3000`

## Building for Production

```bash
npm run build
```

## Environment Variables

- `REACT_APP_API_BASE_URL`: Backend API base URL (default: http://localhost:8000)
- `REACT_APP_REFRESH_INTERVAL`: Auto-refresh interval in milliseconds
- `REACT_APP_APP_NAME`: Application name
- `REACT_APP_VERSION`: Application version

## Dashboard Features

### Overview Tab
- Key performance metrics cards
- Risk distribution pie chart
- Financial trends line chart

### Fraud Alerts Tab
- Real-time fraud alerts table
- Filtering by anomaly type
- Risk level indicators
- Export functionality

### Trends Analysis Tab
- Historical financial data
- Seasonal pattern analysis
- Performance trends

### Operator Profiles Tab
- Individual operator risk assessment
- Detailed financial metrics
- Risk indicator analysis

## API Integration

The dashboard integrates with the FastAPI backend through the following endpoints:

- `GET /fraud/detect` - Fraud detection results
- `GET /fraud/metrics` - Real-time risk metrics
- `GET /fraud/trends` - Historical trends
- `GET /fraud/operators/{id}` - Operator profiles

## Customization

The dashboard is built with modularity in mind. Each component is self-contained and can be easily customized:

- **Colors**: Edit `tailwind.config.js` for theme customization
- **Charts**: Modify chart components in `/src/components/`
- **API**: Update service functions in `/src/services/api.ts`
- **Styling**: Custom CSS in `/src/App.css`