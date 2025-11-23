from fastapi import APIRouter, Query, Depends
from datetime import datetime, timedelta
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from models.schemas import StatCard, DashboardSummary
from database import get_db, RollingInterestingWithGlobalZ, OnlineCasino
from routers.anomalies import get_anomaly_notifications

router = APIRouter()

@router.get("/cards", response_model=List[StatCard])
async def get_stat_cards(db: Session = Depends(get_db)):
    """Get dashboard stat cards from database"""
    # Count stakes anomalies
    stakes_anomalies = db.query(func.count(RollingInterestingWithGlobalZ.ID)).filter(
        or_(
            RollingInterestingWithGlobalZ.stake_global_z > 3,
            RollingInterestingWithGlobalZ.stake_global_z < -3
        )
    ).scalar() or 0
    
    # Count payout anomalies
    payout_anomalies = db.query(func.count(RollingInterestingWithGlobalZ.ID)).filter(
        or_(
            RollingInterestingWithGlobalZ.payout_global_z > 3,
            RollingInterestingWithGlobalZ.payout_global_z < -3
        )
    ).scalar() or 0
    
    # Count total rounds
    total_rounds = db.query(func.count(OnlineCasino.ID)).scalar() or 0
    
    # Calculate average stake
    avg_stake = db.query(func.avg(RollingInterestingWithGlobalZ.stake)).scalar() or 0
    
    return [
        StatCard(
            title="Stakes Anomalies",
            value=str(stakes_anomalies),
            subtitle="Z-score > 3 detected",
            trend="up",
            icon="pi-exclamation-triangle"
        ),
        StatCard(
            title="Payout Anomalies",
            value=str(payout_anomalies),
            subtitle="Unusual payout patterns",
            trend="up",
            icon="pi-exclamation-circle"
        ),
        StatCard(
            title="Total Rounds",
            value=f"{total_rounds:,}",
            subtitle="Casino rounds analyzed",
            trend="up",
            icon="pi-chart-line"
        ),
        StatCard(
            title="Average Stake",
            value=f"${avg_stake:.2f}",
            subtitle="Per round average",
            trend="up",
            icon="pi-dollar"
        )
    ]

@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    notification_limit: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """Get complete dashboard summary"""
    stats = await get_stat_cards(db)
    notifications = await get_anomaly_notifications(notification_limit, db)
    
    return DashboardSummary(
        stats=stats,
        recentAnomalies=notifications,
        totalAnomalies=len(notifications),
        lastUpdated=datetime.now()
    )

@router.get("/metrics")
async def get_current_metrics(db: Session = Depends(get_db)):
    """Get current system metrics from database"""
    # Get latest data point
    latest_casino = db.query(OnlineCasino).order_by(OnlineCasino.time.desc()).first()
    latest_interesting = db.query(RollingInterestingWithGlobalZ).order_by(
        RollingInterestingWithGlobalZ.time.desc()
    ).first()
    
    # Count active alerts (recent anomalies in last hour)
    one_hour_ago = datetime.now() - timedelta(hours=1)
    active_alerts = db.query(func.count(RollingInterestingWithGlobalZ.ID)).filter(
        RollingInterestingWithGlobalZ.time >= one_hour_ago,
        or_(
            RollingInterestingWithGlobalZ.stake_global_z > 3,
            RollingInterestingWithGlobalZ.stake_global_z < -3,
            RollingInterestingWithGlobalZ.payout_global_z > 3,
            RollingInterestingWithGlobalZ.payout_global_z < -3
        )
    ).scalar() or 0
    
    # Calculate average stake and payout from recent data
    recent_data = db.query(
        func.avg(RollingInterestingWithGlobalZ.stake).label('avg_stake'),
        func.avg(RollingInterestingWithGlobalZ.payout).label('avg_payout')
    ).filter(
        RollingInterestingWithGlobalZ.time >= one_hour_ago
    ).first()
    
    return {
        "activeRounds": latest_casino.gamers if latest_casino else 0,
        "activeGamers": latest_casino.gamers if latest_casino else 0,
        "currentStakeAvg": round(recent_data.avg_stake, 2) if recent_data and recent_data.avg_stake else 0,
        "currentPayoutAvg": round(recent_data.avg_payout, 2) if recent_data and recent_data.avg_payout else 0,
        "systemLoad": 0.5,  # Could be calculated based on data volume
        "alertsActive": active_alerts,
        "timestamp": datetime.now()
    }
