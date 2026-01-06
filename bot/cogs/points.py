"""
Cog de sistema de puntos
"""
import discord
from discord.ext import commands
from discord import app_commands
from bot.database.connection import SessionLocal
from bot.services.points_service import PointsService
from bot.services.role_service import RoleService
from bot.utils.logger import bot_logger
from datetime import datetime


class Points(commands.Cog):
    """Comandos relacionados con el sistema de puntos"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Otorgar puntos y experiencia por mensajes"""
        # Ignorar mensajes del bot
        if message.author.bot:
            return
        
        # Ignorar comandos
        if message.content.startswith('/'):
            return
        
        db = SessionLocal()
        try:
            # Obtener o crear usuario (con avatar)
            avatar_url = message.author.display_avatar.url if message.author.display_avatar else None
            
            user = PointsService.get_or_create_user(
                db,
                message.author.id,
                message.author.name,
                message.author.discriminator,
                avatar_url=avatar_url
            )
            
            # Intentar otorgar puntos
            success, points, msg = PointsService.award_points(
                db, user, message.channel.id
            )
            
            if success:
                # Otorgar experiencia también
                from bot.services.level_service import LevelService
                _, exp_gained, leveled_up, new_level = LevelService.award_exp(db, user)
                
                # Si subió de nivel
                if leveled_up:
                    old_level = new_level - 1
                    
                    # Obtener recompensas
                    rewards = LevelService.get_level_rewards(new_level)
                    
                    # Calcular bonificación de puntos
                    bonus_points = rewards['points']
                    
                    # Anunciar level-up con webhook
                    try:
                        from bot.services.announcement_service import LevelAnnouncementService
                        import asyncio
                        
                        # Obtener avatar del usuario
                        avatar_url = message.author.display_avatar.url
                        
                        # Enviar anuncio
                        asyncio.create_task(
                            LevelAnnouncementService.announce_level_up(
                                user_id=message.author.id,
                                username=message.author.display_name,
                                avatar_url=avatar_url,
                                old_level=old_level,
                                new_level=new_level,
                                bonus_points=bonus_points
                            )
                        )
                    except Exception as e:
                        bot_logger.error(f"Error enviando anuncio de nivel: {e}")
                
                # Verificar y asignar roles automáticos
                newly_assigned = RoleService.check_and_assign_auto_roles(
                    db, user, message.guild
                )
                
                # Asignar roles en Discord
                for role in newly_assigned:
                    discord_role = message.guild.get_role(role.discord_role_id)
                    if discord_role:
                        try:
                            await message.author.add_roles(discord_role)
                            bot_logger.info(f"Rol {role.name} asignado a {message.author.name}")
                        except Exception as e:
                            bot_logger.error(f"Error asignando rol: {e}")
        
        finally:
            db.close()
    
    @app_commands.command(name="points", description="Ver tus puntos o los de otro usuario")
    @app_commands.describe(user="Usuario del que quieres ver los puntos (opcional)")
    async def points(self, interaction: discord.Interaction, user: discord.Member = None):
        """Ver puntos de un usuario"""
        target_user = user or interaction.user
        
        db = SessionLocal()
        try:
            db_user = PointsService.get_or_create_user(
                db,
                target_user.id,
                target_user.name,
                target_user.discriminator
            )
            
            stats = PointsService.get_user_stats(db, db_user)
            
            # Obtener siguiente rol
            next_role, points_needed = RoleService.get_next_role(db, db_user)
            
            # Crear embed
            embed = discord.Embed(
                title=f"📊 Estadísticas de {target_user.display_name}",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="💰 Puntos Actuales",
                value=f"**{stats['points']:,}** pts",
                inline=True
            )
            
            embed.add_field(
                name="📈 Total Ganado",
                value=f"{stats['total_earned']:,} pts",
                inline=True
            )
            
            embed.add_field(
                name="🏆 Ranking",
                value=f"#{stats['rank']}",
                inline=True
            )
            
            embed.add_field(
                name="💬 Mensajes Totales",
                value=f"{stats['total_messages']:,}",
                inline=True
            )
            
            embed.add_field(
                name="📅 Mensajes (7 días)",
                value=f"{stats['messages_this_week']:,}",
                inline=True
            )
            
            embed.add_field(
                name="⏰ Última Actividad",
                value=f"<t:{int(stats['last_activity'].timestamp())}:R>",
                inline=True
            )
            
            if next_role:
                embed.add_field(
                    name="🎯 Siguiente Rol",
                    value=f"**{next_role.name}**\nTe faltan **{points_needed:,}** pts",
                    inline=False
                )
            
            embed.set_thumbnail(url=target_user.display_avatar.url)
            embed.set_footer(text=f"Miembro desde")
            embed.timestamp = stats['member_since']
            
            await interaction.response.send_message(embed=embed)
        
        finally:
            db.close()
    
    @app_commands.command(name="leaderboard", description="Ver el top de usuarios con más puntos")
    @app_commands.describe(limit="Cantidad de usuarios a mostrar (máx 25)")
    async def leaderboard(self, interaction: discord.Interaction, limit: int = 10):
        """Ver tabla de clasificación"""
        if limit > 25:
            limit = 25
        if limit < 1:
            limit = 10
        
        db = SessionLocal()
        try:
            top_users = PointsService.get_leaderboard(db, limit)
            
            if not top_users:
                await interaction.response.send_message("❌ No hay usuarios en la tabla de clasificación.")
                return
            
            embed = discord.Embed(
                title="🏆 Tabla de Clasificación",
                description=f"Top {len(top_users)} usuarios con más puntos",
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
                
                leaderboard_text += f"{medal} **{username}** - {user.points:,} pts\n"
            
            embed.description = leaderboard_text
            embed.set_footer(text="Actualizado")
            
            await interaction.response.send_message(embed=embed)
        
        finally:
            db.close()
    
    @app_commands.command(name="help", description="Ver todos los comandos disponibles")
    async def help_command(self, interaction: discord.Interaction):
        """Mostrar ayuda"""
        embed = discord.Embed(
            title="📖 Comandos del Bot",
            description="Lista de comandos disponibles",
            color=discord.Color.purple()
        )
        
        embed.add_field(
            name="💰 Puntos",
            value=(
                "`/points` - Ver tus puntos\n"
                "`/points @usuario` - Ver puntos de otro usuario\n"
                "`/leaderboard` - Ver top de usuarios"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🎭 Roles",
            value=(
                "`/roles` - Ver roles disponibles\n"
                "`/myroles` - Ver tus roles actuales"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🛒 Tienda",
            value=(
                "`/shop` - Ver items disponibles\n"
                "`/buy <id>` - Comprar un item\n"
                "`/purchases` - Ver tu historial de compras"
            ),
            inline=False
        )
        
        embed.add_field(
            name="🎉 Eventos",
            value=(
                "`/events` - Ver eventos activos\n"
                "`/event-join <id>` - Unirse a un evento"
            ),
            inline=False
        )
        
        embed.add_field(
            name="ℹ️ Información",
            value=(
                "Ganas puntos por enviar mensajes (con cooldown de 60s)\n"
                "Los roles se asignan automáticamente al alcanzar puntos\n"
                "Puedes comprar items especiales en la tienda"
            ),
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    """Función para cargar el cog"""
    await bot.add_cog(Points(bot))
