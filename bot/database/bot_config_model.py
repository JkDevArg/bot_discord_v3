"""
Modelo para configuración del bot
"""
from sqlalchemy import Column, Integer, String, Boolean, Float, Text
from bot.database.models import Base


class BotConfig(Base):
    """Configuración general del bot"""
    __tablename__ = 'bot_config'
    
    id = Column(Integer, primary_key=True)
    guild_id = Column(String(20), unique=True, nullable=False, index=True)
    
    # Daily Rewards
    daily_base_reward = Column(Integer, default=50, nullable=False)
    daily_max_streak_bonus = Column(Integer, default=200, nullable=False)
    daily_streak_bonus_per_day = Column(Integer, default=10, nullable=False)
    daily_week_bonus = Column(Integer, default=100, nullable=False)  # Día 7
    daily_month_bonus = Column(Integer, default=500, nullable=False)  # Día 30
    daily_cooldown_hours = Column(Integer, default=20, nullable=False)
    
    # Level System
    level_base_exp = Column(Integer, default=100, nullable=False)
    level_exp_multiplier = Column(Float, default=1.5, nullable=False)
    level_points_per_message = Column(Integer, default=5, nullable=False)
    level_exp_per_message = Column(Integer, default=10, nullable=False)
    level_cooldown_seconds = Column(Integer, default=60, nullable=False)
    
    # Shop
    shop_enabled = Column(Boolean, default=True, nullable=False)
    shop_tax_rate = Column(Float, default=0.0, nullable=False)  # Porcentaje de impuesto
    
    # Events
    event_participation_reward = Column(Integer, default=50, nullable=False)
    event_completion_reward = Column(Integer, default=100, nullable=False)
    
    # General
    welcome_message = Column(Text, nullable=True)
    prefix = Column(String(5), default='!', nullable=False)
    
    def __repr__(self):
        return f"<BotConfig(guild_id={self.guild_id})>"
