"""
API endpoints para sistema de recompensas diarias
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime
from bot.database.connection import SessionLocal
from bot.database.models import User, DailyReward
from web.auth import get_current_user, AdminUser
from sqlalchemy import func, desc

router = APIRouter(prefix="/rewards", tags=["Rewards"])


class RewardStatsResponse(BaseModel):
    total_claims_today: int
    total_active_streaks: int
    longest_streak: int
    longest_streak_user: str
    total_points_distributed: int


class TopStreakUser(BaseModel):
    username: str
    discord_id: int
    streak_days: int
    best_streak: int
    total_claims: int


@router.get("/stats", response_model=RewardStatsResponse)
async def get_reward_stats(current_user: AdminUser = Depends(get_current_user)):
    """Obtener estadísticas generales de recompensas diarias"""
    db = SessionLocal()
    try:
        # Claims de hoy (últimas 24 horas)
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        total_claims_today = db.query(DailyReward).filter(
            DailyReward.last_claim >= today_start
        ).count()
        
        # Streaks activos (reclamaron en las últimas 48 horas)
        from datetime import timedelta
        active_threshold = datetime.utcnow() - timedelta(hours=48)
        total_active_streaks = db.query(DailyReward).filter(
            DailyReward.last_claim >= active_threshold,
            DailyReward.streak_days > 0
        ).count()
        
        # Streak más largo actual
        longest_streak_record = db.query(DailyReward, User).join(User).filter(
            DailyReward.last_claim >= active_threshold
        ).order_by(desc(DailyReward.streak_days)).first()
        
        longest_streak = 0
        longest_streak_user = "N/A"
        if longest_streak_record:
            longest_streak = longest_streak_record[0].streak_days
            longest_streak_user = longest_streak_record[1].username
        
        # Calcular puntos distribuidos (aproximado)
        all_rewards = db.query(DailyReward).all()
        total_points = 0
        for reward in all_rewards:
            # Fórmula: base (50) * claims + streaks bonus
            total_points += 50 * reward.total_claims
            # Bonus aproximado por streaks
            total_points += reward.best_streak * 10 * (reward.total_claims // 7)
        
        return {
            "total_claims_today": total_claims_today,
            "total_active_streaks": total_active_streaks,
            "longest_streak": longest_streak,
            "longest_streak_user": longest_streak_user,
            "total_points_distributed": total_points
        }
    finally:
        db.close()


@router.get("/top-streaks", response_model=List[TopStreakUser])
async def get_top_streaks(
    limit: int = 10,
    current_user: AdminUser = Depends(get_current_user)
):
    """Obtener top usuarios por racha actual"""
    db = SessionLocal()
    try:
        from datetime import timedelta
        active_threshold = datetime.utcnow() - timedelta(hours=48)
        
        # Top por streak actual (solo activos)
        top_streaks = db.query(DailyReward, User).join(User).filter(
            DailyReward.last_claim >= active_threshold
        ).order_by(desc(DailyReward.streak_days)).limit(limit).all()
        
        return [
            {
                "username": user.username,
                "discord_id": user.discord_id,
                "streak_days": reward.streak_days,
                "best_streak": reward.best_streak,
                "total_claims": reward.total_claims
            }
            for reward, user in top_streaks
        ]
    finally:
        db.close()


@router.get("/top-best-streaks", response_model=List[TopStreakUser])
async def get_top_best_streaks(
    limit: int = 10,
    current_user: AdminUser = Depends(get_current_user)
):
    """Obtener top usuarios por mejor racha histórica"""
    db = SessionLocal()
    try:
        top_best = db.query(DailyReward, User).join(User).order_by(
            desc(DailyReward.best_streak)
        ).limit(limit).all()
        
        return [
            {
                "username": user.username,
                "discord_id": user.discord_id,
                "streak_days": reward.streak_days,
                "best_streak": reward.best_streak,
                "total_claims": reward.total_claims
            }
            for reward, user in top_best
        ]
    finally:
        db.close()
