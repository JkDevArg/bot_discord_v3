"""
Endpoints para configuración de canales
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List
import json
from bot.database.models import AdminUser
from bot.database.connection import SessionLocal
from bot.database.channel_config import ChannelConfig
from web.auth import get_current_user


router = APIRouter(prefix="/config", tags=["Configuration"])


class ChannelConfigRequest(BaseModel):
    channel_ids: List[str]


class SingleChannelRequest(BaseModel):
    channel_id: str


@router.get("/channels/points")
async def get_points_channels(current_user: AdminUser = Depends(get_current_user)):
    """Obtener canales configurados para puntos"""
    db = SessionLocal()
    try:
        config = db.query(ChannelConfig).filter(
            ChannelConfig.config_type == 'points_channels'
        ).first()
        
        if not config or not config.channel_ids:
            return {"channel_ids": []}
        
        channel_ids = json.loads(config.channel_ids)
        return {"channel_ids": channel_ids}
    finally:
        db.close()


@router.post("/channels/points")
async def save_points_channels(
    request: ChannelConfigRequest,
    current_user: AdminUser = Depends(get_current_user)
):
    """Guardar canales para puntos"""
    db = SessionLocal()
    try:
        config = db.query(ChannelConfig).filter(
            ChannelConfig.config_type == 'points_channels'
        ).first()
        
        if not config:
            config = ChannelConfig(
                config_type='points_channels',
                channel_ids=json.dumps(request.channel_ids),
                is_enabled=True
            )
            db.add(config)
        else:
            config.channel_ids = json.dumps(request.channel_ids)
        
        db.commit()
        return {"message": "Canales de puntos guardados", "channel_ids": request.channel_ids}
    finally:
        db.close()


@router.get("/channels/announcements")
async def get_announcement_channel(current_user: AdminUser = Depends(get_current_user)):
    """Obtener canal de anuncios"""
    db = SessionLocal()
    try:
        config = db.query(ChannelConfig).filter(
            ChannelConfig.config_type == 'announcement_channel'
        ).first()
        
        if not config or not config.channel_ids:
            return {"channel_id": None}
        
        channel_id = config.channel_ids
        return {"channel_id": channel_id}
    finally:
        db.close()


@router.post("/channels/announcements")
async def save_announcement_channel(
    request: SingleChannelRequest,
    current_user: AdminUser = Depends(get_current_user)
):
    """Guardar canal de anuncios"""
    db = SessionLocal()
    try:
        config = db.query(ChannelConfig).filter(
            ChannelConfig.config_type == 'announcement_channel'
        ).first()
        
        if not config:
            config = ChannelConfig(
                config_type='announcement_channel',
                channel_ids=request.channel_id,
                is_enabled=True
            )
            db.add(config)
        else:
            config.channel_ids = request.channel_id
        
        db.commit()
        return {"message": "Canal de anuncios guardado", "channel_id": request.channel_id}
    finally:
        db.close()


@router.get("/channels/logs")
async def get_log_channel(current_user: AdminUser = Depends(get_current_user)):
    """Obtener canal de logs"""
    db = SessionLocal()
    try:
        config = db.query(ChannelConfig).filter(
            ChannelConfig.config_type == 'log_channel'
        ).first()
        
        if not config or not config.channel_ids:
            return {"channel_id": None}
        
        channel_id = config.channel_ids
        return {"channel_id": channel_id}
    finally:
        db.close()


@router.post("/channels/logs")
async def save_log_channel(
    request: SingleChannelRequest,
    current_user: AdminUser = Depends(get_current_user)
):
    """Guardar canal de logs"""
    db = SessionLocal()
    try:
        config = db.query(ChannelConfig).filter(
            ChannelConfig.config_type == 'log_channel'
        ).first()
        
        if not config:
            config = ChannelConfig(
                config_type='log_channel',
                channel_ids=request.channel_id,
                is_enabled=True
            )
            db.add(config)
        else:
            config.channel_ids = request.channel_id
        
        db.commit()
        return {"message": "Canal de logs guardado", "channel_id": request.channel_id}
    finally:
        db.close()
