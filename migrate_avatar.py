"""
Script para agregar columna avatar_url a la tabla users
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.database.connection import engine
from sqlalchemy import text

print("Agregando columna avatar_url a tabla users...")

try:
    with engine.connect() as conn:
        # Verificar si la columna ya existe
        result = conn.execute(text("PRAGMA table_info(users)"))
        columns = [row[1] for row in result]
        
        if 'avatar_url' not in columns:
            # Agregar columna
            conn.execute(text("ALTER TABLE users ADD COLUMN avatar_url VARCHAR(255)"))
            conn.commit()
            print("✅ Columna avatar_url agregada exitosamente")
        else:
            print("ℹ️  La columna avatar_url ya existe")
    
    print("\n✅ Migración completada")
    print("\n🔄 Ahora reinicia el bot y el panel web:")
    print("   1. Bot: Ctrl+C → python -m bot.main")
    print("   2. Panel web: Ctrl+C → python -m web.main")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
