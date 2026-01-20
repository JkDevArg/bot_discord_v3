"""
Script para inicializar estadísticas diarias
Ejecutar manualmente para poblar datos históricos
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.services.daily_stats_service import DailyStatsService
from bot.utils.logger import bot_logger


def main():
    """Inicializar estadísticas de los últimos 30 días"""
    print("=" * 60)
    print("Inicializando Estadísticas Diarias")
    print("=" * 60)
    print()
    
    try:
        # Backfill de los últimos 30 días
        print("📊 Procesando estadísticas de los últimos 30 días...")
        DailyStatsService.backfill_stats(days=30)
        
        print()
        print("✅ Estadísticas inicializadas correctamente")
        print()
        
        # Mostrar resumen
        print("📈 Resumen de los últimos 7 días:")
        print("-" * 60)
        
        stats = DailyStatsService.get_stats_summary(days=7)
        
        if stats:
            for stat in stats:
                print(f"{stat.date.strftime('%Y-%m-%d')}: "
                      f"{stat.active_users} usuarios, "
                      f"{stat.total_messages} mensajes, "
                      f"{stat.points_awarded} puntos, "
                      f"{stat.new_users} nuevos")
        else:
            print("No hay datos disponibles")
        
        print("-" * 60)
        print()
        print("🎉 Proceso completado exitosamente")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        bot_logger.error(f"Error in init_daily_stats: {e}", exc_info=e)
        sys.exit(1)


if __name__ == "__main__":
    main()
