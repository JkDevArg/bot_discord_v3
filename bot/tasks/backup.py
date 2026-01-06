"""
Sistema de backups automáticos
"""
import os
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from bot.database.connection import SessionLocal
from bot.database.models import BackupLog
from bot.config import BACKUP_ENABLED, BACKUP_RETENTION_DAYS
from bot.utils.logger import backup_logger


class BackupService:
    """Servicio para gestionar backups de la base de datos"""
    
    BACKUP_DIR = Path("backups")
    DB_PATH = Path("data/bot.db")
    
    @staticmethod
    def ensure_backup_dir():
        """Asegurar que el directorio de backups existe"""
        BackupService.BACKUP_DIR.mkdir(exist_ok=True)
    
    @staticmethod
    def create_backup() -> tuple[bool, str, int]:
        """
        Crear backup de la base de datos
        
        Returns:
            Tupla (éxito, ruta_backup, tamaño_bytes)
        """
        if not BACKUP_ENABLED:
            backup_logger.info("Backups desactivados en configuración")
            return False, "", 0
        
        try:
            BackupService.ensure_backup_dir()
            
            # Generar nombre de archivo con timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            backup_filename = f"bot_backup_{timestamp}.db.gz"
            backup_path = BackupService.BACKUP_DIR / backup_filename
            
            # Verificar que la base de datos existe
            if not BackupService.DB_PATH.exists():
                backup_logger.error(f"Base de datos no encontrada: {BackupService.DB_PATH}")
                return False, "", 0
            
            # Crear backup comprimido
            with open(BackupService.DB_PATH, 'rb') as f_in:
                with gzip.open(backup_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Obtener tamaño del backup
            backup_size = backup_path.stat().st_size
            
            # Verificar integridad (que el archivo se creó correctamente)
            if backup_size == 0:
                backup_logger.error("Backup creado pero está vacío")
                backup_path.unlink()
                return False, "", 0
            
            backup_logger.info(
                f"Backup creado exitosamente: {backup_filename} ({backup_size / 1024:.2f} KB)"
            )
            
            # Registrar en base de datos
            BackupService.log_backup(str(backup_path), backup_size, True)
            
            return True, str(backup_path), backup_size
        
        except Exception as e:
            backup_logger.error(f"Error creando backup: {e}", exc_info=e)
            BackupService.log_backup("", 0, False, str(e))
            return False, "", 0
    
    @staticmethod
    def log_backup(backup_path: str, file_size: int, success: bool, error_message: str = None):
        """Registrar backup en la base de datos"""
        db = SessionLocal()
        try:
            log = BackupLog(
                backup_path=backup_path,
                file_size=file_size,
                success=success,
                error_message=error_message
            )
            db.add(log)
            db.commit()
        except Exception as e:
            backup_logger.error(f"Error registrando backup en BD: {e}")
        finally:
            db.close()
    
    @staticmethod
    def cleanup_old_backups():
        """Eliminar backups antiguos según política de retención"""
        try:
            BackupService.ensure_backup_dir()
            
            cutoff_date = datetime.now() - timedelta(days=BACKUP_RETENTION_DAYS)
            deleted_count = 0
            
            # Listar todos los backups
            for backup_file in BackupService.BACKUP_DIR.glob("bot_backup_*.db.gz"):
                # Obtener fecha de modificación
                file_mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
                
                if file_mtime < cutoff_date:
                    backup_file.unlink()
                    deleted_count += 1
                    backup_logger.info(f"Backup antiguo eliminado: {backup_file.name}")
            
            if deleted_count > 0:
                backup_logger.info(f"Se eliminaron {deleted_count} backups antiguos")
        
        except Exception as e:
            backup_logger.error(f"Error limpiando backups antiguos: {e}")
    
    @staticmethod
    def get_backup_stats() -> dict:
        """Obtener estadísticas de backups"""
        try:
            BackupService.ensure_backup_dir()
            
            backups = list(BackupService.BACKUP_DIR.glob("bot_backup_*.db.gz"))
            total_backups = len(backups)
            
            if total_backups == 0:
                return {
                    'total_backups': 0,
                    'total_size_mb': 0,
                    'latest_backup': None,
                    'oldest_backup': None
                }
            
            total_size = sum(b.stat().st_size for b in backups)
            latest_backup = max(backups, key=lambda b: b.stat().st_mtime)
            oldest_backup = min(backups, key=lambda b: b.stat().st_mtime)
            
            return {
                'total_backups': total_backups,
                'total_size_mb': total_size / (1024 * 1024),
                'latest_backup': latest_backup.name,
                'latest_backup_date': datetime.fromtimestamp(latest_backup.stat().st_mtime),
                'oldest_backup': oldest_backup.name,
                'oldest_backup_date': datetime.fromtimestamp(oldest_backup.stat().st_mtime)
            }
        
        except Exception as e:
            backup_logger.error(f"Error obteniendo estadísticas de backup: {e}")
            return {}
    
    @staticmethod
    def restore_backup(backup_filename: str) -> bool:
        """
        Restaurar backup (CUIDADO: sobrescribe la base de datos actual)
        
        Args:
            backup_filename: Nombre del archivo de backup
        
        Returns:
            True si fue exitoso
        """
        try:
            backup_path = BackupService.BACKUP_DIR / backup_filename
            
            if not backup_path.exists():
                backup_logger.error(f"Backup no encontrado: {backup_filename}")
                return False
            
            # Crear backup de seguridad de la BD actual antes de restaurar
            current_backup = BackupService.DB_PATH.with_suffix('.db.before_restore')
            shutil.copy2(BackupService.DB_PATH, current_backup)
            
            # Descomprimir y restaurar
            with gzip.open(backup_path, 'rb') as f_in:
                with open(BackupService.DB_PATH, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            backup_logger.info(f"Backup restaurado exitosamente: {backup_filename}")
            backup_logger.info(f"Backup de seguridad guardado en: {current_backup}")
            
            return True
        
        except Exception as e:
            backup_logger.error(f"Error restaurando backup: {e}", exc_info=e)
            return False
