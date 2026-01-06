"""
Servicio de gestión de puntos
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func
from bot.database.models import User, ActivityLog
from bot.config import (
    POINTS_PER_MESSAGE, MESSAGE_COOLDOWN, MAX_POINTS_PER_HOUR,
    INACTIVITY_DAYS, INACTIVITY_PENALTY
)
from bot.utils.logger import bot_logger
from bot.utils.validators import validate_discord_id, validate_points
import random


class PointsService:
    """Servicio para gestionar puntos de usuarios"""
    
    @staticmethod
    def get_or_create_user(db: Session, discord_id: int, username: str, discriminator: str = None, avatar_url: str = None) -> User:
        """
        Obtener usuario existente o crear uno nuevo
        
        Args:
            db: Sesión de base de datos
            discord_id: ID de Discord del usuario
            username: Nombre de usuario
            discriminator: Discriminador de Discord
            avatar_url: URL del avatar de Discord
        
        Returns:
            Usuario
        """
        user = db.query(User).filter(User.discord_id == discord_id).first()
        
        if not user:
            user = User(
                discord_id=discord_id,
                username=username,
                discriminator=discriminator,
                avatar_url=avatar_url,
                points=0,
                total_points_earned=0,
                total_messages=0
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            bot_logger.info(f"Nuevo usuario creado: {username} ({discord_id})")
        else:
            # Actualizar nombre y avatar si cambiaron
            if user.username != username:
                user.username = username
                user.discriminator = discriminator
            if avatar_url and user.avatar_url != avatar_url:
                user.avatar_url = avatar_url
            db.commit()
        
        return user
    
    @staticmethod
    def can_earn_points(db: Session, user: User) -> tuple[bool, str]:
        """
        Verificar si el usuario puede ganar puntos (cooldown y límite por hora)
        
        Args:
            db: Sesión de base de datos
            user: Usuario
        
        Returns:
            Tupla (puede_ganar, razón)
        """
        now = datetime.utcnow()
        
        # Verificar cooldown (último mensaje)
        last_activity = db.query(ActivityLog).filter(
            ActivityLog.user_id == user.id,
            ActivityLog.activity_type == 'message'
        ).order_by(ActivityLog.created_at.desc()).first()
        
        if last_activity:
            time_since_last = (now - last_activity.created_at).total_seconds()
            if time_since_last < MESSAGE_COOLDOWN:
                remaining = int(MESSAGE_COOLDOWN - time_since_last)
                return False, f"Cooldown activo. Espera {remaining}s"
        
        # Verificar límite por hora
        one_hour_ago = now - timedelta(hours=1)
        points_last_hour = db.query(func.sum(ActivityLog.points_awarded)).filter(
            ActivityLog.user_id == user.id,
            ActivityLog.created_at >= one_hour_ago
        ).scalar() or 0
        
        if points_last_hour >= MAX_POINTS_PER_HOUR:
            return False, f"Límite de {MAX_POINTS_PER_HOUR} puntos por hora alcanzado"
        
        return True, ""
    
    @staticmethod
    def award_points(
        db: Session, 
        user: User, 
        channel_id: int = None,
        points_override: int = None
    ) -> tuple[bool, int, str]:
        """
        Otorgar puntos a un usuario por actividad
        
        Args:
            db: Sesión de base de datos
            user: Usuario
            channel_id: ID del canal (opcional)
            points_override: Cantidad específica de puntos (opcional)
        
        Returns:
            Tupla (éxito, puntos_otorgados, mensaje)
        """
        # Verificar si puede ganar puntos
        can_earn, reason = PointsService.can_earn_points(db, user)
        if not can_earn:
            return False, 0, reason
        
        # Calcular puntos (con variación aleatoria)
        if points_override is not None:
            points = points_override
        else:
            # Variación de ±20% sobre POINTS_PER_MESSAGE
            variation = int(POINTS_PER_MESSAGE * 0.2)
            points = random.randint(
                POINTS_PER_MESSAGE - variation,
                POINTS_PER_MESSAGE + variation
            )
        
        # Actualizar usuario
        user.points += points
        user.total_points_earned += points
        user.total_messages += 1
        user.last_activity = datetime.utcnow()
        
        # Registrar actividad
        activity = ActivityLog(
            user_id=user.id,
            activity_type='message',
            channel_id=channel_id,
            points_awarded=points
        )
        db.add(activity)
        db.commit()
        
        bot_logger.info(f"Puntos otorgados: {user.username} +{points} pts (total: {user.points})")
        return True, points, f"¡Ganaste {points} puntos!"
    
    @staticmethod
    def add_points_admin(db: Session, user: User, points: int, admin_id: int) -> bool:
        """
        Añadir puntos manualmente (comando admin)
        
        Args:
            db: Sesión de base de datos
            user: Usuario
            points: Cantidad de puntos
            admin_id: ID del admin que ejecuta
        
        Returns:
            True si fue exitoso
        """
        if not validate_points(points):
            return False
        
        user.points += points
        if points > 0:
            user.total_points_earned += points
        user.updated_at = datetime.utcnow()
        
        # Registrar actividad
        activity = ActivityLog(
            user_id=user.id,
            activity_type='admin_adjustment',
            points_awarded=points
        )
        db.add(activity)
        db.commit()
        
        bot_logger.info(f"Admin {admin_id} ajustó puntos: {user.username} {points:+d} pts")
        return True
    
    @staticmethod
    def set_points_admin(db: Session, user: User, points: int, admin_id: int) -> bool:
        """
        Establecer puntos exactos (comando admin)
        
        Args:
            db: Sesión de base de datos
            user: Usuario
            points: Cantidad de puntos
            admin_id: ID del admin que ejecuta
        
        Returns:
            True si fue exitoso
        """
        if not validate_points(points):
            return False
        
        old_points = user.points
        user.points = points
        user.updated_at = datetime.utcnow()
        db.commit()
        
        bot_logger.info(f"Admin {admin_id} estableció puntos: {user.username} {old_points} -> {points}")
        return True
    
    @staticmethod
    def get_leaderboard(db: Session, limit: int = 10) -> list[User]:
        """
        Obtener top usuarios por puntos
        
        Args:
            db: Sesión de base de datos
            limit: Cantidad de usuarios a retornar
        
        Returns:
            Lista de usuarios ordenados por puntos
        """
        return db.query(User).order_by(User.points.desc()).limit(limit).all()
    
    @staticmethod
    def apply_inactivity_penalty(db: Session) -> int:
        """
        Aplicar penalización por inactividad a usuarios inactivos
        
        Args:
            db: Sesión de base de datos
        
        Returns:
            Cantidad de usuarios penalizados
        """
        cutoff_date = datetime.utcnow() - timedelta(days=INACTIVITY_DAYS)
        
        # Buscar usuarios inactivos con puntos > 0
        inactive_users = db.query(User).filter(
            User.last_activity < cutoff_date,
            User.points > 0
        ).all()
        
        penalized_count = 0
        for user in inactive_users:
            penalty = int(user.points * INACTIVITY_PENALTY)
            if penalty > 0:
                user.points -= penalty
                user.updated_at = datetime.utcnow()
                penalized_count += 1
                bot_logger.info(
                    f"Penalización por inactividad: {user.username} -{penalty} pts "
                    f"(inactivo desde {user.last_activity.date()})"
                )
        
        if penalized_count > 0:
            db.commit()
            bot_logger.info(f"Penalización aplicada a {penalized_count} usuarios")
        
        return penalized_count
    
    @staticmethod
    def get_user_stats(db: Session, user: User) -> dict:
        """
        Obtener estadísticas de un usuario
        
        Args:
            db: Sesión de base de datos
            user: Usuario
        
        Returns:
            Diccionario con estadísticas
        """
        # Ranking
        rank = db.query(func.count(User.id)).filter(User.points > user.points).scalar() + 1
        
        # Actividad reciente
        week_ago = datetime.utcnow() - timedelta(days=7)
        messages_this_week = db.query(func.count(ActivityLog.id)).filter(
            ActivityLog.user_id == user.id,
            ActivityLog.activity_type == 'message',
            ActivityLog.created_at >= week_ago
        ).scalar()
        
        return {
            'points': user.points,
            'total_earned': user.total_points_earned,
            'total_messages': user.total_messages,
            'rank': rank,
            'messages_this_week': messages_this_week,
            'member_since': user.joined_at,
            'last_activity': user.last_activity
        }
