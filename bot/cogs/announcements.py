"""
Cog de sistema de anuncios
"""
import discord
from discord.ext import commands
from bot.database.connection import SessionLocal
from bot.database.models import AnnouncementConfig
from bot.utils.logger import bot_logger


class AnnouncementsCog(commands.Cog):
    """Sistema de anuncios automáticos"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @staticmethod
    async def get_announcement_channel(guild: discord.Guild, announcement_type: str) -> discord.TextChannel:
        """Obtener canal de anuncios configurado"""
        db = SessionLocal()
        try:
            config = db.query(AnnouncementConfig).filter(
                AnnouncementConfig.announcement_type == announcement_type,
                AnnouncementConfig.is_enabled == True
            ).first()
            
            if config:
                channel = guild.get_channel(config.channel_id)
                return channel
            
            return None
        finally:
            db.close()
    
    @staticmethod
    async def announce_level_up(bot, guild: discord.Guild, user: discord.Member, role):
        """Anunciar que un usuario subió de nivel (obtuvo nuevo rol)"""
        channel = await AnnouncementsCog.get_announcement_channel(guild, 'level_up')
        
        if not channel:
            return
        
        try:
            discord_role = guild.get_role(role.discord_role_id)
            role_mention = discord_role.mention if discord_role else role.name
            
            embed = discord.Embed(
                title="🎉 ¡Nuevo Rol Desbloqueado!",
                description=f"{user.mention} ha alcanzado el rol {role_mention}",
                color=discord.Color.gold()
            )
            
            embed.add_field(
                name="💰 Puntos Requeridos",
                value=f"{role.points_required:,}",
                inline=True
            )
            
            if role.benefits:
                embed.add_field(
                    name="⭐ Beneficios",
                    value=role.benefits,
                    inline=False
                )
            
            embed.set_thumbnail(url=user.display_avatar.url)
            
            await channel.send(embed=embed)
            bot_logger.info(f"Anuncio de level-up enviado: {user.name} -> {role.name}")
        
        except Exception as e:
            bot_logger.error(f"Error enviando anuncio de level-up: {e}")
    
    @staticmethod
    async def announce_level_up_exp(bot, guild: discord.Guild, user: discord.Member, new_level: int, rewards: dict):
        """Anunciar que un usuario subió de nivel (experiencia)"""
        channel = await AnnouncementsCog.get_announcement_channel(guild, 'level_up')
        
        if not channel:
            return
        
        try:
            embed = discord.Embed(
                title="⭐ ¡LEVEL UP!",
                description=f"{user.mention} alcanzó el **Nivel {new_level}**",
                color=discord.Color.gold()
            )
            
            embed.set_thumbnail(url=user.display_avatar.url)
            
            # Mostrar recompensas
            rewards_text = ""
            if rewards['points'] > 0:
                rewards_text += f"💰 **{rewards['points']:,}** puntos bonus\n"
            
            if rewards['title']:
                rewards_text += f"🏆 Título desbloqueado: **{rewards['title']}**\n"
            
            if rewards_text:
                embed.add_field(
                    name="🎁 Recompensas",
                    value=rewards_text,
                    inline=False
                )
            
            embed.add_field(
                name="💫 Nivel Alcanzado",
                value=f"**{new_level}**",
                inline=True
            )
            
            await channel.send(embed=embed)
            bot_logger.info(f"Anuncio de level-up (EXP) enviado: {user.name} -> Nivel {new_level}")
        
        except Exception as e:
            bot_logger.error(f"Error enviando anuncio de level-up (EXP): {e}")
    
    @staticmethod
    async def announce_purchase(bot, guild: discord.Guild, user: discord.Member, item):
        """Anunciar que un usuario realizó una compra"""
        channel = await AnnouncementsCog.get_announcement_channel(guild, 'purchase')
        
        if not channel:
            return
        
        try:
            type_emoji = {
                'role': '🎭',
                'benefit': '⭐',
                'custom': '🎁'
            }.get(item.item_type, '📦')
            
            embed = discord.Embed(
                title="🛒 Nueva Compra",
                description=f"{user.mention} ha comprado **{item.name}**",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="💰 Precio",
                value=f"{item.price:,} pts",
                inline=True
            )
            
            embed.add_field(
                name="📦 Tipo",
                value=f"{type_emoji} {item.item_type}",
                inline=True
            )
            
            embed.set_thumbnail(url=user.display_avatar.url)
            
            await channel.send(embed=embed)
            bot_logger.info(f"Anuncio de compra enviado: {user.name} -> {item.name}")
        
        except Exception as e:
            bot_logger.error(f"Error enviando anuncio de compra: {e}")
    
    @staticmethod
    async def announce_event(bot, guild: discord.Guild, event, announcement_text: str):
        """Anunciar información sobre un evento"""
        channel = await AnnouncementsCog.get_announcement_channel(guild, 'event')
        
        if not channel:
            return
        
        try:
            embed = discord.Embed(
                title=f"🎉 {event.name}",
                description=announcement_text,
                color=discord.Color.orange()
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
            
            if event.description:
                embed.add_field(
                    name="📝 Descripción",
                    value=event.description,
                    inline=False
                )
            
            await channel.send(embed=embed)
            bot_logger.info(f"Anuncio de evento enviado: {event.name}")
        
        except Exception as e:
            bot_logger.error(f"Error enviando anuncio de evento: {e}")


async def setup(bot):
    await bot.add_cog(AnnouncementsCog(bot))
