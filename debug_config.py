"""
Script de prueba para verificar el logging a Discord
"""
import asyncio
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.database.connection import SessionLocal
from bot.database.channel_config import ChannelConfig
import json


def check_config():
    """Verificar configuración de canales"""
    db = SessionLocal()
    try:
        # Verificar canal de logs
        log_config = db.query(ChannelConfig).filter(
            ChannelConfig.config_type == 'log_channel'
        ).first()
        
        print("=" * 50)
        print("VERIFICACIÓN DE CONFIGURACIÓN")
        print("=" * 50)
        
        if log_config:
            print(f"\n✅ Canal de logs configurado:")
            print(f"   - ID en BD: {log_config.channel_ids}")
            print(f"   - Tipo: {log_config.config_type}")
            print(f"   - Habilitado: {log_config.is_enabled}")
            
            # Intentar parsear el ID
            try:
                if log_config.channel_ids.startswith('['):
                    channel_id = int(json.loads(log_config.channel_ids)[0])
                else:
                    channel_id = int(log_config.channel_ids)
                print(f"   - Channel ID parseado: {channel_id}")
            except Exception as e:
                print(f"   - ❌ Error parseando ID: {e}")
        else:
            print("\n❌ No hay canal de logs configurado")
        
        # Verificar otros canales
        all_configs = db.query(ChannelConfig).all()
        print(f"\n📋 Total de configuraciones: {len(all_configs)}")
        for config in all_configs:
            print(f"   - {config.config_type}: {config.channel_ids}")
        
    finally:
        db.close()


if __name__ == "__main__":
    check_config()
