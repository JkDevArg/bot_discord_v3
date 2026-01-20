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


# ============================================================================
# AUTO-MODERATION ENDPOINTS
# ============================================================================

from pydantic import Field
from typing import List, Optional
from datetime import datetime
from bot.database.connection import SessionLocal
from bot.database.models import ModerationConfig, FilteredWord, ModerationLog


class ModerationConfigResponse(BaseModel):
    id: int
    guild_id: int
    spam_enabled: bool
    spam_threshold: int
    spam_timeframe: int
    spam_mute_duration: int
    filter_enabled: bool
    filter_action: str
    
    class Config:
        from_attributes = True


class ModerationConfigUpdate(BaseModel):
    spam_enabled: Optional[bool] = None
    spam_threshold: Optional[int] = Field(None, ge=2, le=20)
    spam_timeframe: Optional[int] = Field(None, ge=1, le=60)
    spam_mute_duration: Optional[int] = Field(None, ge=60, le=3600)
    filter_enabled: Optional[bool] = None
    filter_action: Optional[str] = Field(None, pattern="^(delete|mute|warn)$")


class FilteredWordResponse(BaseModel):
    id: int
    word: str
    is_active: bool
    severity: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class FilteredWordCreate(BaseModel):
    word: str = Field(..., min_length=1, max_length=100)
    severity: str = Field(default="medium", pattern="^(low|medium|high)$")


class ModerationLogResponse(BaseModel):
    id: int
    user_id: int
    username: Optional[str]
    action: str
    reason: Optional[str]
    auto_moderated: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


@router.get("/config", response_model=ModerationConfigResponse)
async def get_moderation_config(current_user: AdminUser = Depends(get_current_user)):
    """Obtener configuración de auto-moderación"""
    db = SessionLocal()
    try:
        guild_id = int(DISCORD_GUILD_ID) if DISCORD_GUILD_ID else 0
        
        config = db.query(ModerationConfig).filter(
            ModerationConfig.guild_id == guild_id
        ).first()
        
        if not config:
            config = ModerationConfig(guild_id=guild_id)
            db.add(config)
            db.commit()
            db.refresh(config)
        
        return config
    finally:
        db.close()


@router.put("/config", response_model=ModerationConfigResponse)
async def update_moderation_config(
    config_update: ModerationConfigUpdate,
    current_user: AdminUser = Depends(get_current_user)
):
    """Actualizar configuración de auto-moderación"""
    db = SessionLocal()
    try:
        guild_id = int(DISCORD_GUILD_ID) if DISCORD_GUILD_ID else 0
        
        config = db.query(ModerationConfig).filter(
            ModerationConfig.guild_id == guild_id
        ).first()
        
        if not config:
            config = ModerationConfig(guild_id=guild_id)
            db.add(config)
        
        if config_update.spam_enabled is not None:
            config.spam_enabled = config_update.spam_enabled
        if config_update.spam_threshold is not None:
            config.spam_threshold = config_update.spam_threshold
        if config_update.spam_timeframe is not None:
            config.spam_timeframe = config_update.spam_timeframe
        if config_update.spam_mute_duration is not None:
            config.spam_mute_duration = config_update.spam_mute_duration
        if config_update.filter_enabled is not None:
            config.filter_enabled = config_update.filter_enabled
        if config_update.filter_action is not None:
            config.filter_action = config_update.filter_action
        
        db.commit()
        db.refresh(config)
        
        return config
    finally:
        db.close()


@router.get("/filtered-words", response_model=List[FilteredWordResponse])
async def get_filtered_words(
    active_only: bool = False,
    current_user: AdminUser = Depends(get_current_user)
):
    """Obtener lista de palabras filtradas"""
    db = SessionLocal()
    try:
        query = db.query(FilteredWord)
        
        if active_only:
            query = query.filter(FilteredWord.is_active == True)
        
        words = query.order_by(FilteredWord.word.asc()).all()
        return words
    finally:
        db.close()


@router.post("/filtered-words", response_model=FilteredWordResponse)
async def create_filtered_word(
    word_data: FilteredWordCreate,
    current_user: AdminUser = Depends(get_current_user)
):
    """Agregar palabra filtrada"""
    db = SessionLocal()
    try:
        existing = db.query(FilteredWord).filter(
            FilteredWord.word == word_data.word.lower()
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Esta palabra ya está en la lista")
        
        new_word = FilteredWord(
            word=word_data.word.lower(),
            severity=word_data.severity,
            is_active=True
        )
        
        db.add(new_word)
        db.commit()
        db.refresh(new_word)
        
        return new_word
    finally:
        db.close()


@router.delete("/filtered-words/{word_id}")
async def delete_filtered_word(
    word_id: int,
    current_user: AdminUser = Depends(get_current_user)
):
    """Eliminar palabra filtrada"""
    db = SessionLocal()
    try:
        word = db.query(FilteredWord).filter(FilteredWord.id == word_id).first()
        
        if not word:
            raise HTTPException(status_code=404, detail="Palabra no encontrada")
        
        db.delete(word)
        db.commit()
        
        return {"message": "Palabra eliminada correctamente"}
    finally:
        db.close()


@router.patch("/filtered-words/{word_id}/toggle")
async def toggle_filtered_word(
    word_id: int,
    current_user: AdminUser = Depends(get_current_user)
):
    """Activar/desactivar palabra filtrada"""
    db = SessionLocal()
    try:
        word = db.query(FilteredWord).filter(FilteredWord.id == word_id).first()
        
        if not word:
            raise HTTPException(status_code=404, detail="Palabra no encontrada")
        
        word.is_active = not word.is_active
        db.commit()
        db.refresh(word)
        
        return word
    finally:
        db.close()


@router.get("/logs", response_model=List[ModerationLogResponse])
async def get_moderation_logs(
    limit: int = 50,
    action: Optional[str] = None,
    current_user: AdminUser = Depends(get_current_user)
):
    """Obtener logs de moderación"""
    db = SessionLocal()
    try:
        query = db.query(ModerationLog)
        
        if action:
            query = query.filter(ModerationLog.action == action)
        
        logs = query.order_by(ModerationLog.created_at.desc()).limit(limit).all()
        return logs
    finally:
        db.close()
