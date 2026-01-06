"""
Script para configurar canal de logs directamente
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.database.connection import SessionLocal
from bot.database.channel_config import ChannelConfig

db = SessionLocal()
try:
    # Buscar o crear configuración
    config = db.query(ChannelConfig).filter(
        ChannelConfig.config_type == 'log_channel'
    ).first()
    
    if config:
        config.channel_ids = '1456918568263221279'
        config.is_enabled = True
        print("✅ Configuración actualizada")
    else:
        config = ChannelConfig(
            config_type='log_channel',
            channel_ids='1456918568263221279',
            is_enabled=True
        )
        db.add(config)
        print("✅ Configuración creada")
    
    db.commit()
    print(f"Canal de logs: 1456918568263221279")
    
except Exception as e:
    print(f"❌ Error: {e}")
    db.rollback()
finally:
    db.close()
