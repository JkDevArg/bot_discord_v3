"""
Endpoints de gestión de usuarios
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from bot.database.connection import SessionLocal
from bot.database.models import AdminUser, User
from bot.services.points_service import PointsService
from bot.services.level_service import LevelService
from web.auth import get_current_user
from sqlalchemy import func
from bot.utils.sanitization import sanitize_integer


router = APIRouter(prefix="/users", tags=["Users"])


class UserResponse(BaseModel):
    id: int
    discord_id: int
    username: str
    points: int
    level: int
    exp: int
    total_messages: int
    last_activity: str
    
    class Config:
        from_attributes = True


class UserStatsResponse(BaseModel):
    total_users: int
    total_points: int
    total_exp: int
    avg_level: float
    top_user_by_points: Optional[dict]
    top_user_by_level: Optional[dict]


@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 50,
    current_user: AdminUser = Depends(get_current_user)
):
    """Listar usuarios"""
    db = SessionLocal()
    try:
        users = db.query(User).offset(skip).limit(limit).all()
        
        return [
            UserResponse(
                id=u.id,
                discord_id=u.discord_id,
                username=u.username,
                points=u.points,
                level=u.level,
                exp=u.exp,
                total_messages=u.total_messages,
                last_activity=u.last_activity.isoformat()
            )
            for u in users
        ]
    finally:
        db.close()


@router.get("/stats", response_model=UserStatsResponse)
async def get_users_stats(current_user: AdminUser = Depends(get_current_user)):
    """Obtener estadísticas de usuarios"""
    db = SessionLocal()
    try:
        total_users = db.query(func.count(User.id)).scalar()
        total_points = db.query(func.sum(User.points)).scalar() or 0
        total_exp = db.query(func.sum(User.exp)).scalar() or 0
        avg_level = db.query(func.avg(User.level)).scalar() or 0
        
        top_by_points = db.query(User).order_by(User.points.desc()).first()
        top_by_level = db.query(User).order_by(User.level.desc(), User.exp.desc()).first()
        
        return UserStatsResponse(
            total_users=total_users,
            total_points=int(total_points),
            total_exp=int(total_exp),
            avg_level=round(avg_level, 2),
            top_user_by_points={
                "username": top_by_points.username,
                "points": top_by_points.points
            } if top_by_points else None,
            top_user_by_level={
                "username": top_by_level.username,
                "level": top_by_level.level,
                "exp": top_by_level.exp
            } if top_by_level else None
        )
    finally:
        db.close()


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, current_user: AdminUser = Depends(get_current_user)):
    """Obtener usuario por ID"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        return UserResponse(
            id=user.id,
            discord_id=user.discord_id,
            username=user.username,
            points=user.points,
            level=user.level,
            exp=user.exp,
            total_messages=user.total_messages,
            last_activity=user.last_activity.isoformat()
        )
    finally:
        db.close()


class UpdatePointsRequest(BaseModel):
    points: int = Field(..., ge=0, le=1000000, description="Puntos del usuario (0-1,000,000)")
    
    @validator('points')
    def validate_points(cls, v):
        sanitized = sanitize_integer(v, min_value=0, max_value=1000000)
        if sanitized is None:
            raise ValueError('Puntos inválidos')
        return sanitized


@router.put("/{user_id}/points")
async def update_user_points(
    user_id: int,
    request: UpdatePointsRequest,
    current_user: AdminUser = Depends(get_current_user)
):
    """Actualizar puntos de un usuario"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        old_points = user.points
        user.points = request.points
        db.commit()
        
        # Log en Discord usando webhook
        try:
            from web.webhook_logger import WebhookLogger
            await WebhookLogger.log_admin_action(
                "Puntos Actualizados",
                f"👤 Usuario: **{user.username}** (ID: {user.discord_id})\n"
                f"💰 Puntos anteriores: **{old_points:,}**\n"
                f"💰 Puntos nuevos: **{request.points:,}**",
                current_user.username
            )
        except Exception as e:
            print(f"Warning: Could not log to Discord: {e}")
        
        return {"message": "Puntos actualizados", "user": user}
    finally:
        db.close()


class UpdateLevelRequest(BaseModel):
    level: int = Field(..., ge=1, le=100, description="Nivel del usuario (1-100)")
    
    @validator('level')
    def validate_level(cls, v):
        sanitized = sanitize_integer(v, min_value=1, max_value=100)
        if sanitized is None:
            raise ValueError('Nivel inválido')
        return sanitized


@router.put("/{user_id}/level")
async def update_user_level(
    user_id: int,
    request: UpdateLevelRequest,
    current_user: AdminUser = Depends(get_current_user)
):
    """Actualizar nivel de un usuario"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        
        # Actualizar nivel
        old_level = user.level
        user.level = request.level
        # Calcular EXP necesaria para el nuevo nivel
        user.exp = (request.level - 1) * 100
        db.commit()
        
        # Si subió de nivel, enviar anuncio
        if request.level > old_level:
            try:
                from bot.services.announcement_service import LevelAnnouncementService
                from bot.services.level_service import LevelService
                import asyncio
                
                # Calcular bonificación si aplica
                rewards = LevelService.get_level_rewards(request.level)
                bonus_points = rewards['points']
                
                # Usar avatar guardado en BD o avatar por defecto
                avatar_url = user.avatar_url if user.avatar_url else f"https://cdn.discordapp.com/embed/avatars/{int(user.discord_id) % 5}.png"
                
                # Enviar anuncio
                asyncio.create_task(
                    LevelAnnouncementService.announce_level_up(
                        user_id=user.discord_id,
                        username=user.username,
                        avatar_url=avatar_url,
                        old_level=old_level,
                        new_level=request.level,
                        bonus_points=bonus_points
                    )
                )
            except Exception as e:
                print(f"Warning: Could not send level announcement: {e}")
        
        # Log en Discord usando webhook
        try:
            from web.webhook_logger import WebhookLogger
            await WebhookLogger.log_admin_action(
                "Nivel Actualizado",
                f"👤 Usuario: **{user.username}** (ID: {user.discord_id})\n"
                f"⭐ Nivel anterior: **{old_level}**\n"
                f"⭐ Nivel nuevo: **{request.level}**",
                current_user.username
            )
        except Exception as e:
            print(f"Warning: Could not log to Discord: {e}")
        
        return {"message": "Nivel actualizado", "user": user}
    finally:
        db.close()
