"""
Gestión de conexiones a la base de datos
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from bot.config import DATABASE_URL
import os

# Asegurar que el directorio data existe
os.makedirs("data", exist_ok=True)

# Crear engine de SQLAlchemy
# Crear engine de SQLAlchemy
connect_args = {}
if "sqlite" in DATABASE_URL:
    connect_args["check_same_thread"] = False

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    connect_args=connect_args
)

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
        AdminUser, AuditLog, ActivityLog, BackupLog
    )
    Base.metadata.create_all(bind=engine)
    print("✓ Base de datos inicializada correctamente")

def drop_all():
    """CUIDADO: Elimina todas las tablas"""
    Base.metadata.drop_all(bind=engine)
    print("✓ Todas las tablas eliminadas")
