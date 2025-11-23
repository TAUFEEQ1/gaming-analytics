from fastapi import APIRouter, Query, Depends
from datetime import datetime, timedelta
from typing import List, Literal
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, func
from models.schemas import AnomalyNotification, AnomalyTableRecord
from database import get_db, RollingInterestingWithGlobalZ, OnlineCasino

router = APIRouter()

@router.get("/notifications", response_model=List[AnomalyNotification])
async def get_anomaly_notifications(
    limit: int = Query(5, ge=1, le=50, description="Number of notifications to return"),
    db: Session = Depends(get_db)
):
    """Get recent anomaly notifications from database"""
    # Query anomalies with z-score > 3 or < -3
    anomalies = db.query(RollingInterestingWithGlobalZ).filter(
        or_(
            RollingInterestingWithGlobalZ.stake_global_z > 3,
            RollingInterestingWithGlobalZ.stake_global_z < -3,
            RollingInterestingWithGlobalZ.payout_global_z > 3,
            RollingInterestingWithGlobalZ.payout_global_z < -3
        )
    ).order_by(RollingInterestingWithGlobalZ.time.desc()).limit(limit).all()
    
    notifications = []
    for i, anomaly in enumerate(anomalies):
        # Determine if it's a stake or payout anomaly (prioritize the larger z-score)
        stake_z_abs = abs(anomaly.stake_global_z) if anomaly.stake_global_z else 0
        payout_z_abs = abs(anomaly.payout_global_z) if anomaly.payout_global_z else 0
        
        if stake_z_abs > payout_z_abs:
            anomaly_type = 'stakes'
            z_score = anomaly.stake_global_z
            value = anomaly.stake
            normal_range = f"{anomaly.stake_global_mean - anomaly.stake_global_std:.0f}-{anomaly.stake_global_mean + anomaly.stake_global_std:.0f}"
            message = 'Unusual spike detected' if z_score > 0 else 'Unusual drop in stakes'
        else:
            anomaly_type = 'payouts'
            z_score = anomaly.payout_global_z
            value = anomaly.payout
            normal_range = f"{anomaly.payout_global_mean - anomaly.payout_global_std:.0f}-{anomaly.payout_global_mean + anomaly.payout_global_std:.0f}"
            message = 'Spike in payout amount' if z_score > 0 else 'Unusual payout drop'
        
        # Determine severity based on z-score
        z_abs = abs(z_score)
        if z_abs >= 5:
            severity = 'critical'
        elif z_abs >= 4:
            severity = 'high'
        elif z_abs >= 3:
            severity = 'medium'
        else:
            severity = 'low'
        
        notifications.append(AnomalyNotification(
            id=i + 1,
            type=anomaly_type,
            severity=severity,
            timestamp=anomaly.time,
            value=round(value, 2),
            normalRange=normal_range,
            zScore=round(z_score, 1),
            message=message
        ))
    
    return notifications

@router.get("/table", response_model=List[AnomalyTableRecord])
async def get_anomaly_table(
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    severity: Literal['all', 'critical', 'high', 'medium', 'low'] = Query('all', description="Filter by severity"),
    db: Session = Depends(get_db)
):
    """Get anomaly table data from database"""
    # Join anomaly data with casino data
    query = db.query(
        RollingInterestingWithGlobalZ,
        OnlineCasino
    ).join(
        OnlineCasino,
        RollingInterestingWithGlobalZ.ID == OnlineCasino.ID
    ).filter(
        or_(
            RollingInterestingWithGlobalZ.stake_global_z > 3,
            RollingInterestingWithGlobalZ.stake_global_z < -3,
            RollingInterestingWithGlobalZ.payout_global_z > 3,
            RollingInterestingWithGlobalZ.payout_global_z < -3
        )
    ).order_by(RollingInterestingWithGlobalZ.time.desc())
    
    results = query.limit(limit).all()
    
    records = []
    for i, (anomaly, casino) in enumerate(results):
        # Determine anomaly type and severity
        stake_z_abs = abs(anomaly.stake_global_z) if anomaly.stake_global_z else 0
        payout_z_abs = abs(anomaly.payout_global_z) if anomaly.payout_global_z else 0
        
        if stake_z_abs > payout_z_abs:
            anomaly_type = 'stake'
            z_abs = stake_z_abs
        else:
            anomaly_type = 'payout'
            z_abs = payout_z_abs
        
        # Determine severity
        if z_abs >= 5:
            record_severity = 'critical'
        elif z_abs >= 4:
            record_severity = 'high'
        elif z_abs >= 3:
            record_severity = 'medium'
        else:
            record_severity = 'low'
        
        # Apply severity filter
        if severity != 'all' and record_severity != severity:
            continue
        
        records.append(AnomalyTableRecord(
            id=anomaly.ID,
            time=anomaly.time,
            stake=round(anomaly.stake, 2),
            gamers=casino.gamers,
            skins=casino.skins,
            payout=round(anomaly.payout, 2),
            peopleWin=int(casino.peopleWin),
            peopleLost=int(casino.peopleLost),
            anomalyType=anomaly_type,
            severity=record_severity
        ))
    
    return records

@router.get("/count")
async def get_anomaly_count(
    hours: int = Query(24, ge=1, le=168, description="Time period in hours"),
    db: Session = Depends(get_db)
):
    """Get count of anomalies in the specified time period"""
    cutoff_time = datetime.now() - timedelta(hours=hours)
    
    # Count total anomalies
    total_count = db.query(func.count(RollingInterestingWithGlobalZ.ID)).filter(
        and_(
            RollingInterestingWithGlobalZ.time >= cutoff_time,
            or_(
                RollingInterestingWithGlobalZ.stake_global_z > 3,
                RollingInterestingWithGlobalZ.stake_global_z < -3,
                RollingInterestingWithGlobalZ.payout_global_z > 3,
                RollingInterestingWithGlobalZ.payout_global_z < -3
            )
        )
    ).scalar() or 0
    
    # Count stakes anomalies
    stakes_count = db.query(func.count(RollingInterestingWithGlobalZ.ID)).filter(
        and_(
            RollingInterestingWithGlobalZ.time >= cutoff_time,
            or_(
                RollingInterestingWithGlobalZ.stake_global_z > 3,
                RollingInterestingWithGlobalZ.stake_global_z < -3
            )
        )
    ).scalar() or 0
    
    # Count payouts anomalies
    payouts_count = db.query(func.count(RollingInterestingWithGlobalZ.ID)).filter(
        and_(
            RollingInterestingWithGlobalZ.time >= cutoff_time,
            or_(
                RollingInterestingWithGlobalZ.payout_global_z > 3,
                RollingInterestingWithGlobalZ.payout_global_z < -3
            )
        )
    ).scalar() or 0
    
    # Count by severity (based on z-score ranges)
    critical_count = db.query(func.count(RollingInterestingWithGlobalZ.ID)).filter(
        and_(
            RollingInterestingWithGlobalZ.time >= cutoff_time,
            or_(
                RollingInterestingWithGlobalZ.stake_global_z >= 5,
                RollingInterestingWithGlobalZ.stake_global_z <= -5,
                RollingInterestingWithGlobalZ.payout_global_z >= 5,
                RollingInterestingWithGlobalZ.payout_global_z <= -5
            )
        )
    ).scalar() or 0
    
    high_count = db.query(func.count(RollingInterestingWithGlobalZ.ID)).filter(
        and_(
            RollingInterestingWithGlobalZ.time >= cutoff_time,
            or_(
                and_(RollingInterestingWithGlobalZ.stake_global_z >= 4, RollingInterestingWithGlobalZ.stake_global_z < 5),
                and_(RollingInterestingWithGlobalZ.stake_global_z <= -4, RollingInterestingWithGlobalZ.stake_global_z > -5),
                and_(RollingInterestingWithGlobalZ.payout_global_z >= 4, RollingInterestingWithGlobalZ.payout_global_z < 5),
                and_(RollingInterestingWithGlobalZ.payout_global_z <= -4, RollingInterestingWithGlobalZ.payout_global_z > -5)
            )
        )
    ).scalar() or 0
    
    medium_count = total_count - critical_count - high_count
    
    return {
        "total": total_count,
        "stakes": stakes_count,
        "payouts": payouts_count,
        "critical": critical_count,
        "high": high_count,
        "medium": medium_count,
        "low": 0,
        "period_hours": hours
    }
