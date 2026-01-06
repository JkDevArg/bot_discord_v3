"""
Bot principal de Discord
"""
import discord
from discord.ext import commands
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.config import DISCORD_TOKEN, DISCORD_GUILD_ID, ENVIRONMENT
from bot.utils.logger import bot_logger
from bot.database.connection import init_db

# Configurar intents
intents = discord.Intents.default()
intents.message_content = True  # Necesario para leer contenido de mensajes
intents.members = True  # Necesario para eventos de miembros
intents.presences = True  # Necesario para detectar presencia en eventos

# Crear bot con prefijo de comandos
bot = commands.Bot(
    command_prefix='/',
    intents=intents,
    help_command=None  # Desactivar comando de ayuda por defecto
)


@bot.event
async def on_ready():
    """Evento cuando el bot está listo"""
    bot_logger.info(f'Bot conectado como {bot.user} (ID: {bot.user.id})')
    bot_logger.info(f'Conectado a {len(bot.guilds)} servidor(es)')
    bot_logger.info(f'Entorno: {ENVIRONMENT}')
    
    # Cambiar estado del bot
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="el servidor | /help"
        )
    )
    
    # Sincronizar comandos slash con Discord
    # Sincronizar comandos slash con Discord
    bot_logger.info("Sincronizando comandos con Discord...")
    try:
        if DISCORD_GUILD_ID:
            try:
                guild = discord.Object(id=int(DISCORD_GUILD_ID))
                bot.tree.copy_global_to(guild=guild)
                await bot.tree.sync(guild=guild)
                bot_logger.info(f"✅ Comandos sincronizados con servidor: {DISCORD_GUILD_ID}")
            except Exception as e:
                bot_logger.error(f"❌ Error sincronizando con guild: {e}")
                await bot.tree.sync() # Fallback global
        else:
            await bot.tree.sync()
            bot_logger.info("✅ Comandos sincronizados globalmente")
    except Exception as e:
        bot_logger.error(f"❌ Error sincronizando comandos: {e}")
    
    bot_logger.info('Bot listo y operativo')


@bot.event
async def on_command_error(ctx, error):
    """Manejo global de errores de comandos"""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❌ Comando no encontrado. Usa `/help` para ver comandos disponibles.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ No tienes permisos para usar este comando.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Falta un argumento requerido: `{error.param.name}`")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"❌ Argumento inválido: {error}")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏰ Este comando está en cooldown. Intenta en {error.retry_after:.1f}s")
    else:
        bot_logger.error(f"Error en comando {ctx.command}: {error}", exc_info=error)
        await ctx.send("❌ Ocurrió un error al ejecutar el comando.")


@bot.event
async def on_member_join(member):
    """Evento cuando un miembro se une al servidor"""
    bot_logger.info(f"Nuevo miembro: {member.name} ({member.id})")
    
    # Crear usuario en base de datos
    from bot.database.connection import SessionLocal
    from bot.services.points_service import PointsService
    
    db = SessionLocal()
    try:
        PointsService.get_or_create_user(
            db, 
            member.id, 
            member.name, 
            member.discriminator
        )
    finally:
        db.close()


@bot.event
async def on_member_remove(member):
    """Evento cuando un miembro sale del servidor"""
    bot_logger.info(f"Miembro salió: {member.name} ({member.id})")


async def main():
    """Función principal del bot"""
    # Inicializar base de datos
    bot_logger.info("Inicializando base de datos...")
    init_db()
    
    async with bot:
        # Cargar cogs
        cogs_to_load = [
            'bot.cogs.points',
            'bot.cogs.roles',
            'bot.cogs.shop',
            'bot.cogs.events',
            'bot.cogs.admin',
            'bot.cogs.announcements',
            'bot.cogs.levels'
        ]
        
        for cog in cogs_to_load:
            try:
                await bot.load_extension(cog)
                bot_logger.info(f"✅ Cog cargado: {cog}")
            except Exception as e:
                bot_logger.error(f"❌ Error cargando {cog}: {e}")
        
        # Iniciar scheduler de tareas (temporalmente desactivado)
        # from bot.tasks.scheduler import start_scheduler
        # start_scheduler(bot)
        bot_logger.info("✅ Scheduler de tareas (desactivado temporalmente)")
        
        # Compartir instancia del bot con el panel web
        from web.discord_integration import DiscordIntegrationService
        DiscordIntegrationService.set_bot_instance(bot)
        bot_logger.info("✅ Bot instance shared with web panel")
        
        # Iniciar bot
        bot_logger.info("Iniciando bot...")
        await bot.start(DISCORD_TOKEN)


if __name__ == "__main__":
    import asyncio
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        bot_logger.info("Bot detenido por el usuario")
    except Exception as e:
        bot_logger.error(f"Error fatal: {e}", exc_info=e)
        sys.exit(1)
