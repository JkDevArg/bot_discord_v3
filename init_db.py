# Script de inicialización de base de datos
"""
Script para inicializar la base de datos y crear datos de ejemplo
"""
import sys
sys.path.insert(0, '.')

from bot.database.connection import init_db, SessionLocal
from bot.database.models import AdminUser, AnnouncementConfig
from bot.utils.security import hash_password
from bot.utils.logger import bot_logger

def create_admin_user():
    """Crear usuario administrador por defecto"""
    db = SessionLocal()
    try:
        # Verificar si ya existe un admin
        existing = db.query(AdminUser).filter(AdminUser.username == 'admin').first()
        if existing:
            print("⚠️  Usuario 'admin' ya existe")
            return
        
        admin = AdminUser(
            username='admin',
            password_hash=hash_password('admin123'),
            is_active=True,
            mfa_enabled=False
        )
        db.add(admin)
        db.commit()
        print("✅ Usuario admin creado:")
        print("   Usuario: admin")
        print("   Contraseña: admin123")
        print("   ⚠️  CAMBIA LA CONTRASEÑA DESPUÉS DEL PRIMER LOGIN")
    
    except Exception as e:
        print(f"❌ Error creando admin: {e}")
        db.rollback()
    finally:
        db.close()

def create_announcement_configs():
    """Crear configuraciones de anuncios por defecto"""
    db = SessionLocal()
    try:
        # Nota: Debes cambiar estos IDs de canal por los de tu servidor
        configs = [
            ('level_up', 0, False),  # Cambiar 0 por ID de canal real
            ('purchase', 0, False),
            ('event', 0, False)
        ]
        
        for ann_type, channel_id, enabled in configs:
            existing = db.query(AnnouncementConfig).filter(
                AnnouncementConfig.announcement_type == ann_type
            ).first()
            
            if not existing:
                config = AnnouncementConfig(
                    announcement_type=ann_type,
                    channel_id=channel_id,
                    is_enabled=enabled
                )
                db.add(config)
        
        db.commit()
        print("✅ Configuraciones de anuncios creadas")
        print("   ⚠️  Configura los IDs de canal desde el panel web")
    
    except Exception as e:
        print(f"❌ Error creando configs: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 50)
    print("Inicializando Base de Datos")
    print("=" * 50)
    
    # Inicializar base de datos
    print("\n1. Creando tablas...")
    init_db()
    
    # Crear usuario admin
    print("\n2. Creando usuario administrador...")
    create_admin_user()
    
    # Crear configuraciones
    print("\n3. Creando configuraciones...")
    create_announcement_configs()
    
    print("\n" + "=" * 50)
    print("✅ Inicialización completada")
    print("=" * 50)
    print("\nPróximos pasos:")
    print("1. Configura tu .env con el token de Discord")
    print("2. Inicia el bot: python -m bot.main")
    print("3. Inicia el panel web: python -m web.main")
    print("4. Configura los canales de anuncios desde el panel web")
