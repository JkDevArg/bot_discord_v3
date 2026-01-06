"""
Servicio de anuncios de nivel usando Discord Webhooks
"""
import aiohttp
from bot.utils.logger import bot_logger
from bot.database.connection import SessionLocal
from bot.database.channel_config import ChannelConfig
from datetime import datetime


class LevelAnnouncementService:
    """Servicio para enviar anuncios de nivel a Discord"""
    
    @staticmethod
    async def announce_level_up(user_id: int, username: str, avatar_url: str, old_level: int, new_level: int, bonus_points: int = 0):
        """
        Anunciar que un usuario subió de nivel
        
        Args:
            user_id: ID de Discord del usuario
            username: Nombre del usuario
            avatar_url: URL del avatar del usuario
            old_level: Nivel anterior
            new_level: Nivel nuevo
            bonus_points: Puntos de bonificación (si aplica)
        """
        try:
            # Obtener webhook URL del canal de anuncios
            db = SessionLocal()
            try:
                config = db.query(ChannelConfig).filter(
                    ChannelConfig.config_type == 'announcement_webhook'
                ).first()
                
                if not config or not config.channel_ids:
                    bot_logger.warning("Announcement webhook URL not configured")
                    return False
                
                webhook_url = config.channel_ids
                
            finally:
                db.close()
            
            # Determinar color según el nivel
            color = LevelAnnouncementService._get_level_color(new_level)
            
            # Crear mensaje personalizado
            message = f"¡El usuario **{username}** ha subido de nivel!"
            
            # Agregar información de bonificación si aplica
            bonus_text = ""
            if bonus_points > 0:
                bonus_text = f"\n🎁 **¡Bonificación!** +{bonus_points} puntos por alcanzar nivel {new_level}"
            
            # Crear embed
            embed = {
                "title": "🎉 ¡Subida de Nivel!",
                "description": message,
                "color": color,
                "thumbnail": {
                    "url": avatar_url
                },
                "fields": [
                    {
                        "name": "Nivel Anterior",
                        "value": f"⭐ {old_level}",
                        "inline": True
                    },
                    {
                        "name": "Nivel Nuevo",
                        "value": f"✨ **{new_level}**",
                        "inline": True
                    }
                ],
                "footer": {
                    "text": f"Usuario ID: {user_id}",
                    "icon_url": avatar_url
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Agregar campo de bonificación si aplica
            if bonus_text:
                embed["fields"].append({
                    "name": "Recompensa",
                    "value": bonus_text,
                    "inline": False
                })
            
            # Enviar via webhook
            async with aiohttp.ClientSession() as session:
                webhook_data = {
                    "username": "Sistema de Niveles",
                    "avatar_url": "https://cdn.discordapp.com/emojis/1234567890.png",  # Opcional: avatar del bot
                    "embeds": [embed]
                }
                
                async with session.post(webhook_url, json=webhook_data) as response:
                    if response.status == 204:
                        bot_logger.info(f"Level-up announcement sent for {username}: {old_level} -> {new_level}")
                        return True
                    else:
                        bot_logger.error(f"Failed to send level-up announcement: {response.status}")
                        return False
        
        except Exception as e:
            bot_logger.error(f"Error sending level-up announcement: {e}")
            return False
    
    @staticmethod
    def _get_level_color(level: int) -> int:
        """
        Obtener color del embed según el nivel
        
        Args:
            level: Nivel del usuario
        
        Returns:
            Color en formato hexadecimal
        """
        if level >= 100:
            return 0xFFD700  # Dorado - Inmortal
        elif level >= 75:
            return 0xFF69B4  # Rosa - Divino
        elif level >= 50:
            return 0x9B59B6  # Púrpura - Mítico
        elif level >= 30:
            return 0xE74C3C  # Rojo - Leyenda
        elif level >= 20:
            return 0xF39C12  # Naranja - Élite
        elif level >= 10:
            return 0x3498DB  # Azul - Guerrero
        else:
            return 0x2ECC71  # Verde - Novato
