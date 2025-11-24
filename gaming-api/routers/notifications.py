from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from datetime import datetime
from models.schemas import NotificationResponse, NotificationListResponse
from database import get_db, Notification

router = APIRouter()

@router.get("/", response_model=NotificationListResponse)
async def get_notifications(
    unread_only: bool = Query(False, description="Filter for unread notifications only"),
    limit: int = Query(50, ge=1, le=200, description="Number of notifications to retrieve"),
    offset: int = Query(0, ge=0, description="Number of notifications to skip"),
    db: Session = Depends(get_db)
):
    """Get notifications with optional filtering for unread ones"""
    query = db.query(Notification)
    
    if unread_only:
        query = query.filter(Notification.is_read == False)
    
    total_count = query.count()
    unread_count = db.query(Notification).filter(Notification.is_read == False).count()
    
    notifications = query.order_by(desc(Notification.timestamp)).offset(offset).limit(limit).all()
    
    return NotificationListResponse(
        notifications=[
            NotificationResponse(
                id=n.id,
                timestamp=n.timestamp,
                anomaly_type=n.anomaly_type,
                severity=n.severity,
                value=n.value,
                z_score=n.z_score,
                message=n.message,
                is_read=n.is_read,
                created_at=n.created_at
            ) for n in notifications
        ],
        total=total_count,
        unread=unread_count,
        limit=limit,
        offset=offset
    )

@router.patch("/{notification_id}/read")
async def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db)
):
    """Mark a specific notification as read"""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    
    if not notification:
        return {"error": "Notification not found"}, 404
    
    notification.is_read = True
    db.commit()
    
    return {"status": "success", "id": notification_id, "is_read": True}

@router.patch("/mark-all-read")
async def mark_all_notifications_as_read(
    db: Session = Depends(get_db)
):
    """Mark all notifications as read"""
    count = db.query(Notification).filter(Notification.is_read == False).update({"is_read": True})
    db.commit()
    
    return {"status": "success", "marked_read": count}

@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    db: Session = Depends(get_db)
):
    """Delete a specific notification"""
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    
    if not notification:
        return {"error": "Notification not found"}, 404
    
    db.delete(notification)
    db.commit()
    
    return {"status": "success", "id": notification_id, "deleted": True}
