"""
Script de debug completo para Discord logging
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.database.connection import SessionLocal
from bot.database.channel_config import ChannelConfig
from web.discord_integration import DiscordIntegrationService
import discord


async def test_discord_logging():
    """Probar el sistema de logging a Discord"""
    
    print("=" * 60)
    print("DEBUG: SISTEMA DE LOGGING A DISCORD")
    print("=" * 60)
    
    # 1. Verificar configuración en BD
    print("\n[1/5] Verificando configuración en base de datos...")
    db = SessionLocal()
    try:
        config = db.query(ChannelConfig).filter(
            ChannelConfig.config_type == 'log_channel'
        ).first()
        
        if not config:
            print("   ❌ ERROR: No hay configuración de canal de logs")
            return
        
        print(f"   ✅ Configuración encontrada")
        print(f"      - Channel IDs: {config.channel_ids}")
        print(f"      - Habilitado: {config.is_enabled}")
        
        channel_id = int(config.channel_ids)
        print(f"      - Channel ID parseado: {channel_id}")
        
    finally:
        db.close()
    
    # 2. Verificar instancia del bot
    print("\n[2/5] Verificando instancia del bot...")
    if not DiscordIntegrationService._bot_instance:
        print("   ❌ ERROR: Bot instance no está configurada")
        print("      El bot debe estar corriendo para que esto funcione")
        return
    
    bot = DiscordIntegrationService._bot_instance
    print(f"   ✅ Bot instance encontrada: {bot.user}")
    print(f"      - Bot ID: {bot.user.id}")
    print(f"      - Bot conectado: {not bot.is_closed()}")
    
    # 3. Verificar acceso al canal
    print(f"\n[3/5] Verificando acceso al canal {channel_id}...")
    channel = bot.get_channel(channel_id)
    
    if not channel:
        print(f"   ❌ ERROR: No se pudo encontrar el canal {channel_id}")
        print("      Verifica que:")
        print("      - El ID del canal sea correcto")
        print("      - El bot esté en el servidor")
        print("      - El bot tenga acceso al canal")
        return
    
    print(f"   ✅ Canal encontrado: #{channel.name}")
    print(f"      - Tipo: {channel.type}")
    print(f"      - Servidor: {channel.guild.name}")
    
    # 4. Verificar permisos
    print(f"\n[4/5] Verificando permisos del bot en el canal...")
    permissions = channel.permissions_for(channel.guild.me)
    
    print(f"   - Ver canal: {'✅' if permissions.view_channel else '❌'}")
    print(f"   - Enviar mensajes: {'✅' if permissions.send_messages else '❌'}")
    print(f"   - Embeds: {'✅' if permissions.embed_links else '❌'}")
    
    if not permissions.send_messages:
        print("\n   ❌ ERROR: El bot NO tiene permiso para enviar mensajes")
        print("      Solución: Da permisos de 'Enviar Mensajes' al bot en este canal")
        return
    
    # 5. Intentar enviar mensaje de prueba
    print(f"\n[5/5] Intentando enviar mensaje de prueba...")
    try:
        embed = discord.Embed(
            title="🧪 Mensaje de Prueba",
            description="Si ves esto, el sistema de logging funciona correctamente",
            color=discord.Color.green()
        )
        embed.add_field(name="Estado", value="✅ Sistema operativo", inline=False)
        embed.add_field(name="Timestamp", value=discord.utils.format_dt(discord.utils.utcnow()), inline=False)
        
        await channel.send(embed=embed)
        
        print("   ✅ ¡MENSAJE ENVIADO CORRECTAMENTE!")
        print("\n" + "=" * 60)
        print("✅ DIAGNÓSTICO COMPLETO")
        print("=" * 60)
        print("El sistema está funcionando correctamente.")
        print("Deberías ver un mensaje de prueba en #log_bot")
        
    except discord.Forbidden:
        print("   ❌ ERROR: Permiso denegado")
        print("      El bot no tiene permisos para enviar mensajes en este canal")
    except Exception as e:
        print(f"   ❌ ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # Necesitamos importar el bot para tener acceso a su event loop
    print("Esperando a que el bot esté listo...")
    print("Asegúrate de que el bot esté corriendo en otra terminal\n")
    
    try:
        asyncio.run(test_discord_logging())
    except KeyboardInterrupt:
        print("\n\nDebug interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
