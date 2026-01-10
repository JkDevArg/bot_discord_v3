"""
Discord leaderboard commands
"""
import discord
from discord.ext import commands
from discord import app_commands
from bot.database.connection import SessionLocal
from bot.database.models import User, Purchase, EventParticipant
from sqlalchemy import func, desc
from datetime import datetime


class Leaderboard(commands.Cog):
    """Comandos de leaderboards"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="leaderboard", description="Ver el leaderboard de puntos")
    @app_commands.describe(category="Categoría del leaderboard")
    @app_commands.choices(category=[
        app_commands.Choice(name="Puntos", value="points"),
        app_commands.Choice(name="Mensajes", value="messages"),
        app_commands.Choice(name="Gastos", value="spending"),
        app_commands.Choice(name="Eventos", value="events")
    ])
    async def leaderboard(self, interaction: discord.Interaction, category: str = "points"):
        """Mostrar leaderboard"""
        db = SessionLocal()
        try:
            embed = discord.Embed(
                title="🏆 Leaderboard",
                color=discord.Color.gold(),
                timestamp=datetime.utcnow()
            )
            
            if category == "points":
                users = db.query(User).filter(User.points > 0).order_by(desc(User.points)).limit(10).all()
                embed.description = "Top 10 usuarios por puntos"
                
                leaderboard_text = ""
                for rank, user in enumerate(users, 1):
                    medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"**{rank}.**"
                    leaderboard_text += f"{medal} {user.username} - **{user.points:,}** pts\n"
                
                embed.add_field(name="Ranking", value=leaderboard_text or "No hay datos", inline=False)
            
            elif category == "messages":
                users = db.query(User).filter(User.message_count > 0).order_by(desc(User.message_count)).limit(10).all()
                embed.description = "Top 10 usuarios por mensajes"
                
                leaderboard_text = ""
                for rank, user in enumerate(users, 1):
                    medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"**{rank}.**"
                    leaderboard_text += f"{medal} {user.username} - **{user.message_count:,}** mensajes\n"
                
                embed.add_field(name="Ranking", value=leaderboard_text or "No hay datos", inline=False)
            
            elif category == "spending":
                spending = db.query(
                    User,
                    func.sum(Purchase.price_paid).label('total_spent')
                ).join(Purchase).group_by(User.id).order_by(desc('total_spent')).limit(10).all()
                
                embed.description = "Top 10 compradores"
                
                leaderboard_text = ""
                for rank, (user, total_spent) in enumerate(spending, 1):
                    medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"**{rank}.**"
                    leaderboard_text += f"{medal} {user.username} - **{int(total_spent):,}** pts gastados\n"
                
                embed.add_field(name="Ranking", value=leaderboard_text or "No hay datos", inline=False)
            
            elif category == "events":
                participation = db.query(
                    User,
                    func.count(EventParticipant.id).label('event_count')
                ).join(EventParticipant).filter(
                    EventParticipant.reward_claimed == True
                ).group_by(User.id).order_by(desc('event_count')).limit(10).all()
                
                embed.description = "Top 10 participantes en eventos"
                
                leaderboard_text = ""
                for rank, (user, event_count) in enumerate(participation, 1):
                    medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"**{rank}.**"
                    leaderboard_text += f"{medal} {user.username} - **{int(event_count)}** eventos completados\n"
                
                embed.add_field(name="Ranking", value=leaderboard_text or "No hay datos", inline=False)
            
            embed.set_footer(text=f"Solicitado por {interaction.user.name}")
            
            await interaction.response.send_message(embed=embed)
        
        finally:
            db.close()


async def setup(bot):
    await bot.add_cog(Leaderboard(bot))
