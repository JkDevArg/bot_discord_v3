"""
Cog de sistema de roles
"""
import discord
from discord.ext import commands
from discord import app_commands
from bot.database.connection import SessionLocal
from bot.services.role_service import RoleService
from bot.services.points_service import PointsService
from datetime import datetime


class Roles(commands.Cog):
    """Comandos relacionados con roles"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="roles", description="Ver todos los roles disponibles")
    async def roles_list(self, interaction: discord.Interaction):
        """Listar roles disponibles"""
        db = SessionLocal()
        try:
            roles = RoleService.get_all_roles(db)
            
            if not roles:
                await interaction.response.send_message("❌ No hay roles configurados.")
                return
            
            embed = discord.Embed(
                title="🎭 Roles Disponibles",
                description="Roles que puedes obtener en el servidor",
                color=discord.Color.purple(),
                timestamp=datetime.utcnow()
            )
            
            for role in roles:
                discord_role = interaction.guild.get_role(role.discord_role_id)
                role_mention = discord_role.mention if discord_role else role.name
                
                value = f"**Puntos requeridos:** {role.points_required:,}\n"
                if role.benefits:
                    value += f"**Beneficios:** {role.benefits}\n"
                if role.auto_assign:
                    value += "✅ Se asigna automáticamente\n"
                if role.is_purchasable:
                    value += "🛒 Disponible en la tienda\n"
                
                embed.add_field(
                    name=f"{role_mention}",
                    value=value,
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed)
        
        finally:
            db.close()
    
    @app_commands.command(name="myroles", description="Ver tus roles actuales")
    async def my_roles(self, interaction: discord.Interaction):
        """Ver roles del usuario"""
        db = SessionLocal()
        try:
            user = PointsService.get_or_create_user(
                db,
                interaction.user.id,
                interaction.user.name,
                interaction.user.discriminator
            )
            
            user_roles = RoleService.get_user_roles(db, user)
            
            embed = discord.Embed(
                title=f"🎭 Roles de {interaction.user.display_name}",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            
            if not user_roles:
                embed.description = "No tienes roles especiales aún."
            else:
                roles_text = ""
                for role in user_roles:
                    discord_role = interaction.guild.get_role(role.discord_role_id)
                    role_mention = discord_role.mention if discord_role else role.name
                    roles_text += f"{role_mention} - {role.points_required:,} pts\n"
                
                embed.description = roles_text
            
            # Mostrar siguiente rol
            next_role, points_needed = RoleService.get_next_role(db, user)
            if next_role:
                embed.add_field(
                    name="🎯 Siguiente Rol",
                    value=f"**{next_role.name}**\nTe faltan **{points_needed:,}** puntos",
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        
        finally:
            db.close()


async def setup(bot):
    await bot.add_cog(Roles(bot))
