"""
Cog de sistema de tienda
"""
import discord
from discord.ext import commands
from discord import app_commands
from bot.database.connection import SessionLocal
from bot.services.shop_service import ShopService
from bot.services.points_service import PointsService
from bot.utils.logger import bot_logger
from datetime import datetime


class Shop(commands.Cog):
    """Comandos relacionados con la tienda"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="shop", description="Ver items disponibles en la tienda")
    async def shop_list(self, interaction: discord.Interaction):
        """Listar items de la tienda"""
        db = SessionLocal()
        try:
            items = ShopService.get_active_items(db)
            
            if not items:
                await interaction.response.send_message("❌ La tienda está vacía.")
                return
            
            # Crear embeds para cada item (estilo card)
            embeds = []
            for item in items:
                # Determinar color según tipo
                color_map = {
                    'role': discord.Color.purple(),
                    'benefit': discord.Color.gold(),
                    'custom': discord.Color.blue()
                }
                color = color_map.get(item.item_type, discord.Color.green())
                
                # Crear embed para el item
                embed = discord.Embed(
                    title=f"{item.name}",
                    description=item.description or "Sin descripción",
                    color=color,
                    timestamp=datetime.utcnow()
                )
                
                # Agregar imagen si existe
                if item.image_url:
                    # Si es URL relativa, convertir a absoluta
                    if item.image_url.startswith('/static/'):
                        # Nota: En producción, usar el dominio real
                        image_url = f"http://localhost:8000{item.image_url}"
                    else:
                        image_url = item.image_url
                    embed.set_image(url=image_url)
                
                # Precio
                embed.add_field(
                    name="💰 Precio",
                    value=f"**{item.price:,}** puntos",
                    inline=True
                )
                
                # Stock
                if item.stock == -1:
                    stock_text = "♾️ Ilimitado"
                elif item.stock > 0:
                    stock_text = f"📦 {item.stock} disponibles"
                else:
                    stock_text = "❌ Agotado"
                
                embed.add_field(
                    name="📦 Stock",
                    value=stock_text,
                    inline=True
                )
                
                # Tipo
                type_emoji = {
                    'role': '🎭 Rol',
                    'benefit': '⭐ Beneficio',
                    'custom': '🎁 Personalizado'
                }.get(item.item_type, '📦 Item')
                
                embed.add_field(
                    name="🏷️ Tipo",
                    value=type_emoji,
                    inline=True
                )
                
                # ID para comprar
                embed.set_footer(text=f"ID: {item.id} • Usa /buy {item.id} para comprar")
                
                embeds.append(embed)
            
            # Enviar todos los embeds
            # Discord permite hasta 10 embeds por mensaje
            if len(embeds) <= 10:
                await interaction.response.send_message(embeds=embeds)
            else:
                # Si hay más de 10, enviar los primeros 10
                await interaction.response.send_message(embeds=embeds[:10])
                await interaction.followup.send(
                    f"ℹ️ Mostrando 10 de {len(embeds)} items. Usa el panel web para ver todos.",
                    ephemeral=True
                )
        
        finally:
            db.close()
    
    @app_commands.command(name="buy", description="Comprar un item de la tienda")
    @app_commands.describe(item_id="ID del item que quieres comprar")
    async def buy_item(self, interaction: discord.Interaction, item_id: int):
        """Comprar item"""
        db = SessionLocal()
        try:
            # Obtener usuario
            user = PointsService.get_or_create_user(
                db,
                interaction.user.id,
                interaction.user.name,
                interaction.user.discriminator
            )
            
            # Obtener item
            item = ShopService.get_item_by_id(db, item_id)
            if not item:
                await interaction.response.send_message("❌ Item no encontrado.", ephemeral=True)
                return
            
            # Intentar comprar
            success, message, purchase = ShopService.purchase_item(db, user, item)
            
            if not success:
                await interaction.response.send_message(f"❌ {message}", ephemeral=True)
                return
            
            # Compra exitosa
            embed = discord.Embed(
                title="✅ Compra Exitosa",
                description=f"Has comprado **{item.name}**",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )
            
            embed.add_field(
                name="💰 Precio Pagado",
                value=f"{item.price:,} pts",
                inline=True
            )
            
            embed.add_field(
                name="💳 Puntos Restantes",
                value=f"{user.points:,} pts",
                inline=True
            )
            
            # Si es un rol, asignarlo
            if item.item_type == 'role' and item.discord_role_id:
                discord_role = interaction.guild.get_role(item.discord_role_id)
                if discord_role:
                    try:
                        await interaction.user.add_roles(discord_role)
                        embed.add_field(
                            name="🎭 Rol Asignado",
                            value=discord_role.mention,
                            inline=False
                        )
                    except Exception as e:
                        bot_logger.error(f"Error asignando rol comprado: {e}")
            
            await interaction.response.send_message(embed=embed)
            
            # Anunciar compra
            from bot.cogs.announcements import AnnouncementsCog
            await AnnouncementsCog.announce_purchase(
                self.bot, interaction.guild, interaction.user, item
            )
        
        finally:
            db.close()
    
    @app_commands.command(name="purchases", description="Ver tu historial de compras")
    async def my_purchases(self, interaction: discord.Interaction):
        """Ver historial de compras"""
        db = SessionLocal()
        try:
            user = PointsService.get_or_create_user(
                db,
                interaction.user.id,
                interaction.user.name,
                interaction.user.discriminator
            )
            
            purchases = ShopService.get_user_purchases(db, user)
            
            if not purchases:
                await interaction.response.send_message(
                    "❌ No has realizado ninguna compra aún.",
                    ephemeral=True
                )
                return
            
            embed = discord.Embed(
                title=f"🛍️ Historial de Compras",
                description=f"Compras de {interaction.user.display_name}",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            
            for purchase in purchases[:10]:  # Últimas 10 compras
                timestamp = int(purchase.purchased_at.timestamp())
                embed.add_field(
                    name=purchase.item.name,
                    value=f"💰 {purchase.price_paid:,} pts • <t:{timestamp}:R>",
                    inline=False
                )
            
            if len(purchases) > 10:
                embed.set_footer(text=f"Mostrando 10 de {len(purchases)} compras")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        
        finally:
            db.close()


async def setup(bot):
    await bot.add_cog(Shop(bot))
