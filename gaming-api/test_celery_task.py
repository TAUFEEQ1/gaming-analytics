#!/usr/bin/env python
"""
Test script to manually run anomaly detection on historical data
This bypasses the 10-minute window to test with the actual 2021 data
"""
from database import SessionLocal, RollingInterestingWithGlobalZ, Notification
from sqlalchemy import and_
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_anomaly_detection():
    """
    Test anomaly detection on all historical data
    """
    logger.info("Starting anomaly detection test on historical data...")
    db = SessionLocal()
    try:
        # Get all records with high Z-scores
        records = db.query(RollingInterestingWithGlobalZ).filter(
            RollingInterestingWithGlobalZ.time.isnot(None)
        ).all()
        
        logger.info(f"Found {len(records)} total records")
        
        notifications_created = 0
        stake_anomalies = 0
        payout_anomalies = 0
        
        for record in records:
            # Check for stake anomalies (Z-score > 3)
            if record.stake_global_z and abs(record.stake_global_z) > 3:
                stake_anomalies += 1
                # Check if notification already exists for this timestamp and type
                existing = db.query(Notification).filter(
                    and_(
                        Notification.timestamp == record.time,
                        Notification.anomaly_type == 'stake'
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
                payout_anomalies += 1
                # Check if notification already exists for this timestamp and type
                existing = db.query(Notification).filter(
                    and_(
                        Notification.timestamp == record.time,
                        Notification.anomaly_type == 'payout'
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
        logger.info(f"✓ Test completed successfully!")
        logger.info(f"  - Total records scanned: {len(records)}")
        logger.info(f"  - Stake anomalies found: {stake_anomalies}")
        logger.info(f"  - Payout anomalies found: {payout_anomalies}")
        logger.info(f"  - New notifications created: {notifications_created}")
        return {"status": "success", "notifications_created": notifications_created, "records_scanned": len(records)}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error in anomaly detection test: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()


if __name__ == "__main__":
    result = test_anomaly_detection()
    print(f"\nFinal Result: {result}")
