"""
Cog de sistema de niveles
"""
import discord
from discord.ext import commands
from discord import app_commands
from bot.database.connection import SessionLocal
from bot.services.level_service import LevelService
from bot.services.points_service import PointsService
from datetime import datetime


class Levels(commands.Cog):
    """Comandos relacionados con niveles y experiencia"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="level", description="Ver tu nivel y experiencia")
    @app_commands.describe(user="Usuario del que quieres ver el nivel (opcional)")
    async def level(self, interaction: discord.Interaction, user: discord.Member = None):
        """Ver nivel de un usuario"""
        target_user = user or interaction.user
        
        db = SessionLocal()
        try:
            db_user = PointsService.get_or_create_user(
                db,
                target_user.id,
                target_user.name,
                target_user.discriminator
            )
            
            stats = LevelService.get_level_stats(db, db_user)
            
            # Crear embed
            embed = discord.Embed(
                title=f"📊 Nivel de {target_user.display_name}",
                color=discord.Color.purple(),
                timestamp=datetime.utcnow()
            )
            
            # Nivel actual
            embed.add_field(
                name="⭐ Nivel",
                value=f"**{stats['level']}**",
                inline=True
            )
            
            # Ranking
            embed.add_field(
                name="🏆 Ranking",
                value=f"#{stats['rank']}",
                inline=True
            )
            
            # EXP total
            embed.add_field(
                name="💫 EXP Total",
                value=f"{stats['total_exp_earned']:,}",
                inline=True
            )
            
            # Barra de progreso
            progress_bar = LevelService.create_progress_bar(stats['progress_percentage'])
            
            embed.add_field(
                name=f"📈 Progreso al Nivel {stats['level'] + 1}",
                value=(
                    f"{progress_bar}\n"
                    f"**{stats['exp_in_current_level']:,}** / **{stats['exp_needed_for_level']:,}** EXP "
                    f"({stats['progress_percentage']}%)\n"
                    f"Faltan **{stats['exp_to_next_level']:,}** EXP"
                ),
                inline=False
            )
            
            embed.set_thumbnail(url=target_user.display_avatar.url)
            embed.set_footer(text=f"Miembro desde")
            embed.timestamp = db_user.joined_at
            
            await interaction.response.send_message(embed=embed)
        
        finally:
            db.close()
    
    @app_commands.command(name="rank", description="Ver tabla de clasificación por nivel")
    @app_commands.describe(limit="Cantidad de usuarios a mostrar (máx 25)")
    async def rank(self, interaction: discord.Interaction, limit: int = 10):
        """Ver tabla de clasificación por nivel"""
        if limit > 25:
            limit = 25
        if limit < 1:
            limit = 10
        
        db = SessionLocal()
        try:
            top_users = LevelService.get_level_leaderboard(db, limit)
            
            if not top_users:
                await interaction.response.send_message("❌ No hay usuarios en la tabla de clasificación.")
                return
            
            embed = discord.Embed(
                title="🏆 Ranking de Niveles",
                description=f"Top {len(top_users)} usuarios por nivel",
                color=discord.Color.gold(),
                timestamp=datetime.utcnow()
            )
            
            medals = ["🥇", "🥈", "🥉"]
            
            leaderboard_text = ""
            for i, user in enumerate(top_users, 1):
                medal = medals[i-1] if i <= 3 else f"`{i}.`"
                
                # Intentar obtener el miembro de Discord
                member = interaction.guild.get_member(user.discord_id)
                username = member.display_name if member else user.username
                
                leaderboard_text += (
                    f"{medal} **{username}** - "
                    f"Nivel **{user.level}** ({user.exp:,} EXP)\n"
                )
            
            embed.description = leaderboard_text
            embed.set_footer(text="Actualizado")
            
            await interaction.response.send_message(embed=embed)
        
        finally:
            db.close()
    
    @app_commands.command(name="levels", description="Ver información sobre el sistema de niveles")
    async def levels_info(self, interaction: discord.Interaction):
        """Información sobre el sistema de niveles"""
        embed = discord.Embed(
            title="⭐ Sistema de Niveles",
            description="Información sobre cómo funcionan los niveles",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="💫 Ganar Experiencia",
            value=(
                f"• Ganas **{LevelService.EXP_PER_MESSAGE} EXP** por cada mensaje\n"
                f"• Mismo cooldown que los puntos (60 segundos)\n"
                f"• La EXP se acumula para subir de nivel"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📊 Niveles",
            value=(
                f"• Nivel 2: {LevelService.calculate_exp_for_level(2):,} EXP\n"
                f"• Nivel 5: {LevelService.calculate_exp_for_level(5):,} EXP\n"
                f"• Nivel 10: {LevelService.calculate_exp_for_level(10):,} EXP\n"
                f"• Nivel 20: {LevelService.calculate_exp_for_level(20):,} EXP\n"
                f"• Nivel 50: {LevelService.calculate_exp_for_level(50):,} EXP"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🎁 Recompensas",
            value=(
                "• **Cada 5 niveles**: Puntos bonus\n"
                "• **Niveles especiales**: Títulos únicos\n"
                "• Nivel 5: 🌱 Novato\n"
                "• Nivel 10: ⚔️ Guerrero\n"
                "• Nivel 20: 👑 Élite\n"
                "• Nivel 30: 🔥 Leyenda\n"
                "• Nivel 50: ⭐ Mítico\n"
                "• Nivel 100: 🏆 Inmortal"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📝 Comandos",
            value=(
                "`/level` - Ver tu nivel\n"
                "`/level @usuario` - Ver nivel de otro usuario\n"
                "`/rank` - Ver ranking de niveles"
            ),
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(Levels(bot))
