"""
Helper para cargar configuración del bot desde la base de datos
"""
from sqlalchemy.orm import Session
from bot.database.models import BotConfig
from bot.config import DISCORD_GUILD_ID


class ConfigHelper:
    """Helper para obtener configuración del bot"""
    
    _cache = {}
    _cache_time = None
    
    @staticmethod
    def get_bot_config(db: Session) -> BotConfig:
        """
        Obtener configuración del bot desde la base de datos
        
        Args:
            db: Sesión de base de datos
            
        Returns:
            BotConfig con la configuración actual
        """
        config = db.query(BotConfig).filter(
            BotConfig.guild_id == str(DISCORD_GUILD_ID)
        ).first()
        
        # Si no existe, crear configuración por defecto
        if not config:
            config = BotConfig(
                guild_id=str(DISCORD_GUILD_ID),
                daily_base_reward=50,
                daily_max_streak_bonus=200,
                daily_streak_bonus_per_day=10,
                daily_week_bonus=100,
                daily_month_bonus=500,
                daily_cooldown_hours=20,
                level_base_exp=100,
                level_exp_multiplier=1.5,
                level_points_per_message=5,
                level_exp_per_message=10,
                level_cooldown_seconds=60,
                shop_enabled=True,
                shop_tax_rate=0.0,
                event_participation_reward=50,
                event_completion_reward=100,
                prefix='!',
                welcome_message=None
            )
            db.add(config)
            db.commit()
            db.refresh(config)
        
        return config
