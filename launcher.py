"""
Launcher unificado para bot y panel web
"""
import asyncio
import uvicorn
from multiprocessing import Process
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot.utils.logger import bot_logger, web_logger


def run_bot():
    """Ejecutar bot de Discord"""
    import asyncio
    from bot.main import main
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        bot_logger.info("Bot detenido")


def run_web():
    """Ejecutar panel web"""
    from web.main import app
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    print("=" * 60)
    print("  DISCORD BOT - SISTEMA UNIFICADO")
    print("=" * 60)
    print()
    print("Iniciando servicios...")
    print("  - Bot de Discord")
    print("  - Panel Web (http://localhost:8000)")
    print()
    print("Presiona Ctrl+C para detener todos los servicios")
    print("=" * 60)
    print()
    
    # Crear procesos
    bot_process = Process(target=run_bot, name="Discord Bot")
    web_process = Process(target=run_web, name="Web Panel")
    
    try:
        # Iniciar bot primero
        bot_process.start()
        
        # Esperar un poco para que el bot se inicialice
        import time
        time.sleep(3)
        
        # Iniciar panel web
        web_process.start()
        
        # Esperar a que terminen
        bot_process.join()
        web_process.join()
        
    except KeyboardInterrupt:
        print("\n\nDeteniendo servicios...")
        bot_process.terminate()
        web_process.terminate()
        bot_process.join()
        web_process.join()
        print("Servicios detenidos correctamente")
