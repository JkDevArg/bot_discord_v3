"""
Script para configurar webhook de Discord
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.database.connection import SessionLocal
from bot.database.channel_config import ChannelConfig

print("=" * 60)
print("CONFIGURAR WEBHOOK DE DISCORD")
print("=" * 60)
print()
print("Pasos para obtener la URL del webhook:")
print("1. Ve a Discord → Servidor → Canal #log_bot")
print("2. Clic derecho → Editar Canal")
print("3. Integraciones → Webhooks → Nuevo Webhook")
print("4. Copia la URL del webhook")
print()
print("=" * 60)
print()

webhook_url = input("Pega la URL del webhook aquí: ").strip()

if not webhook_url.startswith("https://discord.com/api/webhooks/"):
    print("\n❌ Error: La URL no parece ser un webhook válido de Discord")
    print("   Debe empezar con: https://discord.com/api/webhooks/")
    sys.exit(1)

db = SessionLocal()
try:
    config = db.query(ChannelConfig).filter(
        ChannelConfig.config_type == 'webhook_url'
    ).first()
    
    if config:
        config.channel_ids = webhook_url
        config.is_enabled = True
        print("\n✅ Webhook actualizado")
    else:
        config = ChannelConfig(
            config_type='webhook_url',
            channel_ids=webhook_url,
            is_enabled=True
        )
        db.add(config)
        print("\n✅ Webhook configurado")
    
    db.commit()
    
    print(f"\nWebhook URL: {webhook_url[:50]}...")
    print("\n🔄 Ahora reinicia el panel web:")
    print("   1. Presiona Ctrl+C en la terminal del panel web")
    print("   2. Ejecuta: python -m web.main")
    print("\n✅ Luego prueba en: http://localhost:8000/test-log")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    db.rollback()
finally:
    db.close()
