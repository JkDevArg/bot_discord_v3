#!/usr/bin/env python3
"""
Script para crear un usuario administrador en el panel web
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.database.connection import SessionLocal
from bot.database.models import AdminUser
from bot.utils.security import hash_password


def create_admin_user(username: str, password: str, discord_id: int = None):
    """
    Crear un usuario administrador
    
    Args:
        username: Nombre de usuario
        password: Contraseña
        discord_id: ID de Discord (opcional)
    """
    db = SessionLocal()
    
    try:
        # Verificar si el usuario ya existe
        existing_user = db.query(AdminUser).filter(
            AdminUser.username == username
        ).first()
        
        if existing_user:
            print(f"❌ Error: El usuario '{username}' ya existe")
            return False
        
        # Crear hash de la contraseña
        password_hash = hash_password(password)
        
        # Crear nuevo usuario admin
        admin_user = AdminUser(
            username=username,
            password_hash=password_hash,
            discord_id=discord_id,
            is_active=True,
            mfa_enabled=False
        )
        
        db.add(admin_user)
        db.commit()
        
        print(f"✅ Usuario administrador creado exitosamente!")
        print(f"   Username: {username}")
        print(f"   Discord ID: {discord_id if discord_id else 'No configurado'}")
        print(f"\n🔐 Puedes iniciar sesión en el panel web con estas credenciales")
        
        return True
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error al crear usuario: {e}")
        return False
    finally:
        db.close()


def main():
    """Función principal"""
    print("=" * 60)
    print("🔧 Creador de Usuario Administrador - Panel Web")
    print("=" * 60)
    print()
    
    # Solicitar datos
    username = input("Ingresa el nombre de usuario: ").strip()
    if not username:
        print("❌ El nombre de usuario no puede estar vacío")
        return
    
    password = input("Ingresa la contraseña: ").strip()
    if not password:
        print("❌ La contraseña no puede estar vacía")
        return
    
    if len(password) < 6:
        print("⚠️  Advertencia: Se recomienda una contraseña de al menos 6 caracteres")
        confirm = input("¿Continuar de todos modos? (s/n): ").strip().lower()
        if confirm != 's':
            print("❌ Operación cancelada")
            return
    
    discord_id_input = input("Ingresa tu Discord ID (opcional, presiona Enter para omitir): ").strip()
    discord_id = int(discord_id_input) if discord_id_input else None
    
    print()
    print("Creando usuario...")
    create_admin_user(username, password, discord_id)


if __name__ == "__main__":
    main()
