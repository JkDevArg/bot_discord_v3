"""
Cog de sistema de eventos
"""
import discord
from discord.ext import commands
from discord import app_commands
from bot.database.connection import SessionLocal
from bot.services.event_service import EventService
from bot.services.points_service import PointsService
from datetime import datetime


class Events(commands.Cog):
    """Comandos relacionados con eventos"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="events", description="Ver eventos activos")
    async def events_list(self, interaction: discord.Interaction):
        """Listar eventos activos"""
        db = SessionLocal()
        try:
            events = EventService.get_active_events(db)
            
            if not events:
                await interaction.response.send_message("❌ No hay eventos activos.")
                return
            
            embed = discord.Embed(
                title="🎉 Eventos Activos",
                description="Eventos disponibles para participar",
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            
            for event in events:
                start_ts = int(event.start_time.timestamp())
                end_ts = int(event.end_time.timestamp())
                
                status = ""
                now = datetime.utcnow()
                if now < event.start_time:
                    status = "⏳ Próximamente"
                elif now >= event.start_time and now <= event.end_time:
                    status = "🔴 En curso"
                else:
                    status = "✅ Finalizado"
                
                value = f"**{status}**\n"
                if event.description:
                    value += f"{event.description}\n"
                value += f"📅 Inicio: <t:{start_ts}:F>\n"
                value += f"📅 Fin: <t:{end_ts}:F>\n"
                value += f"🎁 Recompensa: {event.reward_points:,} pts\n"
                value += f"📊 Actividad mínima: {event.min_activity} mensajes\n"
                value += f"**ID:** `{event.id}`"
                
                embed.add_field(
                    name=f"🎉 {event.name}",
                    value=value,
                    inline=False
                )
            
            embed.set_footer(text="Usa /event-join <id> para participar")
            
            await interaction.response.send_message(embed=embed)
        
        finally:
            db.close()
    
    @app_commands.command(name="event-join", description="Unirse a un evento")
    @app_commands.describe(event_id="ID del evento")
    async def join_event(self, interaction: discord.Interaction, event_id: int):
        """Unirse a un evento"""
        db = SessionLocal()
        try:
            # Obtener usuario
            user = PointsService.get_or_create_user(
                db,
                interaction.user.id,
                interaction.user.name,
                interaction.user.discriminator
            )
            
            # Obtener evento
            event = EventService.get_event_by_id(db, event_id)
            if not event:
                await interaction.response.send_message("❌ Evento no encontrado.", ephemeral=True)
                return
            
            # Unirse al evento
            success, message = EventService.join_event(db, event, user)
            
            if not success:
                await interaction.response.send_message(f"❌ {message}", ephemeral=True)
                return
            
            embed = discord.Embed(
                title="✅ Te uniste al evento",
                description=f"**{event.name}**",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            
            start_ts = int(event.start_time.timestamp())
            end_ts = int(event.end_time.timestamp())
            
            embed.add_field(
                name="📅 Inicio",
                value=f"<t:{start_ts}:F>",
                inline=True
            )
            
            embed.add_field(
                name="📅 Fin",
                value=f"<t:{end_ts}:F>",
                inline=True
            )
            
            embed.add_field(
                name="🎁 Recompensa",
                value=f"{event.reward_points:,} pts",
                inline=True
            )
            
            embed.add_field(
                name="📋 Requisitos",
                value=(
                    f"• Estar presente al inicio\n"
                    f"• Estar presente al final\n"
                    f"• Enviar al menos {event.min_activity} mensajes durante el evento"
                ),
                inline=False
            )
            
            await interaction.response.send_message(embed=embed)
        
        finally:
            db.close()


async def setup(bot):
    await bot.add_cog(Events(bot))
