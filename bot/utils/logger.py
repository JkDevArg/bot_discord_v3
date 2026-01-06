"""
Sistema de logging centralizado
"""
import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime

# Crear directorio de logs si no existe
os.makedirs("logs", exist_ok=True)

def setup_logger(name: str, log_file: str, level=logging.INFO) -> logging.Logger:
    """
    Configurar logger con rotación de archivos
    
    Args:
        name: Nombre del logger
        log_file: Ruta del archivo de log
        level: Nivel de logging (default: INFO)
    
    Returns:
        Logger configurado
    """
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para archivo con rotación
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Configurar logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Crear loggers principales
bot_logger = setup_logger('bot', 'logs/bot.log')
web_logger = setup_logger('web', 'logs/web.log')
audit_logger = setup_logger('audit', 'logs/audit.log')
backup_logger = setup_logger('backup', 'logs/backup.log')

def log_audit(admin_username: str, action: str, details: str = ""):
    """Helper para logs de auditoría"""
    audit_logger.info(f"[{admin_username}] {action} - {details}")
