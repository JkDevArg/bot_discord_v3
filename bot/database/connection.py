"""
Gestión de conexiones a la base de datos MySQL
"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from bot.config import DATABASE_URL
import os

# Asegurar que el directorio data existe
os.makedirs("data", exist_ok=True)

# Configuración específica de MySQL para seguridad y rendimiento
connect_args = {
    "charset": "utf8mb4",
    "use_unicode": True,
}

pool_config = {
    "pool_size": 10,  # Número de conexiones en el pool
    "max_overflow": 20,  # Conexiones adicionales permitidas
    "pool_timeout": 30,  # Timeout para obtener conexión del pool
    "pool_recycle": 3600,  # Reciclar conexiones cada hora
    "pool_pre_ping": True,  # Verificar conexión antes de usar
}

# Crear engine de SQLAlchemy con configuraciones optimizadas para MySQL
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args=connect_args,
    **pool_config
)

# Configurar modo SQL estricto para MySQL (seguridad adicional)
if "mysql" in DATABASE_URL:
    @event.listens_for(engine, "connect")
    def set_mysql_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        # Asegurar modo estricto y configuraciones de seguridad
        cursor.execute("SET SESSION sql_mode='STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION'")
        cursor.execute("SET SESSION innodb_strict_mode=ON")
        cursor.close()

# Crear session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Session con scope para thread-safety
ScopedSession = scoped_session(SessionLocal)

# Base para modelos
Base = declarative_base()

def get_db():
    """
    Dependency para obtener sesión de base de datos
    Uso: with get_db() as db: ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Inicializar base de datos creando todas las tablas"""
    from bot.database.models import (
        User, Role, UserRole, ShopItem, Purchase,
        Event, EventParticipant, AnnouncementConfig,
        AdminUser, AuditLog, ActivityLog, BackupLog, ItemCategory,
        DailyStats, DailyReward, LeaderboardHistory,
        ModerationConfig, FilteredWord, ModerationLog
    )
    Base.metadata.create_all(bind=engine)
    print("✓ Base de datos inicializada correctamente")

def drop_all():
    """CUIDADO: Elimina todas las tablas"""
    Base.metadata.drop_all(bind=engine)
    print("✓ Todas las tablas eliminadas")
