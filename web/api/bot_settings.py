"""
API endpoints para configuración general del bot
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from bot.database.connection import SessionLocal
from bot.database.models import BotConfig
from web.auth import get_current_user, AdminUser
from bot.config import DISCORD_GUILD_ID

router = APIRouter(prefix="/bot-settings", tags=["Bot Settings"])


class BotConfigSchema(BaseModel):
    # Daily Rewards
    daily_base_reward: int = Field(ge=1, le=10000)
    daily_max_streak_bonus: int = Field(ge=0, le=10000)
    daily_streak_bonus_per_day: int = Field(ge=0, le=1000)
    daily_week_bonus: int = Field(ge=0, le=10000)
    daily_month_bonus: int = Field(ge=0, le=50000)
    daily_cooldown_hours: int = Field(ge=1, le=48)
    
    # Level System
    level_base_exp: int = Field(ge=10, le=10000)
    level_exp_multiplier: float = Field(ge=1.0, le=5.0)
    level_points_per_message: int = Field(ge=0, le=100)
    level_exp_per_message: int = Field(ge=1, le=1000)
    level_cooldown_seconds: int = Field(ge=0, le=3600)
    
    # Shop
    shop_enabled: bool
    shop_tax_rate: float = Field(ge=0.0, le=1.0)
    
    # Events
    event_participation_reward: int = Field(ge=0, le=10000)
    event_completion_reward: int = Field(ge=0, le=10000)
    
    # General
    welcome_message: Optional[str] = None
    prefix: str = Field(min_length=1, max_length=5)


@router.get("", response_model=BotConfigSchema)
async def get_bot_config(current_user: AdminUser = Depends(get_current_user)):
    """Obtener configuración actual del bot"""
    db = SessionLocal()
    try:
        config = db.query(BotConfig).filter(
            BotConfig.guild_id == DISCORD_GUILD_ID
        ).first()
        
        if not config:
            # Crear configuración por defecto
            config = BotConfig(guild_id=DISCORD_GUILD_ID)
            db.add(config)
            db.commit()
            db.refresh(config)
        
        return BotConfigSchema(
            daily_base_reward=config.daily_base_reward,
            daily_max_streak_bonus=config.daily_max_streak_bonus,
            daily_streak_bonus_per_day=config.daily_streak_bonus_per_day,
            daily_week_bonus=config.daily_week_bonus,
            daily_month_bonus=config.daily_month_bonus,
            daily_cooldown_hours=config.daily_cooldown_hours,
            level_base_exp=config.level_base_exp,
            level_exp_multiplier=config.level_exp_multiplier,
            level_points_per_message=config.level_points_per_message,
            level_exp_per_message=config.level_exp_per_message,
            level_cooldown_seconds=config.level_cooldown_seconds,
            shop_enabled=config.shop_enabled,
            shop_tax_rate=config.shop_tax_rate,
            event_participation_reward=config.event_participation_reward,
            event_completion_reward=config.event_completion_reward,
            welcome_message=config.welcome_message,
            prefix=config.prefix
        )
    finally:
        db.close()


@router.put("")
async def update_bot_config(
    config_data: BotConfigSchema,
    current_user: AdminUser = Depends(get_current_user)
):
    """Actualizar configuración del bot"""
    db = SessionLocal()
    try:
        config = db.query(BotConfig).filter(
            BotConfig.guild_id == DISCORD_GUILD_ID
        ).first()
        
        if not config:
            config = BotConfig(guild_id=DISCORD_GUILD_ID)
            db.add(config)
        
        # Actualizar valores
        config.daily_base_reward = config_data.daily_base_reward
        config.daily_max_streak_bonus = config_data.daily_max_streak_bonus
        config.daily_streak_bonus_per_day = config_data.daily_streak_bonus_per_day
        config.daily_week_bonus = config_data.daily_week_bonus
        config.daily_month_bonus = config_data.daily_month_bonus
        config.daily_cooldown_hours = config_data.daily_cooldown_hours
        
        config.level_base_exp = config_data.level_base_exp
        config.level_exp_multiplier = config_data.level_exp_multiplier
        config.level_points_per_message = config_data.level_points_per_message
        config.level_exp_per_message = config_data.level_exp_per_message
        config.level_cooldown_seconds = config_data.level_cooldown_seconds
        
        config.shop_enabled = config_data.shop_enabled
        config.shop_tax_rate = config_data.shop_tax_rate
        
        config.event_participation_reward = config_data.event_participation_reward
        config.event_completion_reward = config_data.event_completion_reward
        
        config.welcome_message = config_data.welcome_message
        config.prefix = config_data.prefix
        
        db.commit()
        
        return {"message": "Configuración actualizada correctamente"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.post("/reset")
async def reset_bot_config(current_user: AdminUser = Depends(get_current_user)):
    """Resetear configuración a valores por defecto"""
    db = SessionLocal()
    try:
        config = db.query(BotConfig).filter(
            BotConfig.guild_id == DISCORD_GUILD_ID
        ).first()
        
        if config:
            db.delete(config)
            db.commit()
        
        # Crear nueva configuración con valores por defecto
        new_config = BotConfig(guild_id=DISCORD_GUILD_ID)
        db.add(new_config)
        db.commit()
        
        return {"message": "Configuración reseteada a valores por defecto"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()
