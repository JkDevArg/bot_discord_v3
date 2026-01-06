"""
Scheduler de tareas programadas
"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from bot.database.connection import SessionLocal
from bot.services.points_service import PointsService
from bot.services.event_service import EventService
from bot.tasks.backup import BackupService
from bot.utils.logger import bot_logger
import requests
from bot.config import HEALTHCHECK_BACKUP_URL, HEALTHCHECK_INACTIVITY_URL


class TaskScheduler:
    """Gestor de tareas programadas"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
    
    def setup_tasks(self):
        """Configurar todas las tareas programadas"""
        
        # Tarea diaria: Aplicar penalización por inactividad (03:00 AM)
        self.scheduler.add_job(
            self.apply_inactivity_penalty,
            CronTrigger(hour=3, minute=0),
            id='inactivity_penalty',
            name='Aplicar penalización por inactividad',
            replace_existing=True
        )
        
        # Tarea diaria: Backup automático (04:00 AM)
        self.scheduler.add_job(
            self.daily_backup,
            CronTrigger(hour=4, minute=0),
            id='daily_backup',
            name='Backup automático diario',
            replace_existing=True
        )
        
        # Tarea cada hora: Verificar eventos activos
        self.scheduler.add_job(
            self.check_events,
            CronTrigger(minute=0),  # Cada hora en punto
            id='check_events',
            name='Verificar eventos activos',
            replace_existing=True
        )
        
        # Tarea diaria: Limpiar backups antiguos (05:00 AM)
        self.scheduler.add_job(
            self.cleanup_backups,
            CronTrigger(hour=5, minute=0),
            id='cleanup_backups',
            name='Limpiar backups antiguos',
            replace_existing=True
        )
        
        bot_logger.info("Tareas programadas configuradas")
    
    async def apply_inactivity_penalty(self):
        """Aplicar penalización por inactividad"""
        try:
            bot_logger.info("Iniciando tarea: Penalización por inactividad")
            
            db = SessionLocal()
            try:
                penalized_count = PointsService.apply_inactivity_penalty(db)
                bot_logger.info(f"Penalización aplicada a {penalized_count} usuarios")
                
                # Notificar a healthcheck si está configurado
                if HEALTHCHECK_INACTIVITY_URL:
                    requests.get(HEALTHCHECK_INACTIVITY_URL, timeout=10)
            
            finally:
                db.close()
        
        except Exception as e:
            bot_logger.error(f"Error en tarea de inactividad: {e}", exc_info=e)
            if HEALTHCHECK_INACTIVITY_URL:
                requests.get(f"{HEALTHCHECK_INACTIVITY_URL}/fail", timeout=10)
    
    async def daily_backup(self):
        """Crear backup diario"""
        try:
            bot_logger.info("Iniciando tarea: Backup diario")
            
            success, backup_path, backup_size = BackupService.create_backup()
            
            if success:
                bot_logger.info(f"Backup completado: {backup_path} ({backup_size / 1024:.2f} KB)")
                
                # Notificar a healthcheck si está configurado
                if HEALTHCHECK_BACKUP_URL:
                    requests.get(HEALTHCHECK_BACKUP_URL, timeout=10)
            else:
                bot_logger.error("Backup falló")
                if HEALTHCHECK_BACKUP_URL:
                    requests.get(f"{HEALTHCHECK_BACKUP_URL}/fail", timeout=10)
        
        except Exception as e:
            bot_logger.error(f"Error en tarea de backup: {e}", exc_info=e)
            if HEALTHCHECK_BACKUP_URL:
                requests.get(f"{HEALTHCHECK_BACKUP_URL}/fail", timeout=10)
    
    async def check_events(self):
        """Verificar eventos activos y finalizarlos si es necesario"""
        try:
            bot_logger.info("Verificando eventos activos")
            
            db = SessionLocal()
            try:
                # Obtener eventos que deberían haber terminado
                now = datetime.utcnow()
                from bot.database.models import Event
                from sqlalchemy import and_
                
                events_to_finish = db.query(Event).filter(
                    and_(
                        Event.is_active == True,
                        Event.is_finished == False,
                        Event.end_time <= now
                    )
                ).all()
                
                for event in events_to_finish:
                    bot_logger.info(f"Finalizando evento: {event.name}")
                    eligible_count, winners = EventService.finish_event(db, event)
                    bot_logger.info(
                        f"Evento {event.name} finalizado: {eligible_count} participantes elegibles"
                    )
            
            finally:
                db.close()
        
        except Exception as e:
            bot_logger.error(f"Error verificando eventos: {e}", exc_info=e)
    
    async def cleanup_backups(self):
        """Limpiar backups antiguos"""
        try:
            bot_logger.info("Limpiando backups antiguos")
            BackupService.cleanup_old_backups()
        
        except Exception as e:
            bot_logger.error(f"Error limpiando backups: {e}", exc_info=e)
    
    def start(self):
        """Iniciar el scheduler"""
        self.scheduler.start()
        bot_logger.info("Scheduler de tareas iniciado")
    
    def shutdown(self):
        """Detener el scheduler"""
        self.scheduler.shutdown()
        bot_logger.info("Scheduler de tareas detenido")
