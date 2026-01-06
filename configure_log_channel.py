"""
Script para configurar el canal de logs directamente
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.database.connection import SessionLocal
from bot.database.channel_config import ChannelConfig


def configure_log_channel():
    """Configurar canal de logs"""
    db = SessionLocal()
    try:
        # Pedir el ID del canal
        print("=" * 50)
        print("CONFIGURAR CANAL DE LOGS")
        print("=" * 50)
        print("\nPor favor, ingresa el ID del canal #log_bot de Discord:")
        print("(Haz clic derecho en el canal -> Copiar ID)")
        print()
        
        channel_id = input("ID del canal: ").strip()
        
        if not channel_id.isdigit():
            print("❌ Error: El ID debe ser un número")
            return
        
        # Buscar configuración existente
        config = db.query(ChannelConfig).filter(
            ChannelConfig.config_type == 'log_channel'
        ).first()
        
        if config:
            print(f"\n📝 Actualizando configuración existente...")
            config.channel_ids = channel_id
            config.is_enabled = True
        else:
            print(f"\n✨ Creando nueva configuración...")
            config = ChannelConfig(
                config_type='log_channel',
                channel_ids=channel_id,
                is_enabled=True
            )
            db.add(config)
        
        db.commit()
        
        print(f"\n✅ Canal de logs configurado correctamente!")
        print(f"   - Channel ID: {channel_id}")
        print(f"   - Tipo: log_channel")
        print(f"   - Estado: Habilitado")
        print("\n🔄 Ahora reinicia el panel web para aplicar los cambios")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    configure_log_channel()
