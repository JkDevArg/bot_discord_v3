"""
Servicio de gestión de niveles y experiencia
"""
from sqlalchemy.orm import Session
from bot.database.models import User, ActivityLog
from bot.utils.logger import bot_logger
from datetime import datetime
import math


class LevelService:
    """Servicio para gestionar niveles y experiencia"""
    
    # Configuración del sistema de niveles
    BASE_EXP = 100  # EXP base para nivel 2
    EXP_MULTIPLIER = 1.8  # Multiplicador por nivel (aumentado para más dificultad)
    EXP_PER_MESSAGE = 15  # EXP por mensaje
    
    @staticmethod
    def calculate_exp_for_level(level: int) -> int:
        """
        Calcular EXP necesaria para alcanzar un nivel
        
        Fórmula progresiva: BASE_EXP * (level - 1) ^ EXP_MULTIPLIER
        Cada nivel es progresivamente más difícil
        
        Args:
            level: Nivel objetivo
        
        Returns:
            EXP total necesaria desde nivel 1
        """
        if level <= 1:
            return 0
        
        total_exp = 0
        for lvl in range(2, level + 1):
            # Dificultad progresiva: cada nivel requiere más EXP
            total_exp += int(LevelService.BASE_EXP * math.pow(lvl - 1, LevelService.EXP_MULTIPLIER))
        
        return total_exp
    
    @staticmethod
    def calculate_exp_to_next_level(current_level: int, current_exp: int) -> int:
        """
        Calcular EXP faltante para el siguiente nivel
        
        Args:
            current_level: Nivel actual
            current_exp: EXP actual
        
        Returns:
            EXP faltante para siguiente nivel
        """
        exp_for_next = LevelService.calculate_exp_for_level(current_level + 1)
        return exp_for_next - current_exp
    
    @staticmethod
    def calculate_level_from_exp(total_exp: int) -> int:
        """
        Calcular nivel basado en EXP total
        
        Args:
            total_exp: EXP total acumulada
        
        Returns:
            Nivel correspondiente
        """
        level = 1
        while LevelService.calculate_exp_for_level(level + 1) <= total_exp:
            level += 1
        return level
    
    @staticmethod
    def create_progress_bar(percentage: float, length: int = 10) -> str:
        """
        Crear barra de progreso visual
        
        Args:
            percentage: Porcentaje de progreso (0-100)
            length: Longitud de la barra
        
        Returns:
            Barra de progreso en string
        """
        filled = int(length * percentage / 100)
        empty = length - filled
        return f"[{'█' * filled}{'░' * empty}]"
    
    @staticmethod
    def award_exp(
        db: Session,
        user: User,
        exp_amount: int = None
    ) -> tuple[bool, int, bool, int]:
        """
        Otorgar experiencia a un usuario
        
        Args:
            db: Sesión de base de datos
            user: Usuario
            exp_amount: Cantidad de EXP (None = usar default)
        
        Returns:
            Tupla (éxito, exp_otorgada, subió_nivel, nivel_nuevo)
        """
        if exp_amount is None:
            exp_amount = LevelService.EXP_PER_MESSAGE
        
        old_level = user.level
        
        # Añadir EXP
        user.exp += exp_amount
        user.total_exp_earned += exp_amount
        
        # Calcular nuevo nivel
        new_level = LevelService.calculate_level_from_exp(user.exp)
        leveled_up = new_level > old_level
        
        if leveled_up:
            user.level = new_level
            
            # Bonificación cada 10 niveles
            bonus_points = 0
            if new_level % 10 == 0:
                bonus_points = 5
                user.points += bonus_points
                bot_logger.info(
                    f"🎁 ¡Bonificación! {user.username} recibió +{bonus_points} puntos por alcanzar nivel {new_level}"
                )
            
            bot_logger.info(
                f"¡Level UP! {user.username}: Nivel {old_level} -> {new_level} "
                f"({user.exp} EXP total){f' +{bonus_points} puntos' if bonus_points > 0 else ''}"
            )
        
        user.updated_at = datetime.utcnow()
        db.commit()
        
        return True, exp_amount, leveled_up, new_level
    
    @staticmethod
    def add_exp_admin(db: Session, user: User, exp: int, admin_id: int) -> bool:
        """
        Añadir EXP manualmente (comando admin)
        
        Args:
            db: Sesión de base de datos
            user: Usuario
            exp: Cantidad de EXP
            admin_id: ID del admin que ejecuta
        
        Returns:
            True si fue exitoso
        """
        old_level = user.level
        
        user.exp += exp
        if exp > 0:
            user.total_exp_earned += exp
        
        # Recalcular nivel
        user.level = LevelService.calculate_level_from_exp(user.exp)
        user.updated_at = datetime.utcnow()
        db.commit()
        
        bot_logger.info(
            f"Admin {admin_id} ajustó EXP: {user.username} {exp:+d} EXP "
            f"(Nivel {old_level} -> {user.level})"
        )
        return True
    
    @staticmethod
    def set_level_admin(db: Session, user: User, level: int, admin_id: int) -> bool:
        """
        Establecer nivel exacto (comando admin)
        
        Args:
            db: Sesión de base de datos
            user: Usuario
            level: Nivel objetivo
            admin_id: ID del admin que ejecuta
        
        Returns:
            True si fue exitoso
        """
        if level < 1:
            level = 1
        
        old_level = user.level
        
        # Calcular EXP necesaria para ese nivel
        user.exp = LevelService.calculate_exp_for_level(level)
        user.level = level
        user.updated_at = datetime.utcnow()
        db.commit()
        
        bot_logger.info(
            f"Admin {admin_id} estableció nivel: {user.username} "
            f"Nivel {old_level} -> {level}"
        )
        return True
    
    @staticmethod
    def get_level_leaderboard(db: Session, limit: int = 10) -> list[User]:
        """
        Obtener top usuarios por nivel
        
        Args:
            db: Sesión de base de datos
            limit: Cantidad de usuarios a retornar
        
        Returns:
            Lista de usuarios ordenados por nivel y EXP
        """
        return db.query(User).order_by(
            User.level.desc(),
            User.exp.desc()
        ).limit(limit).all()
    
    @staticmethod
    def get_level_stats(db: Session, user: User) -> dict:
        """
        Obtener estadísticas de nivel de un usuario
        
        Args:
            db: Sesión de base de datos
            user: Usuario
        
        Returns:
            Diccionario con estadísticas
        """
        from sqlalchemy import func
        
        # Ranking por nivel
        rank = db.query(func.count(User.id)).filter(
            (User.level > user.level) |
            ((User.level == user.level) & (User.exp > user.exp))
        ).scalar() + 1
        
        # EXP para siguiente nivel
        exp_to_next = LevelService.calculate_exp_to_next_level(user.level, user.exp)
        exp_for_next_level = LevelService.calculate_exp_for_level(user.level + 1)
        exp_for_current_level = LevelService.calculate_exp_for_level(user.level)
        
        # Progreso en el nivel actual (%)
        exp_in_current_level = user.exp - exp_for_current_level
        exp_needed_for_level = exp_for_next_level - exp_for_current_level
        progress_percentage = (exp_in_current_level / exp_needed_for_level * 100) if exp_needed_for_level > 0 else 100
        
        return {
            'level': user.level,
            'exp': user.exp,
            'total_exp_earned': user.total_exp_earned,
            'exp_to_next_level': exp_to_next,
            'exp_in_current_level': exp_in_current_level,
            'exp_needed_for_level': exp_needed_for_level,
            'progress_percentage': round(progress_percentage, 1),
            'rank': rank
        }
    
    @staticmethod
    def get_level_rewards(level: int) -> dict:
        """
        Obtener recompensas por alcanzar un nivel
        
        Args:
            level: Nivel alcanzado
        
        Returns:
            Diccionario con recompensas
        """
        rewards = {
            'points': 0,
            'title': None,
            'special': None
        }
        
        # Bonificación cada 10 niveles: +5 puntos
        if level % 10 == 0:
            rewards['points'] = 5
            rewards['special'] = f"🎁 ¡Bonificación de nivel {level}!"
        
        # Títulos especiales
        level_titles = {
            5: "🌱 Novato",
            10: "⚔️ Guerrero",
            15: "🛡️ Veterano",
            20: "👑 Élite",
            25: "💎 Maestro",
            30: "🔥 Leyenda",
            50: "⭐ Mítico",
            75: "🌟 Divino",
            100: "🏆 Inmortal"
        }
        
        if level in level_titles:
            rewards['title'] = level_titles[level]
        
        return rewards
