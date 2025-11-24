from celery_app import celery_app
from database import SessionLocal, RollingInterestingWithGlobalZ, Notification
from datetime import datetime, timedelta
from sqlalchemy import and_
import logging
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@celery_app.task(name='tasks.detect_anomalies_task')
def detect_anomalies_task():
    """
    Periodic task to detect anomalies and create notifications
    """
    logger.info("Starting anomaly detection task...")
    db = SessionLocal()
    try:
        # Get records from the last 10 minutes
        cutoff_time = datetime.utcnow() - timedelta(minutes=10)
        
        records = db.query(RollingInterestingWithGlobalZ).filter(
            and_(
                RollingInterestingWithGlobalZ.time >= cutoff_time,
                RollingInterestingWithGlobalZ.time.isnot(None)
            )
        ).all()
        
        notifications_created = 0
        
        for record in records:
            # Check for stake anomalies (Z-score > 3)
            if record.stake_global_z and abs(record.stake_global_z) > 3:
                # Check if notification already exists for this timestamp and type
                existing = db.query(Notification).filter(
                    and_(
                        Notification.timestamp == record.time,
                        Notification.anomaly_type == 'stakes'
                    )
                ).first()
                
                if not existing:
                    severity = 'critical' if abs(record.stake_global_z) > 4 else 'high' if abs(record.stake_global_z) > 3.5 else 'medium'
                    message = f"Unusual {'spike' if record.stake_global_z > 0 else 'drop'} in stakes detected"
                    
                    notification = Notification(
                        timestamp=record.time,
                        anomaly_type='stakes',
                        severity=severity,
                        value=record.stake,
                        z_score=record.stake_global_z,
                        message=message,
                        is_read=False
                    )
                    db.add(notification)
                    notifications_created += 1
            
            # Check for payout anomalies (Z-score > 3)
            if record.payout_global_z and abs(record.payout_global_z) > 3:
                # Check if notification already exists for this timestamp and type
                existing = db.query(Notification).filter(
                    and_(
                        Notification.timestamp == record.time,
                        Notification.anomaly_type == 'payouts'
                    )
                ).first()
                
                if not existing:
                    severity = 'critical' if abs(record.payout_global_z) > 4 else 'high' if abs(record.payout_global_z) > 3.5 else 'medium'
                    message = f"Abnormal {'pattern' if record.payout_global_z > 0 else 'drop'} in payouts detected"
                    
                    notification = Notification(
                        timestamp=record.time,
                        anomaly_type='payouts',
                        severity=severity,
                        value=record.payout,
                        z_score=record.payout_global_z,
                        message=message,
                        is_read=False
                    )
                    db.add(notification)
                    notifications_created += 1
        
        db.commit()
        logger.info(f"Anomaly detection completed. Created {notifications_created} new notifications from {len(records)} records.")
        return {"status": "success", "notifications_created": notifications_created, "records_scanned": len(records)}
        
    except Exception as e:
        db.rollback()
        error_msg = str(e) if str(e) else repr(e)
        error_trace = traceback.format_exc()
        logger.error(f"Error in anomaly detection task: {error_msg}")
        logger.error(f"Traceback: {error_trace}")
        return {"status": "error", "message": error_msg, "traceback": error_trace}
    finally:
        db.close()
        logger.info("Anomaly detection task completed.")
