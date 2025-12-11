# Gaming Fraud Detection API

A comprehensive FastAPI-based fraud detection system for gaming/lottery transactions.

## Features

- **Multi-Algorithm Anomaly Detection**: Uses Isolation Forest, One-Class SVM, DBSCAN, and Z-score methods
- **Time-Series Analysis**: Detects seasonal patterns, velocity anomalies, and temporal irregularities
- **Behavioral Pattern Detection**: Identifies unusual win rates, stake patterns, and gaming behaviors
- **Real-time Analytics**: Provides live monitoring and risk metrics
- **Government-Grade Security**: Designed for regulatory compliance and government oversight

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the API

```bash
uvicorn fraud_detection_api:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

- `GET /` - API status
- `GET /fraud/detect` - Run comprehensive fraud detection
- `GET /fraud/metrics` - Get real-time risk metrics
- `GET /fraud/operators/{operator_id}` - Get operator risk profile
- `GET /fraud/trends` - Get fraud trends over time

## Data Format

The system expects CSV data with the following key columns:
- `timestamp_end` - Transaction timestamp
- `operator_id` - Gaming operator identifier
- `stake_real_money` - Amount staked
- `payout_base_win` - Payout amount
- `GGR` - Gross Gaming Revenue
- `no_of_bets` - Number of bets
- `bets_won_cnt` - Number of winning bets

## Documentation

Access the interactive API documentation at `http://localhost:8000/docs`