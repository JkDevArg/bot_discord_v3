# Guía para configurar el Webhook de Discord

## Paso 1: Crear el Webhook en Discord

1. Ve a Discord y abre tu servidor
2. Haz clic derecho en el canal `#log_bot`
3. Selecciona "Editar Canal"
4. Ve a la pestaña "Integraciones"
5. Click en "Webhooks"
6. Click en "Nuevo Webhook"
7. Dale un nombre (ej: "Panel Web Logs")
8. **Copia la URL del Webhook** (se ve así: `https://discord.com/api/webhooks/...`)

## Paso 2: Configurar el Webhook en el sistema

Ejecuta este comando reemplazando `TU_WEBHOOK_URL` con la URL que copiaste:

```powershell
cd G:\PROYECTOS\botdiscord
.\venv\Scripts\activate
python -c "from bot.database.connection import SessionLocal; from bot.database.channel_config import ChannelConfig; db = SessionLocal(); config = db.query(ChannelConfig).filter(ChannelConfig.config_type == 'webhook_url').first(); config.channel_ids = 'TU_WEBHOOK_URL' if config else None; db.add(ChannelConfig(config_type='webhook_url', channel_ids='TU_WEBHOOK_URL', is_enabled=True)) if not config else None; db.commit(); print('✅ Webhook configurado'); db.close()"
```

O usa este script más simple:

```powershell
python configure_webhook.py
```

## Paso 3: Reiniciar el panel web

```powershell
# Detén el panel web (Ctrl+C)
# Luego reinicia:
python -m web.main
```

## Paso 4: Probar

1. Ve a http://localhost:8000/test-log
2. Click en "Enviar Mensaje de Prueba"
3. Revisa #log_bot - deberías ver el mensaje

¡Listo! Ahora todos los cambios de puntos/niveles se registrarán automáticamente en Discord.
