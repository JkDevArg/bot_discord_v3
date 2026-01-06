"""
Cog de comandos administrativos
"""
import discord
from discord.ext import commands
from discord import app_commands
from bot.database.connection import SessionLocal
from bot.services.points_service import PointsService
from bot.services.role_service import RoleService
from bot.services.shop_service import ShopService
from bot.services.event_service import EventService
from bot.config import ADMIN_USER_IDS
from bot.utils.logger import bot_logger, log_audit
from datetime import datetime


def is_admin():
    """Decorator para verificar si el usuario es admin"""
    async def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.id in ADMIN_USER_IDS
    return app_commands.check(predicate)


class Admin(commands.Cog):
    """Comandos administrativos"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="admin-add-points", description="[ADMIN] Añadir puntos a un usuario")
    @app_commands.describe(user="Usuario", points="Cantidad de puntos")
    @is_admin()
    async def add_points(self, interaction: discord.Interaction, user: discord.Member, points: int):
        """Añadir puntos a un usuario"""
        db = SessionLocal()
        try:
            db_user = PointsService.get_or_create_user(
                db, user.id, user.name, user.discriminator
            )
            
            success = PointsService.add_points_admin(db, db_user, points, interaction.user.id)
            
            if success:
                log_audit(
                    interaction.user.name,
                    f"Añadió {points} puntos a {user.name}",
                    f"Puntos totales: {db_user.points}"
                )
                
                await interaction.response.send_message(
                    f"✅ Se añadieron **{points:,}** puntos a {user.mention}\n"
                    f"Puntos totales: **{db_user.points:,}**"
                )
            else:
                await interaction.response.send_message("❌ Error al añadir puntos.", ephemeral=True)
        
        finally:
            db.close()

    @commands.command(name="sync")
    async def sync_tree(self, ctx):
        """[ADMIN] Sincronizar comandos manualmente (Text Command)"""
        if ctx.author.id not in ADMIN_USER_IDS:
            return

        await ctx.send("⏳ Sincronizando comandos...")
        try:
            synced = await self.bot.tree.sync()
            await ctx.send(f"✅ Sincronizados {len(synced)} comandos globalmente.")
        except Exception as e:
            await ctx.send(f"❌ Error: {e}")
    
    @app_commands.command(name="admin-set-points", description="[ADMIN] Establecer puntos exactos a un usuario")
    @app_commands.describe(user="Usuario", points="Cantidad de puntos")
    @is_admin()
    async def set_points(self, interaction: discord.Interaction, user: discord.Member, points: int):
        """Establecer puntos exactos"""
        db = SessionLocal()
        try:
            db_user = PointsService.get_or_create_user(
                db, user.id, user.name, user.discriminator
            )
            
            old_points = db_user.points
            success = PointsService.set_points_admin(db, db_user, points, interaction.user.id)
            
            if success:
                log_audit(
                    interaction.user.name,
                    f"Estableció puntos de {user.name}",
                    f"{old_points} -> {points}"
                )
                
                await interaction.response.send_message(
                    f"✅ Puntos de {user.mention} establecidos a **{points:,}**"
                )
            else:
                await interaction.response.send_message("❌ Error al establecer puntos.", ephemeral=True)
        
        finally:
            db.close()
    
    @app_commands.command(name="admin-create-role", description="[ADMIN] Crear un nuevo rol")
    @app_commands.describe(
        name="Nombre del rol",
        discord_role="Rol de Discord",
        points_required="Puntos requeridos",
        auto_assign="Asignar automáticamente"
    )
    @is_admin()
    async def create_role(
        self,
        interaction: discord.Interaction,
        name: str,
        discord_role: discord.Role,
        points_required: int,
        auto_assign: bool = True
    ):
        """Crear rol"""
        db = SessionLocal()
        try:
            role = RoleService.create_role(
                db,
                name=name,
                discord_role_id=discord_role.id,
                points_required=points_required,
                color=f"#{discord_role.color.value:06x}",
                auto_assign=auto_assign
            )
            
            log_audit(
                interaction.user.name,
                f"Creó rol {name}",
                f"Puntos requeridos: {points_required}"
            )
            
            await interaction.response.send_message(
                f"✅ Rol **{name}** creado exitosamente\n"
                f"Puntos requeridos: **{points_required:,}**\n"
                f"Auto-asignar: **{'Sí' if auto_assign else 'No'}**"
            )
        
        finally:
            db.close()
    
    @app_commands.command(name="admin-create-item", description="[ADMIN] Crear item en la tienda")
    @app_commands.describe(
        name="Nombre del item",
        price="Precio en puntos",
        item_type="Tipo de item",
        description="Descripción"
    )
    @is_admin()
    async def create_item(
        self,
        interaction: discord.Interaction,
        name: str,
        price: int,
        item_type: str,
        description: str = ""
    ):
        """Crear item de tienda"""
        db = SessionLocal()
        try:
            item = ShopService.create_item(
                db,
                name=name,
                price=price,
                item_type=item_type,
                description=description
            )
            
            log_audit(
                interaction.user.name,
                f"Creó item {name}",
                f"Precio: {price} pts, Tipo: {item_type}"
            )
            
            await interaction.response.send_message(
                f"✅ Item **{name}** creado exitosamente\n"
                f"Precio: **{price:,}** pts\n"
                f"Tipo: **{item_type}**\n"
                f"ID: `{item.id}`"
            )
        
        except ValueError as e:
            await interaction.response.send_message(f"❌ Error: {e}", ephemeral=True)
        finally:
            db.close()
    
    @app_commands.command(name="admin-create-event", description="[ADMIN] Crear un evento")
    @app_commands.describe(
        name="Nombre del evento",
        start_time="Hora de inicio (formato: YYYY-MM-DD HH:MM)",
        end_time="Hora de fin (formato: YYYY-MM-DD HH:MM)",
        reward_points="Puntos de recompensa",
        min_activity="Actividad mínima requerida"
    )
    @is_admin()
    async def create_event(
        self,
        interaction: discord.Interaction,
        name: str,
        start_time: str,
        end_time: str,
        reward_points: int = 100,
        min_activity: int = 10
    ):
        """Crear evento"""
        db = SessionLocal()
        try:
            # Parsear fechas
            start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M")
            
            event = EventService.create_event(
                db,
                name=name,
                start_time=start_dt,
                end_time=end_dt,
                created_by=interaction.user.id,
                reward_points=reward_points,
                min_activity=min_activity
            )
            
            log_audit(
                interaction.user.name,
                f"Creó evento {name}",
                f"Recompensa: {reward_points} pts"
            )
            
            await interaction.response.send_message(
                f"✅ Evento **{name}** creado exitosamente\n"
                f"Inicio: <t:{int(start_dt.timestamp())}:F>\n"
                f"Fin: <t:{int(end_dt.timestamp())}:F>\n"
                f"Recompensa: **{reward_points:,}** pts\n"
                f"ID: `{event.id}`"
            )
        
        except ValueError as e:
            await interaction.response.send_message(
                f"❌ Error en formato de fecha. Usa: YYYY-MM-DD HH:MM\nEjemplo: 2026-01-10 20:00",
                ephemeral=True
            )
        finally:
            db.close()
    
    @app_commands.command(name="admin-stats", description="[ADMIN] Ver estadísticas del servidor")
    @is_admin()
    async def server_stats(self, interaction: discord.Interaction):
        """Ver estadísticas"""
        db = SessionLocal()
        try:
            from sqlalchemy import func
            from bot.database.models import User, Purchase, Event
            
            total_users = db.query(func.count(User.id)).scalar()
            total_points = db.query(func.sum(User.points)).scalar() or 0
            total_purchases = db.query(func.count(Purchase.id)).scalar()
            active_events = db.query(func.count(Event.id)).filter(
                Event.is_active == True, Event.is_finished == False
            ).scalar()
            
            shop_stats = ShopService.get_shop_stats(db)
            
            embed = discord.Embed(
                title="📊 Estadísticas del Servidor",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(name="👥 Usuarios", value=f"{total_users:,}", inline=True)
            embed.add_field(name="💰 Puntos Totales", value=f"{total_points:,}", inline=True)
            embed.add_field(name="🛒 Compras", value=f"{total_purchases:,}", inline=True)
            embed.add_field(name="🎉 Eventos Activos", value=f"{active_events}", inline=True)
            embed.add_field(
                name="💸 Puntos Gastados",
                value=f"{shop_stats['total_points_spent']:,}",
                inline=True
            )
            
            if shop_stats['most_popular_item']:
                embed.add_field(
                    name="🏆 Item Más Popular",
                    value=f"{shop_stats['most_popular_item']} ({shop_stats['most_popular_count']} compras)",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed)
        
        finally:
            db.close()
            db.close()
    
    @app_commands.command(name="admin-add-exp", description="[ADMIN] Añadir experiencia a un usuario")
    @app_commands.describe(user="Usuario", exp="Cantidad de EXP")
    @is_admin()
    async def add_exp(self, interaction: discord.Interaction, user: discord.Member, exp: int):
        """Añadir experiencia a un usuario"""
        db = SessionLocal()
        try:
            from bot.services.level_service import LevelService
            
            db_user = PointsService.get_or_create_user(
                db, user.id, user.name, user.discriminator
            )
            
            old_level = db_user.level
            success = LevelService.add_exp_admin(db, db_user, exp, interaction.user.id)
            
            if success:
                log_audit(
                    interaction.user.name,
                    f"Añadió {exp} EXP a {user.name}",
                    f"Nivel {old_level} -> {db_user.level}"
                )
                
                level_change = f" (Nivel {old_level} -> {db_user.level})" if db_user.level != old_level else ""
                
                await interaction.response.send_message(
                    f"✅ Se añadieron **{exp:,}** EXP a {user.mention}{level_change}\n"
                    f"EXP total: **{db_user.exp:,}** | Nivel: **{db_user.level}**"
                )
            else:
                await interaction.response.send_message("❌ Error al añadir EXP.", ephemeral=True)
        
        finally:
            db.close()
    
    @app_commands.command(name="admin-set-level", description="[ADMIN] Establecer nivel exacto a un usuario")
    @app_commands.describe(user="Usuario", level="Nivel objetivo")
    @is_admin()
    async def set_level(self, interaction: discord.Interaction, user: discord.Member, level: int):
        """Establecer nivel exacto"""
        db = SessionLocal()
        try:
            from bot.services.level_service import LevelService
            
            db_user = PointsService.get_or_create_user(
                db, user.id, user.name, user.discriminator
            )
            
            old_level = db_user.level
            success = LevelService.set_level_admin(db, db_user, level, interaction.user.id)
            
            if success:
                log_audit(
                    interaction.user.name,
                    f"Estableció nivel de {user.name}",
                    f"Nivel {old_level} -> {level}"
                )
                
                await interaction.response.send_message(
                    f"✅ Nivel de {user.mention} establecido a **{level}**\n"
                    f"EXP total: **{db_user.exp:,}**"
                )
            else:
                await interaction.response.send_message("❌ Error al establecer nivel.", ephemeral=True)
        
        finally:
            db.close()


async def setup(bot):
    await bot.add_cog(Admin(bot))
