from fastapi import APIRouter, Query, Depends
from datetime import datetime, timedelta
from typing import List, Literal
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, and_
from pydantic import BaseModel
from database import get_db, RollingInterestingWithDBSCAN, OnlineCasino

router = APIRouter()

# Pydantic Models for Composite Metrics
class CompositeMetricsPoint(BaseModel):
    round: int
    time: datetime
    stake: float
    payout: float
    houseNet: float
    stakeZScore: float
    payoutZScore: float
    houseNetZScore: float
    dbAnomaly: int
    dbCluster: int

class CompositeChartData(BaseModel):
    timestamps: List[datetime]
    rounds: List[int]
    stakeZScores: List[float]
    payoutZScores: List[float]
    houseNetZScores: List[float]
    dbAnomalies: List[int]
    anomalyIndices: List[int]

class DBSCANAnomalyNotification(BaseModel):
    id: int
    type: str
    severity: Literal['critical', 'high', 'medium', 'low']
    timestamp: datetime
    metrics: dict
    message: str

class DBSCANTableRecord(BaseModel):
    id: int
    round: int
    time: datetime
    stake: float
    payout: float
    houseNet: float
    stakeZScore: float
    payoutZScore: float
    houseNetZScore: float
    dbAnomaly: int
    dbCluster: int
    severity: str
    gamers: int = 0
    skins: int = 0

class CompositeStats(BaseModel):
    dbscanAnomalies: int
    avgHouseNet: float
    totalRounds: int
    normalPoints: int
    clusterCount: int

@router.get("/chart-data", response_model=CompositeChartData)
async def get_composite_chart_data(
    limit: int = Query(100, ge=10, le=10000, description="Number of records to retrieve"),
    start_date: datetime | None = Query(None, description="Start date filter (ISO format)"),
    end_date: datetime | None = Query(None, description="End date filter (ISO format)"),
    db: Session = Depends(get_db)
):
    """Get composite metrics chart data with DBSCAN anomalies"""
    # Query data from database
    query = db.query(RollingInterestingWithDBSCAN)
    
    # Apply date filters
    if start_date:
        query = query.filter(RollingInterestingWithDBSCAN.time >= start_date)
    if end_date:
        query = query.filter(RollingInterestingWithDBSCAN.time <= end_date)
    
    # If date filters are applied, don't limit results (or use a much higher limit)
    # Otherwise use the limit parameter
    if start_date or end_date:
        records = query.order_by(RollingInterestingWithDBSCAN.time.asc()).all()
    else:
        records = query.order_by(RollingInterestingWithDBSCAN.time.desc()).limit(limit).all()
        # Reverse to get chronological order
        records = list(reversed(records))
    
    if not records:
        return CompositeChartData(
            timestamps=[], rounds=[], stakeZScores=[], payoutZScores=[], 
            houseNetZScores=[], dbAnomalies=[], anomalyIndices=[]
        )
    
    timestamps = [r.time for r in records]
    rounds = [r.ID for r in records]
    stake_z_scores = [round(r.stake_global_z, 2) if r.stake_global_z else 0 for r in records]
    payout_z_scores = [round(r.payout_global_z, 2) if r.payout_global_z else 0 for r in records]
    house_net_z_scores = [round(r.house_net_global_z, 2) if r.house_net_global_z else 0 for r in records]
    db_anomalies = [r.db_anomaly for r in records]
    
    # Get indices of DBSCAN anomalies
    anomaly_indices = [i for i, r in enumerate(records) if r.db_anomaly == 1]
    
    return CompositeChartData(
        timestamps=timestamps,
        rounds=rounds,
        stakeZScores=stake_z_scores,
        payoutZScores=payout_z_scores,
        houseNetZScores=house_net_z_scores,
        dbAnomalies=db_anomalies,
        anomalyIndices=anomaly_indices
    )

@router.get("/notifications", response_model=List[DBSCANAnomalyNotification])
async def get_dbscan_notifications(
    limit: int = Query(5, ge=1, le=50, description="Number of notifications to return"),
    start_date: datetime | None = Query(None, description="Start date filter (ISO format)"),
    end_date: datetime | None = Query(None, description="End date filter (ISO format)"),
    db: Session = Depends(get_db)
):
    """Get recent DBSCAN anomaly notifications"""
    # Query DBSCAN anomalies
    query = db.query(RollingInterestingWithDBSCAN).filter(
        RollingInterestingWithDBSCAN.db_anomaly == 1
    )
    
    # Apply date filters
    if start_date:
        query = query.filter(RollingInterestingWithDBSCAN.time >= start_date)
    if end_date:
        query = query.filter(RollingInterestingWithDBSCAN.time <= end_date)
    
    anomalies = query.order_by(RollingInterestingWithDBSCAN.time.desc()).limit(limit).all()
    
    notifications = []
    for i, anomaly in enumerate(anomalies):
        # Calculate severity based on combined z-scores
        z_scores = [
            abs(anomaly.stake_global_z) if anomaly.stake_global_z else 0,
            abs(anomaly.payout_global_z) if anomaly.payout_global_z else 0,
            abs(anomaly.house_net_global_z) if anomaly.house_net_global_z else 0
        ]
        max_z = max(z_scores)
        avg_z = sum(z_scores) / len(z_scores)
        
        if max_z >= 5 or avg_z >= 3.5:
            severity = 'critical'
        elif max_z >= 4 or avg_z >= 3:
            severity = 'high'
        elif max_z >= 3 or avg_z >= 2.5:
            severity = 'medium'
        else:
            severity = 'low'
        
        # Generate descriptive message
        message = 'Multi-variate anomaly cluster detected'
        if abs(anomaly.house_net_global_z or 0) > 3:
            if (anomaly.house_net_global_z or 0) > 0:
                message = 'Unusual house profit pattern detected'
            else:
                message = 'Unusual house loss pattern detected'
        
        notifications.append(DBSCANAnomalyNotification(
            id=i + 1,
            type='multivariate',
            severity=severity,
            timestamp=anomaly.time,
            metrics={
                'stakeZScore': round(anomaly.stake_global_z, 1) if anomaly.stake_global_z else 0,
                'payoutZScore': round(anomaly.payout_global_z, 1) if anomaly.payout_global_z else 0,
                'houseNetZScore': round(anomaly.house_net_global_z, 1) if anomaly.house_net_global_z else 0
            },
            message=message
        ))
    
    return notifications

@router.get("/table", response_model=List[DBSCANTableRecord])
async def get_dbscan_table(
    limit: int = Query(20, ge=1, le=100, description="Number of records to return"),
    show_anomalies_only: bool = Query(False, description="Show only DBSCAN anomalies"),
    start_date: datetime | None = Query(None, description="Start date filter (ISO format)"),
    end_date: datetime | None = Query(None, description="End date filter (ISO format)"),
    db: Session = Depends(get_db)
):
    """Get DBSCAN anomaly table data"""
    # Build query
    query = db.query(
        RollingInterestingWithDBSCAN,
        OnlineCasino
    ).outerjoin(
        OnlineCasino,
        RollingInterestingWithDBSCAN.ID == OnlineCasino.ID
    )
    
    if show_anomalies_only:
        query = query.filter(RollingInterestingWithDBSCAN.db_anomaly == 1)
    
    # Apply date filters
    if start_date:
        query = query.filter(RollingInterestingWithDBSCAN.time >= start_date)
    if end_date:
        query = query.filter(RollingInterestingWithDBSCAN.time <= end_date)
    
    query = query.order_by(RollingInterestingWithDBSCAN.time.desc())
    results = query.limit(limit).all()
    
    records = []
    for dbscan_record, casino_record in results:
        # Calculate severity
        if dbscan_record.db_anomaly == 1:
            # For DBSCAN anomalies, determine severity based on z-scores
            z_scores = [
                abs(dbscan_record.stake_global_z) if dbscan_record.stake_global_z else 0,
                abs(dbscan_record.payout_global_z) if dbscan_record.payout_global_z else 0,
                abs(dbscan_record.house_net_global_z) if dbscan_record.house_net_global_z else 0
            ]
            max_z = max(z_scores)
            
            if max_z >= 5:
                severity = 'critical'
            elif max_z >= 4:
                severity = 'high'
            elif max_z >= 3:
                severity = 'medium'
            else:
                severity = 'low'
        else:
            severity = 'normal'
        
        records.append(DBSCANTableRecord(
            id=dbscan_record.ID,
            round=dbscan_record.ID,
            time=dbscan_record.time,
            stake=round(dbscan_record.stake, 2),
            payout=round(dbscan_record.payout, 2),
            houseNet=round(dbscan_record.house_net, 2),
            stakeZScore=round(dbscan_record.stake_global_z, 2) if dbscan_record.stake_global_z else 0,
            payoutZScore=round(dbscan_record.payout_global_z, 2) if dbscan_record.payout_global_z else 0,
            houseNetZScore=round(dbscan_record.house_net_global_z, 2) if dbscan_record.house_net_global_z else 0,
            dbAnomaly=dbscan_record.db_anomaly,
            dbCluster=dbscan_record.db_cluster if dbscan_record.db_cluster else 0,
            severity=severity,
            gamers=casino_record.gamers if casino_record else 0,
            skins=casino_record.skins if casino_record else 0
        ))
    
    return records

@router.get("/stats", response_model=CompositeStats)
async def get_composite_stats(
    start_date: datetime | None = Query(None, description="Start date filter (ISO format)"),
    end_date: datetime | None = Query(None, description="End date filter (ISO format)"),
    db: Session = Depends(get_db)
):
    """Get composite metrics statistics"""
    # Base query with date filters
    base_query = db.query(RollingInterestingWithDBSCAN)
    if start_date:
        base_query = base_query.filter(RollingInterestingWithDBSCAN.time >= start_date)
    if end_date:
        base_query = base_query.filter(RollingInterestingWithDBSCAN.time <= end_date)
    
    # Count DBSCAN anomalies
    dbscan_anomalies = base_query.filter(
        RollingInterestingWithDBSCAN.db_anomaly == 1
    ).count() or 0
    
    # Calculate average house net
    avg_house_net = db.query(func.avg(RollingInterestingWithDBSCAN.house_net))
    if start_date:
        avg_house_net = avg_house_net.filter(RollingInterestingWithDBSCAN.time >= start_date)
    if end_date:
        avg_house_net = avg_house_net.filter(RollingInterestingWithDBSCAN.time <= end_date)
    avg_house_net = avg_house_net.scalar() or 0
    
    # Total rounds
    total_rounds = base_query.count() or 0
    
    # Normal points (not anomalies)
    normal_points = base_query.filter(
        RollingInterestingWithDBSCAN.db_anomaly == 0
    ).count() or 0
    
    # Count distinct clusters (excluding -1 which represents anomalies in DBSCAN)
    cluster_query = db.query(func.count(func.distinct(RollingInterestingWithDBSCAN.db_cluster))).filter(
        RollingInterestingWithDBSCAN.db_cluster >= 0
    )
    if start_date:
        cluster_query = cluster_query.filter(RollingInterestingWithDBSCAN.time >= start_date)
    if end_date:
        cluster_query = cluster_query.filter(RollingInterestingWithDBSCAN.time <= end_date)
    cluster_count = cluster_query.scalar() or 0
    
    return CompositeStats(
        dbscanAnomalies=dbscan_anomalies,
        avgHouseNet=round(avg_house_net, 2),
        totalRounds=total_rounds,
        normalPoints=normal_points,
        clusterCount=cluster_count
    )

@router.get("/anomaly-count")
async def get_dbscan_anomaly_count(
    hours: int = Query(24, ge=1, le=168, description="Time period in hours"),
    db: Session = Depends(get_db)
):
    """Get count of DBSCAN anomalies in the specified time period"""
    cutoff_time = datetime.now() - timedelta(hours=hours)
    
    # Count DBSCAN anomalies
    total_count = db.query(func.count(RollingInterestingWithDBSCAN.ID)).filter(
        and_(
            RollingInterestingWithDBSCAN.time >= cutoff_time,
            RollingInterestingWithDBSCAN.db_anomaly == 1
        )
    ).scalar() or 0
    
    # Count by severity based on max z-score
    anomalies = db.query(
        RollingInterestingWithDBSCAN.stake_global_z,
        RollingInterestingWithDBSCAN.payout_global_z,
        RollingInterestingWithDBSCAN.house_net_global_z
    ).filter(
        and_(
            RollingInterestingWithDBSCAN.time >= cutoff_time,
            RollingInterestingWithDBSCAN.db_anomaly == 1
        )
    ).all()
    
    critical_count = 0
    high_count = 0
    medium_count = 0
    low_count = 0
    
    for stake_z, payout_z, house_z in anomalies:
        max_z = max(abs(stake_z or 0), abs(payout_z or 0), abs(house_z or 0))
        if max_z >= 5:
            critical_count += 1
        elif max_z >= 4:
            high_count += 1
        elif max_z >= 3:
            medium_count += 1
        else:
            low_count += 1
    
    return {
        "total": total_count,
        "critical": critical_count,
        "high": high_count,
        "medium": medium_count,
        "low": low_count,
        "period_hours": hours
    }
