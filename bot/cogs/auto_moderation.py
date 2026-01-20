"""
Cog para auto-moderación (anti-spam y filtro de palabras)
"""
import discord
from discord.ext import commands
from datetime import datetime, timedelta
from collections import defaultdict
from bot.database.connection import SessionLocal
from bot.database.models import ModerationConfig, FilteredWord, ModerationLog
from bot.utils.logger import bot_logger
from bot.config import DISCORD_GUILD_ID
import re


class AutoModerationCog(commands.Cog):
    """Sistema de auto-moderación"""
    
    def __init__(self, bot):
        self.bot = bot
        # Cache de mensajes por usuario para detección de spam
        self.user_messages = defaultdict(list)
        # Cache de palabras filtradas
        self.filtered_words_cache = []
        self.last_cache_update = None
    
    async def get_or_create_config(self, db, guild_id):
        """Obtener o crear configuración de moderación"""
        config = db.query(ModerationConfig).filter(
            ModerationConfig.guild_id == guild_id
        ).first()
        
        if not config:
            config = ModerationConfig(guild_id=guild_id)
            db.add(config)
            db.commit()
            db.refresh(config)
        
        return config
    
    async def update_filtered_words_cache(self, db):
        """Actualizar cache de palabras filtradas"""
        words = db.query(FilteredWord).filter(FilteredWord.is_active == True).all()
        self.filtered_words_cache = [word.word.lower() for word in words]
        self.last_cache_update = datetime.utcnow()
        bot_logger.info(f"Filtered words cache updated: {len(self.filtered_words_cache)} words")
    
    async def log_moderation_action(self, db, user, action, reason, message_content=None, channel_id=None):
        """Registrar acción de moderación"""
        log = ModerationLog(
            user_id=user.id,
            username=str(user),
            action=action,
            reason=reason,
            auto_moderated=True,
            message_content=message_content,
            channel_id=channel_id
        )
        db.add(log)
        db.commit()
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Listener para todos los mensajes"""
        # Ignorar mensajes del bot y DMs
        if message.author.bot or not message.guild:
            return
        
        # Ignorar administradores
        if message.author.guild_permissions.administrator:
            return
        
        db = SessionLocal()
        try:
            config = await self.get_or_create_config(db, message.guild.id)
            
            # Actualizar cache de palabras si es necesario
            if not self.last_cache_update or \
               (datetime.utcnow() - self.last_cache_update) > timedelta(minutes=5):
                await self.update_filtered_words_cache(db)
            
            # 1. Detección de spam
            if config.spam_enabled:
                await self.check_spam(message, config, db)
            
            # 2. Filtro de palabras
            if config.filter_enabled:
                await self.check_filtered_words(message, config, db)
        
        except Exception as e:
            bot_logger.error(f"Error in auto-moderation: {e}", exc_info=e)
        finally:
            db.close()
    
    async def check_spam(self, message, config, db):
        """Verificar si el mensaje es spam"""
        user_id = message.author.id
        now = datetime.utcnow()
        
        # Agregar mensaje actual
        self.user_messages[user_id].append(now)
        
        # Limpiar mensajes antiguos
        cutoff = now - timedelta(seconds=config.spam_timeframe)
        self.user_messages[user_id] = [
            msg_time for msg_time in self.user_messages[user_id]
            if msg_time > cutoff
        ]
        
        # Verificar si excede el threshold
        if len(self.user_messages[user_id]) > config.spam_threshold:
            try:
                # Eliminar mensajes recientes del usuario
                deleted_count = 0
                async for msg in message.channel.history(limit=50):
                    if msg.author.id == user_id and deleted_count < config.spam_threshold:
                        try:
                            await msg.delete()
                            deleted_count += 1
                        except:
                            pass
                
                # Aplicar timeout
                duration = timedelta(seconds=config.spam_mute_duration)
                await message.author.timeout(duration, reason="Auto-moderación: Spam detectado")
                
                # Log
                await self.log_moderation_action(
                    db, message.author, "spam_mute",
                    f"Spam detectado: {len(self.user_messages[user_id])} mensajes en {config.spam_timeframe}s",
                    channel_id=message.channel.id
                )
                
                # Notificar en el canal
                embed = discord.Embed(
                    title="🚫 Auto-moderación: Spam",
                    description=f"{message.author.mention} ha sido silenciado por {config.spam_mute_duration // 60} minutos por spam.",
                    color=discord.Color.red()
                )
                await message.channel.send(embed=embed, delete_after=10)
                
                # Limpiar cache del usuario
                self.user_messages[user_id] = []
                
                bot_logger.warning(f"Spam detected: {message.author} muted for {config.spam_mute_duration}s")
                
            except discord.Forbidden:
                bot_logger.error(f"No permission to mute {message.author}")
            except Exception as e:
                bot_logger.error(f"Error muting user for spam: {e}")
    
    async def check_filtered_words(self, message, config, db):
        """Verificar si el mensaje contiene palabras filtradas"""
        content_lower = message.content.lower()
        
        # Buscar palabras filtradas
        found_words = []
        for word in self.filtered_words_cache:
            # Usar regex para buscar palabras completas
            pattern = r'\b' + re.escape(word) + r'\b'
            if re.search(pattern, content_lower):
                found_words.append(word)
        
        if found_words:
            try:
                # Eliminar mensaje
                await message.delete()
                
                # Log
                await self.log_moderation_action(
                    db, message.author, "filtered_word",
                    f"Palabras filtradas detectadas: {', '.join(found_words)}",
                    message_content=message.content[:500],
                    channel_id=message.channel.id
                )
                
                # Acción según configuración
                if config.filter_action == "mute":
                    duration = timedelta(minutes=10)
                    await message.author.timeout(duration, reason="Auto-moderación: Palabra filtrada")
                    
                    embed = discord.Embed(
                        title="🚫 Auto-moderación: Contenido Inapropiado",
                        description=f"{message.author.mention} ha sido silenciado por 10 minutos por usar lenguaje inapropiado.",
                        color=discord.Color.red()
                    )
                    await message.channel.send(embed=embed, delete_after=10)
                else:
                    # Solo delete
                    embed = discord.Embed(
                        title="⚠️ Mensaje Eliminado",
                        description=f"{message.author.mention}, tu mensaje fue eliminado por contener lenguaje inapropiado.",
                        color=discord.Color.orange()
                    )
                    await message.channel.send(embed=embed, delete_after=5)
                
                bot_logger.warning(f"Filtered word detected: {message.author} - {found_words}")
                
            except discord.Forbidden:
                bot_logger.error(f"No permission to delete message from {message.author}")
            except Exception as e:
                bot_logger.error(f"Error filtering message: {e}")


async def setup(bot):
    await bot.add_cog(AutoModerationCog(bot))
