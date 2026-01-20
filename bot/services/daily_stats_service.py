"""
Servicio para tracking automático de estadísticas diarias
"""
from datetime import datetime, timedelta
from sqlalchemy import func
from bot.database.connection import SessionLocal
from bot.database.models import User, DailyStats, ActivityLog
from bot.utils.logger import bot_logger


class DailyStatsService:
    """Servicio para actualizar estadísticas diarias"""
    
    @staticmethod
    def update_daily_stats(date: datetime = None):
        """
        Actualizar estadísticas del día especificado
        
        Args:
            date: Fecha a procesar (default: ayer)
        """
        db = SessionLocal()
        try:
            # Si no se especifica fecha, usar ayer
            if date is None:
                date = datetime.utcnow() - timedelta(days=1)
            
            # Normalizar a medianoche
            date = date.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Verificar si ya existe registro para esta fecha
            existing = db.query(DailyStats).filter(
                DailyStats.date == date
            ).first()
            
            if existing:
                bot_logger.info(f"Stats for {date.date()} already exist, updating...")
                stats = existing
            else:
                stats = DailyStats(date=date)
                db.add(stats)
            
            # Calcular rango del día
            day_start = date
            day_end = date + timedelta(days=1)
            
            # 1. Contar usuarios activos (que tuvieron actividad ese día)
            active_users = db.query(User).filter(
                User.last_activity >= day_start,
                User.last_activity < day_end
            ).count()
            
            # 2. Contar mensajes totales del día
            # Aproximación: usuarios activos * promedio de mensajes
            users_with_activity = db.query(User).filter(
                User.last_activity >= day_start,
                User.last_activity < day_end
            ).all()
            
            total_messages = sum(user.total_messages for user in users_with_activity)
            
            # 3. Calcular puntos otorgados
            # Aproximación: suma de puntos ganados por usuarios activos ese día
            points_awarded = 0
            for user in users_with_activity:
                # Estimación: si el usuario estuvo activo, asumimos que ganó puntos
                # En una implementación real, deberías tener un log de puntos
                points_awarded += user.total_points_earned
            
            # 4. Contar nuevos usuarios
            new_users = db.query(User).filter(
                User.created_at >= day_start,
                User.created_at < day_end
            ).count()
            
            # Actualizar stats
            stats.active_users = active_users
            stats.total_messages = total_messages
            stats.points_awarded = points_awarded
            stats.new_users = new_users
            
            db.commit()
            
            bot_logger.info(
                f"Daily stats updated for {date.date()}: "
                f"{active_users} users, {total_messages} messages, "
                f"{points_awarded} points, {new_users} new users"
            )
            
            return stats
            
        except Exception as e:
            bot_logger.error(f"Error updating daily stats: {e}", exc_info=e)
            db.rollback()
            raise
        finally:
            db.close()
    
    @staticmethod
    def backfill_stats(days: int = 30):
        """
        Rellenar estadísticas de los últimos N días
        
        Args:
            days: Número de días hacia atrás a procesar
        """
        bot_logger.info(f"Backfilling stats for last {days} days...")
        
        for i in range(days, 0, -1):
            date = datetime.utcnow() - timedelta(days=i)
            try:
                DailyStatsService.update_daily_stats(date)
            except Exception as e:
                bot_logger.error(f"Error backfilling day {date.date()}: {e}")
        
        bot_logger.info("Backfill completed")
    
    @staticmethod
    def get_stats_summary(days: int = 7):
        """
        Obtener resumen de estadísticas de los últimos N días
        
        Args:
            days: Número de días a incluir
            
        Returns:
            Lista de DailyStats
        """
        db = SessionLocal()
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            stats = db.query(DailyStats).filter(
                DailyStats.date >= start_date
            ).order_by(DailyStats.date.desc()).all()
            
            return stats
        finally:
            db.close()
