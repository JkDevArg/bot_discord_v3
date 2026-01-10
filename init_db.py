"""
Database initialization script
Creates all tables and ensures schema is up to date
Safe to run multiple times (idempotent)
"""
from bot.database.connection import SessionLocal, engine, Base
from bot.database.models import *
from sqlalchemy import text, inspect
import sys

def check_column_exists(table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table"""
    inspector = inspect(engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def init_database():
    """Initialize database with all tables and migrations"""
    print("🔧 Initializing database...")
    
    try:
        # Create all tables
        print("📊 Creating tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ Tables created")
        
        # Check and add category_id column if missing
        if not check_column_exists('shop_items', 'category_id'):
            print("📝 Adding category_id column to shop_items...")
            db = SessionLocal()
            try:
                db.execute(text("""
                    ALTER TABLE shop_items 
                    ADD COLUMN category_id INTEGER REFERENCES item_categories(id)
                """))
                db.commit()
                print("✅ category_id column added")
            except Exception as e:
                print(f"⚠️  Could not add category_id: {e}")
                db.rollback()
            finally:
                db.close()
        else:
            print("✅ category_id column already exists")
        
        # Verify critical tables exist
        inspector = inspect(engine)
        required_tables = ['users', 'shop_items', 'item_categories', 'admin_users']
        existing_tables = inspector.get_table_names()
        
        for table in required_tables:
            if table in existing_tables:
                print(f"✅ Table '{table}' exists")
            else:
                print(f"❌ Table '{table}' missing!")
                return False
        
        print("\n✅ Database initialized successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error initializing database: {e}")
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)
