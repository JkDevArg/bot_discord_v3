"""
Script para crear webhook en el canal de anuncios correcto
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.database.connection import SessionLocal
from bot.database.channel_config import ChannelConfig

print("=" * 60)
print("CREAR WEBHOOK PARA CANAL DE ANUNCIOS")
print("=" * 60)
print()
print("Canal de anuncios: 1456918414214955058")
print()
print("Pasos:")
print("1. Ve a Discord → Canal #bot-anuncios")
print("2. Clic derecho → Editar Canal")
print("3. Integraciones → Webhooks → Nuevo Webhook")
print("4. Nombre: 'Anuncios de Nivel'")
print("5. Copia la URL del webhook")
print()
print("=" * 60)
print()

webhook_url = input("Pega la URL del webhook aquí: ").strip()

if not webhook_url.startswith("https://discord.com/api/webhooks/"):
    print("\n❌ Error: La URL no parece ser un webhook válido de Discord")
    sys.exit(1)

db = SessionLocal()
try:
    config = db.query(ChannelConfig).filter(
        ChannelConfig.config_type == 'announcement_webhook'
    ).first()
    
    if config:
        config.channel_ids = webhook_url
        config.is_enabled = True
        print("\n✅ Webhook actualizado")
    else:
        config = ChannelConfig(
            config_type='announcement_webhook',
            channel_ids=webhook_url,
            is_enabled=True
        )
        db.add(config)
        print("\n✅ Webhook configurado")
    
    db.commit()
    
    print(f"\nWebhook URL: {webhook_url[:50]}...")
    print("\n🔄 Reinicia el bot para aplicar cambios")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    db.rollback()
finally:
    db.close()
