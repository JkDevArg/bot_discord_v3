"""
Servicio de logging usando Discord Webhooks
"""
import aiohttp
import discord
from typing import Optional
from bot.utils.logger import web_logger
from bot.database.connection import SessionLocal
from bot.database.channel_config import ChannelConfig
from datetime import datetime


class WebhookLogger:
    """Servicio para enviar logs a Discord usando webhooks"""
    
    @staticmethod
    async def send_log(title: str, description: str, color: int = 0x3498db, fields: list = None):
        """
        Enviar log a Discord usando webhook
        
        Args:
            title: Título del embed
            description: Descripción del embed
            color: Color del embed (hex)
            fields: Lista de campos adicionales [{"name": "...", "value": "...", "inline": bool}]
        """
        try:
            # Obtener webhook URL desde configuración
            db = SessionLocal()
            try:
                config = db.query(ChannelConfig).filter(
                    ChannelConfig.config_type == 'webhook_url'
                ).first()
                
                if not config or not config.channel_ids:
                    web_logger.warning("Webhook URL not configured")
                    return False
                
                webhook_url = config.channel_ids
                
            finally:
                db.close()
            
            # Crear embed
            embed = {
                "title": title,
                "description": description,
                "color": color,
                "timestamp": datetime.utcnow().isoformat(),
                "footer": {
                    "text": "Panel Web Administrativo"
                }
            }
            
            # Agregar campos si existen
            if fields:
                embed["fields"] = fields
            
            # Enviar via webhook
            async with aiohttp.ClientSession() as session:
                webhook_data = {
                    "embeds": [embed]
                }
                
                async with session.post(webhook_url, json=webhook_data) as response:
                    if response.status == 204:
                        web_logger.info(f"Log sent to Discord via webhook: {title}")
                        return True
                    else:
                        web_logger.error(f"Failed to send webhook: {response.status}")
                        return False
        
        except Exception as e:
            web_logger.error(f"Error sending webhook: {e}")
            return False
    
    @staticmethod
    async def log_admin_action(action: str, details: str, admin_username: str):
        """
        Registrar acción administrativa
        
        Args:
            action: Tipo de acción
            details: Detalles de la acción
            admin_username: Usuario que ejecutó la acción
        """
        await WebhookLogger.send_log(
            title="⚙️ Acción Administrativa",
            description=f"**Acción:** {action}\n\n{details}",
            color=0x3498db,  # Azul
            fields=[
                {"name": "Admin", "value": admin_username, "inline": True},
                {"name": "Origen", "value": "Panel Web", "inline": True}
            ]
        )
    
    @staticmethod
    async def log_moderation(action: str, user: str, reason: str, admin_username: str, extra_fields: list = None):
        """
        Registrar acción de moderación
        
        Args:
            action: Tipo de acción (Kick, Ban, Timeout)
            user: Usuario afectado
            reason: Razón de la acción
            admin_username: Moderador
            extra_fields: Campos adicionales
        """
        colors = {
            "Kick": 0xe67e22,  # Naranja
            "Ban": 0xe74c3c,   # Rojo
            "Timeout": 0xf39c12  # Amarillo
        }
        
        fields = [
            {"name": "Usuario", "value": user, "inline": False},
            {"name": "Razón", "value": reason, "inline": False},
            {"name": "Moderador", "value": admin_username, "inline": True},
            {"name": "Origen", "value": "Panel Web", "inline": True}
        ]
        
        if extra_fields:
            fields.extend(extra_fields)
        
        await WebhookLogger.send_log(
            title=f"🔨 {action}",
            description=f"Acción de moderación ejecutada",
            color=colors.get(action, 0x95a5a6),
            fields=fields
        )
