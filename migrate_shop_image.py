"""
Script para agregar columna image_url a la tabla shop_items
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bot.database.connection import engine
from sqlalchemy import text

print("Agregando columna image_url a tabla shop_items...")

try:
    with engine.connect() as conn:
        # Verificar si la columna ya existe
        result = conn.execute(text("PRAGMA table_info(shop_items)"))
        columns = [row[1] for row in result]
        
        if 'image_url' not in columns:
            # Agregar columna
            conn.execute(text("ALTER TABLE shop_items ADD COLUMN image_url VARCHAR(500)"))
            conn.commit()
            print("✅ Columna image_url agregada exitosamente")
        else:
            print("ℹ️  La columna image_url ya existe")
    
    print("\n✅ Migración completada")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
