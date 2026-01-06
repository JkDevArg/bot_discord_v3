"""
Configuración centralizada del bot de Discord
Carga todas las variables de entorno y proporciona valores por defecto
"""
import os
from typing import List
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Discord Configuration
DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")
DISCORD_GUILD_ID: int = int(os.getenv("DISCORD_GUILD_ID", "0"))

# Admin Configuration
ADMIN_USER_IDS: List[int] = [
    int(uid.strip()) 
    for uid in os.getenv("ADMIN_USER_IDS", "").split(",") 
    if uid.strip()
]

# Points System Configuration
POINTS_PER_MESSAGE: int = int(os.getenv("POINTS_PER_MESSAGE", "10"))
MESSAGE_COOLDOWN: int = int(os.getenv("MESSAGE_COOLDOWN", "60"))  # segundos
MAX_POINTS_PER_HOUR: int = int(os.getenv("MAX_POINTS_PER_HOUR", "100"))
INACTIVITY_DAYS: int = int(os.getenv("INACTIVITY_DAYS", "60"))
INACTIVITY_PENALTY: float = float(os.getenv("INACTIVITY_PENALTY", "0.25"))

# Database Configuration
DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///data/bot.db")

# Web Panel Configuration
WEB_SECRET_KEY: str = os.getenv("WEB_SECRET_KEY", "change-me-in-production")
WEB_HOST: str = os.getenv("WEB_HOST", "0.0.0.0")
WEB_PORT: int = int(os.getenv("WEB_PORT", "8000"))

# Backup Configuration
BACKUP_ENABLED: bool = os.getenv("BACKUP_ENABLED", "true").lower() == "true"
BACKUP_RETENTION_DAYS: int = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))

# Monitoring Configuration (opcional)
SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")
HEALTHCHECK_BACKUP_URL: str = os.getenv("HEALTHCHECK_BACKUP_URL", "")
HEALTHCHECK_INACTIVITY_URL: str = os.getenv("HEALTHCHECK_INACTIVITY_URL", "")
DISCORD_WEBHOOK_ALERTS: str = os.getenv("DISCORD_WEBHOOK_ALERTS", "")

# Environment
ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

# Validación de configuración crítica
def validate_config() -> None:
    """Valida que la configuración crítica esté presente"""
    errors = []
    
    if not DISCORD_TOKEN:
        errors.append("DISCORD_TOKEN no está configurado")
    
    if DISCORD_GUILD_ID == 0:
        errors.append("DISCORD_GUILD_ID no está configurado")
    
    if not ADMIN_USER_IDS:
        errors.append("ADMIN_USER_IDS no está configurado")
    
    if ENVIRONMENT == "production" and WEB_SECRET_KEY == "change-me-in-production":
        errors.append("WEB_SECRET_KEY debe cambiarse en producción")
    
    if errors:
        raise ValueError(
            "Errores de configuración:\n" + "\n".join(f"- {e}" for e in errors)
        )

# Validar al importar
if __name__ != "__main__":
    validate_config()
