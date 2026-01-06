"""
Servicio de integración con Discord para acciones desde el panel web
"""
import discord
from typing import Optional
from bot.utils.logger import web_logger
from bot.database.connection import SessionLocal
from bot.database.models import AuditLog
from datetime import datetime


class DiscordIntegrationService:
    """Servicio para ejecutar acciones de Discord desde el panel web"""
    
    _bot_instance = None
    
    @classmethod
    def set_bot_instance(cls, bot):
        """Establecer instancia del bot para usar desde el panel web"""
        cls._bot_instance = bot
        web_logger.info("Bot instance set in DiscordIntegrationService")
    
    @classmethod
    async def send_log_message(cls, message: str, embed: Optional[discord.Embed] = None):
        """
        Enviar mensaje al canal de logs configurado
        
        NOTA: Esta función requiere que el bot esté corriendo en el mismo proceso.
        Como el bot y el panel web corren en procesos separados, esta función
        solo funcionará si se llama desde dentro del proceso del bot.
        
        Para logging desde el panel web, usar log_admin_action() que guarda en BD.
        """
        if not cls._bot_instance:
            web_logger.warning("Bot instance not set - cannot send Discord message directly")
            web_logger.info("Logging to database instead...")
            return False
        
        try:
            # Obtener canal de logs desde configuración
            from bot.database.channel_config import ChannelConfig
            db = SessionLocal()
            try:
                config = db.query(ChannelConfig).filter(
                    ChannelConfig.config_type == 'log_channel'
                ).first()
                
                if not config or not config.channel_ids:
                    web_logger.warning("Log channel not configured")
                    return False
                
                channel_id = int(config.channel_ids)
                
                channel = cls._bot_instance.get_channel(channel_id)
                if not channel:
                    web_logger.error(f"Log channel {channel_id} not found")
                    return False
                
                if embed:
                    await channel.send(content=message if message else None, embed=embed)
                else:
                    await channel.send(message)
                
                web_logger.info(f"Message sent to Discord channel {channel_id}")
                return True
            finally:
                db.close()
        
        except Exception as e:
            web_logger.error(f"Error sending log message: {e}")
            return False
    
    @classmethod
    async def kick_member(cls, guild_id: int, user_id: int, reason: str, admin_username: str) -> tuple[bool, str]:
        """
        Expulsar miembro del servidor
        
        Args:
            guild_id: ID del servidor
            user_id: ID del usuario a expulsar
            reason: Razón de la expulsión
            admin_username: Usuario admin que ejecuta la acción
        
        Returns:
            Tupla (éxito, mensaje)
        """
        if not cls._bot_instance:
            return False, "Bot no disponible"
        
        try:
            guild = cls._bot_instance.get_guild(guild_id)
            if not guild:
                return False, "Servidor no encontrado"
            
            member = guild.get_member(user_id)
            if not member:
                return False, "Usuario no encontrado en el servidor"
            
            # Expulsar
            await member.kick(reason=f"[Panel Web - {admin_username}] {reason}")
            
            # Log en Discord
            embed = discord.Embed(
                title="🚪 Usuario Expulsado",
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Usuario", value=f"{member.mention} ({member.name})", inline=False)
            embed.add_field(name="Razón", value=reason, inline=False)
            embed.add_field(name="Moderador", value=admin_username, inline=True)
            embed.add_field(name="Origen", value="Panel Web", inline=True)
            
            await cls.send_log_message(None, embed)
            
            # Log en BD
            cls._log_action(admin_username, "kick", "user", user_id, f"Kicked {member.name}: {reason}")
            
            return True, f"Usuario {member.name} expulsado correctamente"
        
        except discord.Forbidden:
            return False, "El bot no tiene permisos para expulsar usuarios"
        except Exception as e:
            web_logger.error(f"Error kicking member: {e}")
            return False, f"Error: {str(e)}"
    
    @classmethod
    async def ban_member(cls, guild_id: int, user_id: int, reason: str, admin_username: str, delete_days: int = 0) -> tuple[bool, str]:
        """
        Banear miembro del servidor
        
        Args:
            guild_id: ID del servidor
            user_id: ID del usuario a banear
            reason: Razón del baneo
            admin_username: Usuario admin que ejecuta la acción
            delete_days: Días de mensajes a eliminar (0-7)
        
        Returns:
            Tupla (éxito, mensaje)
        """
        if not cls._bot_instance:
            return False, "Bot no disponible"
        
        try:
            guild = cls._bot_instance.get_guild(guild_id)
            if not guild:
                return False, "Servidor no encontrado"
            
            member = guild.get_member(user_id)
            username = member.name if member else str(user_id)
            
            # Banear
            await guild.ban(
                discord.Object(id=user_id),
                reason=f"[Panel Web - {admin_username}] {reason}",
                delete_message_days=min(delete_days, 7)
            )
            
            # Log en Discord
            embed = discord.Embed(
                title="🔨 Usuario Baneado",
                color=discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Usuario", value=f"<@{user_id}> ({username})", inline=False)
            embed.add_field(name="Razón", value=reason, inline=False)
            embed.add_field(name="Moderador", value=admin_username, inline=True)
            embed.add_field(name="Origen", value="Panel Web", inline=True)
            if delete_days > 0:
                embed.add_field(name="Mensajes eliminados", value=f"{delete_days} días", inline=True)
            
            await cls.send_log_message(None, embed)
            
            # Log en BD
            cls._log_action(admin_username, "ban", "user", user_id, f"Banned {username}: {reason}")
            
            return True, f"Usuario {username} baneado correctamente"
        
        except discord.Forbidden:
            return False, "El bot no tiene permisos para banear usuarios"
        except Exception as e:
            web_logger.error(f"Error banning member: {e}")
            return False, f"Error: {str(e)}"
    
    @classmethod
    async def timeout_member(cls, guild_id: int, user_id: int, duration_minutes: int, reason: str, admin_username: str) -> tuple[bool, str]:
        """
        Silenciar (timeout) miembro del servidor
        
        Args:
            guild_id: ID del servidor
            user_id: ID del usuario a silenciar
            duration_minutes: Duración en minutos (máx 40320 = 28 días)
            reason: Razón del silencio
            admin_username: Usuario admin que ejecuta la acción
        
        Returns:
            Tupla (éxito, mensaje)
        """
        if not cls._bot_instance:
            return False, "Bot no disponible"
        
        try:
            guild = cls._bot_instance.get_guild(guild_id)
            if not guild:
                return False, "Servidor no encontrado"
            
            member = guild.get_member(user_id)
            if not member:
                return False, "Usuario no encontrado en el servidor"
            
            # Calcular duración
            from datetime import timedelta
            duration = timedelta(minutes=min(duration_minutes, 40320))  # Máx 28 días
            
            # Aplicar timeout
            await member.timeout(duration, reason=f"[Panel Web - {admin_username}] {reason}")
            
            # Log en Discord
            embed = discord.Embed(
                title="🔇 Usuario Silenciado",
                color=discord.Color.yellow(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Usuario", value=f"{member.mention} ({member.name})", inline=False)
            embed.add_field(name="Duración", value=f"{duration_minutes} minutos", inline=True)
            embed.add_field(name="Razón", value=reason, inline=False)
            embed.add_field(name="Moderador", value=admin_username, inline=True)
            embed.add_field(name="Origen", value="Panel Web", inline=True)
            
            await cls.send_log_message(None, embed)
            
            # Log en BD
            cls._log_action(admin_username, "timeout", "user", user_id, f"Timeout {member.name} for {duration_minutes}min: {reason}")
            
            return True, f"Usuario {member.name} silenciado por {duration_minutes} minutos"
        
        except discord.Forbidden:
            return False, "El bot no tiene permisos para silenciar usuarios"
        except Exception as e:
            web_logger.error(f"Error timing out member: {e}")
            return False, f"Error: {str(e)}"
    
    @classmethod
    async def log_admin_action(cls, action: str, details: str, admin_username: str):
        """
        Registrar acción administrativa en Discord
        
        Args:
            action: Tipo de acción (ej: "points_updated", "level_changed")
            details: Detalles de la acción
            admin_username: Usuario que ejecutó la acción
        """
        try:
            embed = discord.Embed(
                title="⚙️ Acción Administrativa",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="Acción", value=action, inline=False)
            embed.add_field(name="Detalles", value=details, inline=False)
            embed.add_field(name="Admin", value=admin_username, inline=True)
            embed.add_field(name="Origen", value="Panel Web", inline=True)
            
            await cls.send_log_message(None, embed)
            
            # Log en BD
            cls._log_action(admin_username, action, None, None, details)
        
        except Exception as e:
            web_logger.error(f"Error logging admin action: {e}")
    
    @staticmethod
    def _log_action(admin_username: str, action: str, target_type: Optional[str], target_id: Optional[int], details: str):
        """Registrar acción en base de datos"""
        db = SessionLocal()
        try:
            from bot.database.models import AdminUser
            admin = db.query(AdminUser).filter(AdminUser.username == admin_username).first()
            
            if admin:
                log = AuditLog(
                    admin_id=admin.id,
                    action=action,
                    target_type=target_type,
                    target_id=target_id,
                    details=details
                )
                db.add(log)
                db.commit()
        except Exception as e:
            web_logger.error(f"Error logging to database: {e}")
        finally:
            db.close()
