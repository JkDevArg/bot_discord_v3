"""
API endpoints para gestión de roles
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from bot.database.connection import SessionLocal
from bot.database.models import Role
from web.auth import get_current_user, AdminUser
from web.discord_integration import DiscordIntegrationService

router = APIRouter(prefix="/roles", tags=["Roles"])


class RoleCreate(BaseModel):
    discord_role_id: int
    name: str
    points_required: int
    auto_assign: bool = True
    is_active: bool = True


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    points_required: Optional[int] = None
    auto_assign: Optional[bool] = None
    is_active: Optional[bool] = None


class RoleResponse(BaseModel):
    id: int
    discord_role_id: int
    name: str
    points_required: int
    auto_assign: bool
    is_active: bool
    color: Optional[str] = None
    
    class Config:
        from_attributes = True


class DiscordRoleInfo(BaseModel):
    id: int
    name: str
    color: str
    position: int


@router.get("", response_model=List[RoleResponse])
async def get_roles(current_user: AdminUser = Depends(get_current_user)):
    """Obtener todos los roles configurados"""
    db = SessionLocal()
    try:
        roles = db.query(Role).order_by(Role.points_required.asc()).all()
        
        # Enriquecer con información de Discord si el bot está disponible
        if DiscordIntegrationService._bot_instance:
            for role in roles:
                try:
                    # Obtener el primer guild (servidor)
                    guild = DiscordIntegrationService._bot_instance.guilds[0]
                    discord_role = guild.get_role(role.discord_role_id)
                    if discord_role:
                        role.color = f"#{discord_role.color.value:06x}"
                except:
                    pass
        
        return roles
    finally:
        db.close()


@router.get("/discord", response_model=List[DiscordRoleInfo])
async def get_discord_roles(current_user: AdminUser = Depends(get_current_user)):
    """Obtener roles disponibles en Discord"""
    if not DiscordIntegrationService._bot_instance:
        raise HTTPException(
            status_code=503,
            detail="Bot no disponible. Asegúrate de que el bot esté corriendo."
        )
    
    try:
        # Obtener el primer guild
        guild = DiscordIntegrationService._bot_instance.guilds[0]
        
        discord_roles = []
        for role in guild.roles:
            # Ignorar @everyone y roles de bot
            if role.name == "@everyone" or role.managed:
                continue
            
            discord_roles.append({
                "id": role.id,
                "name": role.name,
                "color": f"#{role.color.value:06x}",
                "position": role.position
            })
        
        # Ordenar por posición (más alto primero)
        discord_roles.sort(key=lambda x: x["position"], reverse=True)
        
        return discord_roles
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo roles de Discord: {str(e)}")


@router.post("", response_model=RoleResponse)
async def create_role(
    role: RoleCreate,
    current_user: AdminUser = Depends(get_current_user)
):
    """Crear nuevo rol"""
    db = SessionLocal()
    try:
        # Verificar que no exista ya
        existing = db.query(Role).filter(
            Role.discord_role_id == role.discord_role_id
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail="Este rol ya está configurado"
            )
        
        # Crear rol
        new_role = Role(
            discord_role_id=role.discord_role_id,
            name=role.name,
            points_required=role.points_required,
            auto_assign=role.auto_assign,
            is_active=role.is_active
        )
        
        db.add(new_role)
        db.commit()
        db.refresh(new_role)
        
        return new_role
    finally:
        db.close()


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: int,
    role_update: RoleUpdate,
    current_user: AdminUser = Depends(get_current_user)
):
    """Actualizar rol existente"""
    db = SessionLocal()
    try:
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Rol no encontrado")
        
        # Actualizar campos
        if role_update.name is not None:
            role.name = role_update.name
        if role_update.points_required is not None:
            role.points_required = role_update.points_required
        if role_update.auto_assign is not None:
            role.auto_assign = role_update.auto_assign
        if role_update.is_active is not None:
            role.is_active = role_update.is_active
        
        db.commit()
        db.refresh(role)
        
        return role
    finally:
        db.close()


@router.delete("/{role_id}")
async def delete_role(
    role_id: int,
    current_user: AdminUser = Depends(get_current_user)
):
    """Eliminar rol"""
    db = SessionLocal()
    try:
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(status_code=404, detail="Rol no encontrado")
        
        db.delete(role)
        db.commit()
        
        return {"message": "Rol eliminado correctamente"}
    finally:
        db.close()
