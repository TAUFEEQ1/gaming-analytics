from fastapi import APIRouter, Query, Depends
from datetime import datetime, timedelta
from typing import List, Literal
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
import math
from models.schemas import StakesPayoutsChartResponse, ChartData
from database import get_db, RollingInterestingWithGlobalZ, InterestingData

router = APIRouter()

def calculate_stats(data: List[float]):
    """Calculate mean and standard deviation"""
    if not data:
        return 0, 0
    mean = sum(data) / len(data)
    variance = sum((x - mean) ** 2 for x in data) / len(data)
    std = math.sqrt(variance)
    return mean, std

@router.get("/stakes-payouts/{chart_type}", response_model=StakesPayoutsChartResponse)
async def get_stakes_payouts_chart(
    chart_type: Literal['stakes', 'payouts'],
    start_date: str = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(None, description="End date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Get stakes or payouts chart data with anomaly detection from database"""
    # Build query with optional date filters
    query = db.query(RollingInterestingWithGlobalZ).filter(
        RollingInterestingWithGlobalZ.time.isnot(None)
    )
    
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(RollingInterestingWithGlobalZ.time >= start_dt)
        except ValueError:
            pass  # Ignore invalid date format
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(RollingInterestingWithGlobalZ.time < end_dt)
        except ValueError:
            pass  # Ignore invalid date format
    
    records = query.order_by(RollingInterestingWithGlobalZ.time).all()
    
    if not records:
        return StakesPayoutsChartResponse(
            chartType=chart_type,
            data=ChartData(
                timestamps=[],
                values=[],
                anomalies=[],
                bounds={"upper": [], "lower": [], "mean": []}
            ),
            mean=0,
            std=0
        )
    
    timestamps = [r.time for r in records]
    stakes = [r.stake for r in records]
    payouts = [r.payout for r in records]
    
    # Select data based on chart type
    if chart_type == 'stakes':
        values = stakes
        z_scores = [r.stake_global_z for r in records]
        mean = records[0].stake_global_mean if records else 0
        std = records[0].stake_global_std if records else 0
    else:
        values = payouts
        z_scores = [r.payout_global_z for r in records]
        mean = records[0].payout_global_mean if records else 0
        std = records[0].payout_global_std if records else 0
    
    upper_bound = mean + 3 * std
    lower_bound = mean - 3 * std
    
    # Detect anomalies (z-score > 3 or < -3)
    anomalies = []
    for i, (ts, val, z) in enumerate(zip(timestamps, values, z_scores)):
        if abs(z) > 3:
            anomalies.append({
                "x": ts,
                "y": round(val, 2),
                "index": i,
                "zScore": round(z, 2)
            })
    
    chart_data = ChartData(
        timestamps=timestamps,
        values=[round(v, 2) for v in values],
        anomalies=anomalies,
        bounds={
            "upper": [round(upper_bound, 2)] * len(timestamps),
            "lower": [round(lower_bound, 2)] * len(timestamps),
            "mean": [round(mean, 2)] * len(timestamps)
        }
    )
    
    return StakesPayoutsChartResponse(
        chartType=chart_type,
        data=chart_data,
        mean=round(mean, 2),
        std=round(std, 2)
    )


