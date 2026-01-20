"""
API endpoints para perfiles de usuario detallados
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from bot.database.connection import SessionLocal
from bot.database.models import User, Purchase, DailyReward, ActivityLog
from web.auth import get_current_user, AdminUser
from sqlalchemy import func, desc

router = APIRouter(prefix="/users", tags=["User Profiles"])


class UserProfileResponse(BaseModel):
    user_id: int
    discord_id: int
    username: str
    discriminator: str
    avatar_url: Optional[str]
    level: int
    exp: int
    exp_needed: int
    points: int
    message_count: int
    total_spent: int
    events_completed: int
    current_streak: int
    best_streak: int
    created_at: datetime
    last_activity: Optional[datetime]


class ActivityHistoryItem(BaseModel):
    id: int
    activity_type: str
    description: str
    timestamp: datetime
    metadata: Optional[dict] = None


class PurchaseHistoryItem(BaseModel):
    id: int
    item_name: str
    price_paid: int
    purchased_at: datetime


class LevelProgressItem(BaseModel):
    date: str
    exp_gained: int
    level: int


@router.get("/{user_id}/profile", response_model=UserProfileResponse)
async def get_user_profile(
    user_id: int,
    current_user: AdminUser = Depends(get_current_user)
):
    """Obtener perfil completo del usuario"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Calcular EXP necesaria para siguiente nivel
        from bot.services.level_service import LevelService
        from bot.utils.config_helper import ConfigHelper
        
        # Cargar config para calcular EXP correctamente
        config = ConfigHelper.get_bot_config(db)
        exp_needed = LevelService.calculate_exp_for_level(
            user.level + 1,
            base_exp=config.level_base_exp,
            multiplier=config.level_exp_multiplier
        )
        
        # Total gastado en tienda
        total_spent = db.query(func.sum(Purchase.price_paid)).filter(
            Purchase.user_id == user_id
        ).scalar() or 0
        
        # Eventos completados
        from bot.database.models import EventParticipant
        events_completed = db.query(func.count(EventParticipant.id)).filter(
            EventParticipant.user_id == user_id,
            EventParticipant.reward_received == True
        ).scalar() or 0
        
        # Rachas de daily rewards
        daily_reward = db.query(DailyReward).filter(
            DailyReward.user_id == user_id
        ).first()
        
        current_streak = daily_reward.streak_days if daily_reward else 0
        best_streak = daily_reward.best_streak if daily_reward else 0
        
        return UserProfileResponse(
            user_id=user.id,
            discord_id=user.discord_id,
            username=user.username,
            discriminator=user.discriminator,
            avatar_url=user.avatar_url,
            level=user.level,
            exp=user.exp,
            exp_needed=exp_needed,
            points=user.points,
            message_count=user.total_messages,
            total_spent=int(total_spent),
            events_completed=events_completed,
            current_streak=current_streak,
            best_streak=best_streak,
            created_at=user.created_at,
            last_activity=user.last_activity
        )
    finally:
        db.close()


@router.get("/{user_id}/activity-history", response_model=List[ActivityHistoryItem])
async def get_activity_history(
    user_id: int,
    limit: int = 50,
    current_user: AdminUser = Depends(get_current_user)
):
    """Obtener historial de actividad del usuario"""
    db = SessionLocal()
    try:
        activities = db.query(ActivityLog).filter(
            ActivityLog.user_id == user_id
        ).order_by(desc(ActivityLog.created_at)).limit(limit).all()
        
        result = []
        for activity in activities:
            # Crear descripción basada en el tipo de actividad
            description = f"Actividad: {activity.activity_type}"
            if activity.points_awarded and activity.points_awarded > 0:
                description = f"Ganó {activity.points_awarded} puntos por {activity.activity_type}"
            
            result.append(ActivityHistoryItem(
                id=activity.id,
                activity_type=activity.activity_type,
                description=description,
                timestamp=activity.created_at,
                metadata={"points": activity.points_awarded} if activity.points_awarded else None
            ))
        
        return result
    finally:
        db.close()


@router.get("/{user_id}/purchases", response_model=List[PurchaseHistoryItem])
async def get_purchase_history(
    user_id: int,
    current_user: AdminUser = Depends(get_current_user)
):
    """Obtener historial de compras del usuario"""
    db = SessionLocal()
    try:
        purchases = db.query(Purchase).filter(
            Purchase.user_id == user_id
        ).order_by(desc(Purchase.purchased_at)).all()
        
        result = []
        for purchase in purchases:
            result.append(PurchaseHistoryItem(
                id=purchase.id,
                item_name=purchase.item_name,
                price_paid=purchase.price_paid,
                purchased_at=purchase.purchased_at
            ))
        
        return result
    finally:
        db.close()


@router.get("/{user_id}/level-progress", response_model=List[LevelProgressItem])
async def get_level_progress(
    user_id: int,
    days: int = 30,
    current_user: AdminUser = Depends(get_current_user)
):
    """Obtener progreso de nivel en los últimos N días"""
    db = SessionLocal()
    try:
        # Obtener usuario
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return []
        
        # Obtener actividades de level-up en los últimos N días
        start_date = datetime.utcnow() - timedelta(days=days)
        
        activities = db.query(ActivityLog).filter(
            ActivityLog.user_id == user_id,
            ActivityLog.activity_type == 'level_up',
            ActivityLog.created_at >= start_date
        ).order_by(ActivityLog.created_at.asc()).all()
        
        # Si no hay level-ups, crear datos simulados basados en EXP actual
        if not activities:
            return [LevelProgressItem(
                date=datetime.utcnow().strftime('%Y-%m-%d'),
                exp_gained=user.exp,
                level=user.level
            )]
        
        result = []
        for activity in activities:
            result.append(LevelProgressItem(
                date=activity.created_at.strftime('%Y-%m-%d'),
                exp_gained=100,  # Placeholder
                level=user.level
            ))
        
        return result
    finally:
        db.close()
