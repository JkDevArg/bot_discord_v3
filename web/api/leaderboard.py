"""
API endpoints for leaderboards
"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import List, Literal, Optional
from bot.database.connection import SessionLocal
from bot.database.models import User, Purchase, EventParticipant
from web.auth import get_current_user, AdminUser
from sqlalchemy import func, desc

router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    discord_id: int
    username: str
    discriminator: str
    value: int
    avatar_url: Optional[str] = None


@router.get("/points", response_model=List[LeaderboardEntry])
async def get_points_leaderboard(
    limit: int = Query(10, ge=1, le=100),
    current_user: AdminUser = Depends(get_current_user)
):
    """Get top users by points"""
    db = SessionLocal()
    try:
        users = db.query(User).filter(
            User.points > 0
        ).order_by(desc(User.points)).limit(limit).all()
        
        result = []
        for rank, user in enumerate(users, 1):
            result.append({
                "rank": rank,
                "user_id": user.id,
                "discord_id": user.discord_id,
                "username": user.username,
                "discriminator": user.discriminator,
                "value": user.points,
                "avatar_url": user.avatar_url
            })
        
        return result
    finally:
        db.close()


@router.get("/messages", response_model=List[LeaderboardEntry])
async def get_messages_leaderboard(
    limit: int = Query(10, ge=1, le=100),
    current_user: AdminUser = Depends(get_current_user)
):
    """Get top users by message count"""
    db = SessionLocal()
    try:
        users = db.query(User).filter(
            User.message_count > 0
        ).order_by(desc(User.message_count)).limit(limit).all()
        
        result = []
        for rank, user in enumerate(users, 1):
            result.append({
                "rank": rank,
                "user_id": user.id,
                "discord_id": user.discord_id,
                "username": user.username,
                "discriminator": user.discriminator,
                "value": user.message_count,
                "avatar_url": user.avatar_url
            })
        
        return result
    finally:
        db.close()


@router.get("/spending", response_model=List[LeaderboardEntry])
async def get_spending_leaderboard(
    limit: int = Query(10, ge=1, le=100),
    current_user: AdminUser = Depends(get_current_user)
):
    """Get top spenders in shop"""
    db = SessionLocal()
    try:
        # Get total spending per user
        spending = db.query(
            User.id,
            User.discord_id,
            User.username,
            User.discriminator,
            User.avatar_url,
            func.sum(Purchase.price_paid).label('total_spent')
        ).join(Purchase).group_by(
            User.id
        ).order_by(desc('total_spent')).limit(limit).all()
        
        result = []
        for rank, (user_id, discord_id, username, discriminator, avatar_url, total_spent) in enumerate(spending, 1):
            result.append({
                "rank": rank,
                "user_id": user_id,
                "discord_id": discord_id,
                "username": username,
                "discriminator": discriminator,
                "value": int(total_spent or 0),
                "avatar_url": avatar_url
            })
        
        return result
    finally:
        db.close()


@router.get("/events", response_model=List[LeaderboardEntry])
async def get_events_leaderboard(
    limit: int = Query(10, ge=1, le=100),
    current_user: AdminUser = Depends(get_current_user)
):
    """Get top event participants"""
    db = SessionLocal()
    try:
        # Get event participation count per user
        participation = db.query(
            User.id,
            User.discord_id,
            User.username,
            User.discriminator,
            User.avatar_url,
            func.count(EventParticipant.id).label('event_count')
        ).join(EventParticipant).filter(
            EventParticipant.reward_claimed == True
        ).group_by(
            User.id
        ).order_by(desc('event_count')).limit(limit).all()
        
        result = []
        for rank, (user_id, discord_id, username, discriminator, avatar_url, event_count) in enumerate(participation, 1):
            result.append({
                "rank": rank,
                "user_id": user_id,
                "discord_id": discord_id,
                "username": username,
                "discriminator": discriminator,
                "value": int(event_count or 0),
                "avatar_url": avatar_url
            })
        
        return result
    finally:
        db.close()


@router.get("/level", response_model=List[LeaderboardEntry])
async def get_level_leaderboard(
    limit: int = Query(10, ge=1, le=100),
    current_user: AdminUser = Depends(get_current_user)
):
    """Get top users by level"""
    db = SessionLocal()
    try:
        users = db.query(User).order_by(
            desc(User.level),
            desc(User.exp)
        ).limit(limit).all()
        
        result = []
        for rank, user in enumerate(users, 1):
            result.append({
                "rank": rank,
                "user_id": user.id,
                "discord_id": user.discord_id,
                "username": user.username,
                "discriminator": user.discriminator,
                "value": user.level,
                "avatar_url": user.avatar_url
            })
        
        return result
    finally:
        db.close()


@router.get("/weekly", response_model=List[LeaderboardEntry])
async def get_weekly_leaderboard(
    limit: int = Query(10, ge=1, le=100),
    current_user: AdminUser = Depends(get_current_user)
):
    """Get top users by points (last 7 days activity)"""
    from datetime import datetime, timedelta
    
    db = SessionLocal()
    try:
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        users = db.query(User).filter(
            User.last_activity >= week_ago
        ).order_by(desc(User.points)).limit(limit).all()
        
        result = []
        for rank, user in enumerate(users, 1):
            result.append({
                "rank": rank,
                "user_id": user.id,
                "discord_id": user.discord_id,
                "username": user.username,
                "discriminator": user.discriminator,
                "value": user.points,
                "avatar_url": user.avatar_url
            })
        
        return result
    finally:
        db.close()


@router.get("/monthly", response_model=List[LeaderboardEntry])
async def get_monthly_leaderboard(
    limit: int = Query(10, ge=1, le=100),
    current_user: AdminUser = Depends(get_current_user)
):
    """Get top users by points (last 30 days activity)"""
    from datetime import datetime, timedelta
    
    db = SessionLocal()
    try:
        month_ago = datetime.utcnow() - timedelta(days=30)
        
        users = db.query(User).filter(
            User.last_activity >= month_ago
        ).order_by(desc(User.points)).limit(limit).all()
        
        result = []
        for rank, user in enumerate(users, 1):
            result.append({
                "rank": rank,
                "user_id": user.id,
                "discord_id": user.discord_id,
                "username": user.username,
                "discriminator": user.discriminator,
                "value": user.points,
                "avatar_url": user.avatar_url
            })
        
        return result
    finally:
        db.close()


@router.get("/level-distribution")
async def get_level_distribution(current_user: AdminUser = Depends(get_current_user)):
    """Get distribution of users by level for chart"""
    db = SessionLocal()
    try:
        distribution = db.query(
            User.level,
            func.count(User.id).label('count')
        ).group_by(User.level).order_by(User.level.asc()).all()
        
        return [
            {"level": level, "count": count}
            for level, count in distribution
        ]
    finally:
        db.close()
