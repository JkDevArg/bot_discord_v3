"""
Servicio de gestión de roles
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from bot.database.models import Role, User, UserRole
from bot.utils.logger import bot_logger
from bot.utils.validators import validate_hex_color
from datetime import datetime
import discord


class RoleService:
    """Servicio para gestionar roles"""
    
    @staticmethod
    def create_role(
        db: Session,
        name: str,
        discord_role_id: int,
        points_required: int = 0,
        color: str = "#FFFFFF",
        benefits: str = "",
        auto_assign: bool = True,
        is_purchasable: bool = False
    ) -> Role:
        """
        Crear un nuevo rol
        
        Args:
            db: Sesión de base de datos
            name: Nombre del rol
            discord_role_id: ID del rol en Discord
            points_required: Puntos requeridos
            color: Color en formato hex
            benefits: Descripción de beneficios
            auto_assign: Si se asigna automáticamente
            is_purchasable: Si se puede comprar en la tienda
        
        Returns:
            Rol creado
        """
        if not validate_hex_color(color):
            color = "#FFFFFF"
        
        role = Role(
            name=name,
            discord_role_id=discord_role_id,
            points_required=points_required,
            color=color,
            benefits=benefits,
            auto_assign=auto_assign,
            is_purchasable=is_purchasable
        )
        db.add(role)
        db.commit()
        db.refresh(role)
        
        bot_logger.info(f"Rol creado: {name} (req: {points_required} pts)")
        return role
    
    @staticmethod
    def get_role_by_id(db: Session, role_id: int) -> Role:
        """Obtener rol por ID"""
        return db.query(Role).filter(Role.id == role_id).first()
    
    @staticmethod
    def get_role_by_discord_id(db: Session, discord_role_id: int) -> Role:
        """Obtener rol por Discord ID"""
        return db.query(Role).filter(Role.discord_role_id == discord_role_id).first()
    
    @staticmethod
    def get_all_roles(db: Session) -> list[Role]:
        """Obtener todos los roles ordenados por puntos requeridos"""
        return db.query(Role).order_by(Role.points_required).all()
    
    @staticmethod
    def update_role(db: Session, role: Role, **kwargs) -> Role:
        """
        Actualizar rol
        
        Args:
            db: Sesión de base de datos
            role: Rol a actualizar
            **kwargs: Campos a actualizar
        
        Returns:
            Rol actualizado
        """
        for key, value in kwargs.items():
            if hasattr(role, key):
                setattr(role, key, value)
        
        role.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(role)
        
        bot_logger.info(f"Rol actualizado: {role.name}")
        return role
    
    @staticmethod
    def delete_role(db: Session, role: Role) -> bool:
        """
        Eliminar rol
        
        Args:
            db: Sesión de base de datos
            role: Rol a eliminar
        
        Returns:
            True si fue exitoso
        """
        db.delete(role)
        db.commit()
        bot_logger.info(f"Rol eliminado: {role.name}")
        return True
    
    @staticmethod
    def assign_role_to_user(db: Session, user: User, role: Role) -> bool:
        """
        Asignar rol a usuario
        
        Args:
            db: Sesión de base de datos
            user: Usuario
            role: Rol
        
        Returns:
            True si fue exitoso, False si ya lo tenía
        """
        # Verificar si ya tiene el rol
        existing = db.query(UserRole).filter(
            and_(UserRole.user_id == user.id, UserRole.role_id == role.id)
        ).first()
        
        if existing:
            return False
        
        user_role = UserRole(user_id=user.id, role_id=role.id)
        db.add(user_role)
        db.commit()
        
        bot_logger.info(f"Rol asignado: {role.name} -> {user.username}")
        return True
    
    @staticmethod
    def remove_role_from_user(db: Session, user: User, role: Role) -> bool:
        """
        Remover rol de usuario
        
        Args:
            db: Sesión de base de datos
            user: Usuario
            role: Rol
        
        Returns:
            True si fue exitoso
        """
        user_role = db.query(UserRole).filter(
            and_(UserRole.user_id == user.id, UserRole.role_id == role.id)
        ).first()
        
        if user_role:
            db.delete(user_role)
            db.commit()
            bot_logger.info(f"Rol removido: {role.name} <- {user.username}")
            return True
        
        return False
    
    @staticmethod
    def get_user_roles(db: Session, user: User) -> list[Role]:
        """
        Obtener roles de un usuario
        
        Args:
            db: Sesión de base de datos
            user: Usuario
        
        Returns:
            Lista de roles
        """
        user_roles = db.query(UserRole).filter(UserRole.user_id == user.id).all()
        return [ur.role for ur in user_roles]
    
    @staticmethod
    def check_and_assign_auto_roles(db: Session, user: User, guild: discord.Guild) -> list[Role]:
        """
        Verificar y asignar roles automáticos según puntos
        
        Args:
            db: Sesión de base de datos
            user: Usuario
            guild: Guild de Discord
        
        Returns:
            Lista de roles nuevos asignados
        """
        # Obtener roles auto-asignables que el usuario cumple requisitos
        eligible_roles = db.query(Role).filter(
            Role.auto_assign == True,
            Role.points_required <= user.points
        ).all()
        
        # Obtener roles actuales del usuario
        current_roles = RoleService.get_user_roles(db, user)
        current_role_ids = {r.id for r in current_roles}
        
        # Asignar roles nuevos
        newly_assigned = []
        for role in eligible_roles:
            if role.id not in current_role_ids:
                if RoleService.assign_role_to_user(db, user, role):
                    newly_assigned.append(role)
                    
                    # Asignar rol en Discord
                    try:
                        discord_role = guild.get_role(role.discord_role_id)
                        if discord_role:
                            member = guild.get_member(user.discord_id)
                            if member:
                                # Esto se debe hacer de forma asíncrona en el bot
                                pass
                    except Exception as e:
                        bot_logger.error(f"Error asignando rol en Discord: {e}")
        
        return newly_assigned
    
    @staticmethod
    def get_next_role(db: Session, user: User) -> tuple[Role, int]:
        """
        Obtener el siguiente rol que puede alcanzar el usuario
        
        Args:
            db: Sesión de base de datos
            user: Usuario
        
        Returns:
            Tupla (siguiente_rol, puntos_faltantes) o (None, 0)
        """
        next_role = db.query(Role).filter(
            Role.auto_assign == True,
            Role.points_required > user.points
        ).order_by(Role.points_required).first()
        
        if next_role:
            points_needed = next_role.points_required - user.points
            return next_role, points_needed
        
        return None, 0
