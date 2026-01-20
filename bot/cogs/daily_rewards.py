"""
Cog para sistema de recompensas diarias
"""
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timedelta
from bot.database.connection import SessionLocal
from bot.database.models import User, DailyReward
from bot.services.points_service import PointsService
from bot.utils.logger import bot_logger


class DailyRewardsCog(commands.Cog):
    """Sistema de recompensas diarias con streaks"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="daily", description="Reclama tu recompensa diaria")
    async def daily_reward(self, interaction: discord.Interaction):
        """Comando para reclamar recompensa diaria"""
        db = SessionLocal()
        try:
            # Obtener o crear usuario
            user = PointsService.get_or_create_user(
                db,
                interaction.user.id,
                interaction.user.name,
                interaction.user.discriminator
            )
            
            # Obtener o crear registro de daily reward
            daily_reward = db.query(DailyReward).filter(
                DailyReward.user_id == user.id
            ).first()
            
            now = datetime.utcnow()
            
            if daily_reward:
                # Verificar si ya reclamó hoy
                time_since_last = now - daily_reward.last_claim
                
                if time_since_last < timedelta(hours=20):
                    # Todavía no puede reclamar
                    hours_left = 20 - (time_since_last.total_seconds() / 3600)
                    embed = discord.Embed(
                        title="⏰ Recompensa Diaria",
                        description=f"Ya reclamaste tu recompensa hoy.\nVuelve en **{hours_left:.1f} horas**.",
                        color=discord.Color.orange()
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return
                
                # Verificar streak
                if time_since_last < timedelta(hours=48):
                    # Mantiene el streak
                    daily_reward.streak_days += 1
                else:
                    # Perdió el streak
                    daily_reward.streak_days = 1
                
                daily_reward.last_claim = now
                daily_reward.total_claims += 1
                
                # Actualizar mejor streak
                if daily_reward.streak_days > daily_reward.best_streak:
                    daily_reward.best_streak = daily_reward.streak_days
            else:
                # Primera vez
                daily_reward = DailyReward(
                    user_id=user.id,
                    last_claim=now,
                    streak_days=1,
                    total_claims=1,
                    best_streak=1
                )
                db.add(daily_reward)
            
            # Calcular recompensa
            base_reward = 50
            streak_bonus = min(daily_reward.streak_days * 10, 200)  # Máx 200 de bonus
            total_reward = base_reward + streak_bonus
            
            # Bonos especiales
            special_bonus = 0
            special_msg = ""
            if daily_reward.streak_days == 7:
                special_bonus = 100
                special_msg = "\n🎉 **¡Bonus semanal!** +100 puntos"
            elif daily_reward.streak_days == 30:
                special_bonus = 500
                special_msg = "\n🏆 **¡Bonus mensual!** +500 puntos"
            
            total_reward += special_bonus
            
            # Otorgar puntos
            user.points += total_reward
            user.total_points_earned += total_reward
            
            db.commit()
            
            # Crear embed de respuesta
            embed = discord.Embed(
                title="🎁 Recompensa Diaria Reclamada",
                description=f"Has recibido **{total_reward} puntos**!",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="💰 Recompensa Base",
                value=f"{base_reward} puntos",
                inline=True
            )
            
            embed.add_field(
                name="🔥 Bonus por Racha",
                value=f"+{streak_bonus} puntos",
                inline=True
            )
            
            embed.add_field(
                name="📊 Racha Actual",
                value=f"**{daily_reward.streak_days}** días consecutivos",
                inline=False
            )
            
            embed.add_field(
                name="🏅 Mejor Racha",
                value=f"{daily_reward.best_streak} días",
                inline=True
            )
            
            embed.add_field(
                name="📈 Total Reclamado",
                value=f"{daily_reward.total_claims} veces",
                inline=True
            )
            
            if special_msg:
                embed.add_field(
                    name="✨ Bonus Especial",
                    value=special_msg,
                    inline=False
                )
            
            embed.set_footer(text=f"Vuelve mañana para mantener tu racha!")
            
            await interaction.response.send_message(embed=embed)
            
            bot_logger.info(f"Daily reward claimed: {interaction.user.name} - {total_reward} points - Streak: {daily_reward.streak_days}")
            
        except Exception as e:
            bot_logger.error(f"Error in daily reward: {e}", exc_info=e)
            await interaction.response.send_message(
                "❌ Ocurrió un error al procesar tu recompensa diaria.",
                ephemeral=True
            )
        finally:
            db.close()
    
    @app_commands.command(name="streak", description="Ver tu racha de recompensas diarias")
    async def check_streak(self, interaction: discord.Interaction):
        """Ver información de racha"""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.discord_id == interaction.user.id).first()
            
            if not user:
                await interaction.response.send_message(
                    "❌ No tienes un perfil todavía. Envía algunos mensajes primero!",
                    ephemeral=True
                )
                return
            
            daily_reward = db.query(DailyReward).filter(
                DailyReward.user_id == user.id
            ).first()
            
            if not daily_reward:
                await interaction.response.send_message(
                    "❌ Aún no has reclamado tu primera recompensa diaria. Usa `/daily`!",
                    ephemeral=True
                )
                return
            
            # Verificar si el streak está activo
            time_since_last = datetime.utcnow() - daily_reward.last_claim
            streak_active = time_since_last < timedelta(hours=48)
            
            embed = discord.Embed(
                title="🔥 Tu Racha de Recompensas",
                color=discord.Color.gold() if streak_active else discord.Color.greyple()
            )
            
            embed.add_field(
                name="📊 Racha Actual",
                value=f"**{daily_reward.streak_days}** días" if streak_active else "**0** días (racha perdida)",
                inline=True
            )
            
            embed.add_field(
                name="🏅 Mejor Racha",
                value=f"{daily_reward.best_streak} días",
                inline=True
            )
            
            embed.add_field(
                name="📈 Total Reclamado",
                value=f"{daily_reward.total_claims} veces",
                inline=True
            )
            
            # Calcular próxima recompensa
            hours_until_next = max(0, 20 - (time_since_last.total_seconds() / 3600))
            
            if hours_until_next > 0:
                embed.add_field(
                    name="⏰ Próxima Recompensa",
                    value=f"En {hours_until_next:.1f} horas",
                    inline=False
                )
            else:
                embed.add_field(
                    name="✅ Disponible",
                    value="¡Puedes reclamar tu recompensa ahora con `/daily`!",
                    inline=False
                )
            
            # Próximos bonos
            next_bonus = ""
            if daily_reward.streak_days < 7:
                next_bonus = f"Día 7: +100 puntos bonus (faltan {7 - daily_reward.streak_days} días)"
            elif daily_reward.streak_days < 30:
                next_bonus = f"Día 30: +500 puntos bonus (faltan {30 - daily_reward.streak_days} días)"
            
            if next_bonus:
                embed.add_field(
                    name="🎯 Próximo Objetivo",
                    value=next_bonus,
                    inline=False
                )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            bot_logger.error(f"Error checking streak: {e}", exc_info=e)
            await interaction.response.send_message(
                "❌ Ocurrió un error al verificar tu racha.",
                ephemeral=True
            )
        finally:
            db.close()


async def setup(bot):
    await bot.add_cog(DailyRewardsCog(bot))
