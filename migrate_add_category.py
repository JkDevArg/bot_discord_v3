"""
Script para agregar la columna category_id a la tabla shop_items
Ejecutar con: docker exec -it discord_bot python migrate_add_category.py
"""
from bot.database.connection import SessionLocal, engine
from sqlalchemy import text

def migrate():
    db = SessionLocal()
    try:
        # Verificar si la columna ya existe
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='shop_items' AND column_name='category_id'
        """))
        
        if result.fetchone():
            print("✅ La columna category_id ya existe")
            return
        
        # Agregar la columna
        print("📝 Agregando columna category_id a shop_items...")
        db.execute(text("""
            ALTER TABLE shop_items 
            ADD COLUMN category_id INTEGER REFERENCES item_categories(id)
        """))
        db.commit()
        print("✅ Columna category_id agregada exitosamente!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate()
