"""
Endpoints de moderación
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from bot.database.models import AdminUser
from web.auth import get_current_user
from web.discord_integration import DiscordIntegrationService
from bot.config import DISCORD_GUILD_ID


router = APIRouter(prefix="/moderation", tags=["Moderation"])


class KickRequest(BaseModel):
    user_id: int
    reason: str


class BanRequest(BaseModel):
    user_id: int
    reason: str
    delete_message_days: int = 0


class TimeoutRequest(BaseModel):
    user_id: int
    duration_minutes: int
    reason: str


@router.post("/kick")
async def kick_user(request: KickRequest, current_user: AdminUser = Depends(get_current_user)):
    """Expulsar usuario del servidor"""
    success, message = await DiscordIntegrationService.kick_member(
        DISCORD_GUILD_ID,
        request.user_id,
        request.reason,
        current_user.username
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {"message": message}


@router.post("/ban")
async def ban_user(request: BanRequest, current_user: AdminUser = Depends(get_current_user)):
    """Banear usuario del servidor"""
    success, message = await DiscordIntegrationService.ban_member(
        DISCORD_GUILD_ID,
        request.user_id,
        request.reason,
        current_user.username,
        request.delete_message_days
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {"message": message}


@router.post("/timeout")
async def timeout_user(request: TimeoutRequest, current_user: AdminUser = Depends(get_current_user)):
    """Silenciar (timeout) usuario"""
    success, message = await DiscordIntegrationService.timeout_member(
        DISCORD_GUILD_ID,
        request.user_id,
        request.duration_minutes,
        request.reason,
        current_user.username
    )
    
    if not success:
        raise HTTPException(status_code=400, detail=message)
    
    return {"message": message}
