"""
Cog para tareas programadas (scheduled tasks)
"""
import discord
from discord.ext import commands, tasks
from datetime import datetime, time
from bot.services.daily_stats_service import DailyStatsService
from bot.utils.logger import bot_logger


class ScheduledTasksCog(commands.Cog):
    """Tareas programadas del bot"""
    
    def __init__(self, bot):
        self.bot = bot
        self.daily_stats_task.start()
    
    def cog_unload(self):
        """Detener tareas al descargar el cog"""
        self.daily_stats_task.cancel()
    
    @tasks.loop(time=time(hour=0, minute=5))  # Ejecutar a las 00:05 UTC
    async def daily_stats_task(self):
        """Tarea diaria para actualizar estadísticas"""
        try:
            bot_logger.info("Running daily stats update task...")
            
            # Actualizar stats del día anterior
            stats = DailyStatsService.update_daily_stats()
            
            bot_logger.info(
                f"Daily stats updated: {stats.active_users} users, "
                f"{stats.total_messages} messages, {stats.points_awarded} points"
            )
            
        except Exception as e:
            bot_logger.error(f"Error in daily stats task: {e}", exc_info=e)
    
    @daily_stats_task.before_loop
    async def before_daily_stats_task(self):
        """Esperar a que el bot esté listo antes de iniciar la tarea"""
        await self.bot.wait_until_ready()
        bot_logger.info("Daily stats task scheduled (runs at 00:05 UTC)")


async def setup(bot):
    await bot.add_cog(ScheduledTasksCog(bot))
