"""
Endpoint de prueba para Discord logging
"""
from fastapi import APIRouter, Depends
from web.auth import get_current_user
from bot.database.models import AdminUser
from web.discord_integration import DiscordIntegrationService
import discord
from datetime import datetime

router = APIRouter(prefix="/test", tags=["Test"])


@router.post("/discord-log")
async def test_discord_log(current_user: AdminUser = Depends(get_current_user)):
    """Enviar mensaje de prueba al canal de logs"""
    try:
        from web.webhook_logger import WebhookLogger
        
        await WebhookLogger.log_admin_action(
            "🧪 Prueba del Sistema",
            f"✅ El sistema de logging está funcionando correctamente\n"
            f"👤 Usuario de prueba: **{current_user.username}**\n"
            f"⏰ Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            current_user.username
        )
        
        return {
            "success": True,
            "message": "Mensaje de prueba enviado correctamente. Revisa el canal #log_bot en Discord."
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/level-announcement")
async def test_level_announcement(current_user: AdminUser = Depends(get_current_user)):
    """Enviar anuncio de prueba de subida de nivel"""
    try:
        from bot.services.announcement_service import LevelAnnouncementService
        
        # Datos de prueba
        await LevelAnnouncementService.announce_level_up(
            user_id=123456789,
            username=current_user.username,
            avatar_url="https://cdn.discordapp.com/embed/avatars/0.png",
            old_level=9,
            new_level=10,
            bonus_points=5  # Bonificación porque es nivel 10
        )
        
        return {
            "success": True,
            "message": "Anuncio de nivel enviado correctamente. Revisa el canal #bot-anuncios en Discord."
        }
        
    except Exception as e:
        import traceback
        return {
            "success": False,
            "error": f"{str(e)}\n{traceback.format_exc()}"
        }
