"""
API endpoints for analytics and statistics
"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import List, Dict
from datetime import datetime, timedelta
from bot.database.connection import SessionLocal
from bot.database.models import User, Purchase, Event, EventParticipant
from web.auth import get_current_user, AdminUser
from sqlalchemy import func, and_, extract

router = APIRouter(prefix="/analytics", tags=["Analytics"])


class TimeSeriesData(BaseModel):
    date: str
    value: int


class AnalyticsResponse(BaseModel):
    user_growth: List[TimeSeriesData]
    points_distribution: List[TimeSeriesData]
    activity_by_day: List[Dict[str, int]]
    shop_revenue: List[TimeSeriesData]
    event_participation: List[TimeSeriesData]


@router.get("/overview", response_model=AnalyticsResponse)
async def get_analytics_overview(
    days: int = Query(30, ge=7, le=365),
    current_user: AdminUser = Depends(get_current_user)
):
    """Get analytics overview for the specified period"""
    db = SessionLocal()
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # User growth (new users per day)
        user_growth = db.query(
            func.date(User.created_at).label('date'),
            func.count(User.id).label('count')
        ).filter(
            User.created_at >= start_date
        ).group_by(
            func.date(User.created_at)
        ).all()
        
        user_growth_data = [
            {"date": str(date), "value": count}
            for date, count in user_growth
        ]
        
        # Points distribution (total points awarded per day)
        # This would require tracking point changes, for now we'll use message count as proxy
        activity_data = db.query(
            func.date(User.last_activity).label('date'),
            func.sum(User.message_count).label('messages')
        ).filter(
            User.last_activity >= start_date
        ).group_by(
            func.date(User.last_activity)
        ).all()
        
        points_dist_data = [
            {"date": str(date), "value": int(messages * 10)}  # Assuming 10 points per message
            for date, messages in activity_data
        ]
        
        # Activity by day of week
        activity_by_day = db.query(
            extract('dow', User.last_activity).label('day'),
            func.count(User.id).label('count')
        ).filter(
            User.last_activity >= start_date
        ).group_by('day').all()
        
        day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        activity_by_day_data = [
            {day_names[int(day)]: count}
            for day, count in activity_by_day
        ]
        
        # Shop revenue (purchases per day)
        shop_revenue = db.query(
            func.date(Purchase.purchased_at).label('date'),
            func.sum(Purchase.price_paid).label('revenue')
        ).filter(
            Purchase.purchased_at >= start_date
        ).group_by(
            func.date(Purchase.purchased_at)
        ).all()
        
        shop_revenue_data = [
            {"date": str(date), "value": int(revenue)}
            for date, revenue in shop_revenue
        ]
        
        # Event participation (participants per event)
        event_participation = db.query(
            Event.name.label('event'),
            func.count(EventParticipant.id).label('participants')
        ).join(EventParticipant).filter(
            Event.created_at >= start_date
        ).group_by(Event.name).all()
        
        event_participation_data = [
            {"date": event, "value": participants}
            for event, participants in event_participation
        ]
        
        return {
            "user_growth": user_growth_data,
            "points_distribution": points_dist_data,
            "activity_by_day": activity_by_day_data,
            "shop_revenue": shop_revenue_data,
            "event_participation": event_participation_data
        }
    finally:
        db.close()


@router.get("/top-contributors")
async def get_top_contributors(
    limit: int = Query(10, ge=1, le=50),
    current_user: AdminUser = Depends(get_current_user)
):
    """Get top contributors by various metrics"""
    db = SessionLocal()
    try:
        # Top by messages
        top_messages = db.query(User).order_by(
            User.message_count.desc()
        ).limit(limit).all()
        
        # Top by points
        top_points = db.query(User).order_by(
            User.points.desc()
        ).limit(limit).all()
        
        # Top by purchases
        top_spenders = db.query(
            User,
            func.count(Purchase.id).label('purchase_count')
        ).join(Purchase).group_by(User.id).order_by(
            func.count(Purchase.id).desc()
        ).limit(limit).all()
        
        return {
            "top_messages": [
                {"username": u.username, "value": u.message_count}
                for u in top_messages
            ],
            "top_points": [
                {"username": u.username, "value": u.points}
                for u in top_points
            ],
            "top_spenders": [
                {"username": u.username, "value": count}
                for u, count in top_spenders
            ]
        }
    finally:
        db.close()
