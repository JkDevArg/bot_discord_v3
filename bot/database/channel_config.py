"""
Modelo extendido para configuración de canales
"""
from sqlalchemy import Column, Integer, String, Boolean, BigInteger
from bot.database.models import Base


class ChannelConfig(Base):
    """Configuración de canales para el bot"""
    __tablename__ = 'channel_config'
    
    id = Column(Integer, primary_key=True)
    config_type = Column(String(50), unique=True, nullable=False)  # 'points_channels', 'log_channel'
    channel_ids = Column(String(500))  # JSON array de IDs de canales
    is_enabled = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<ChannelConfig {self.config_type}>"
