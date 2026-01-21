"""
Script de migración para arreglar la tabla activity_log
Elimina las columnas de backup que fueron agregadas por error
"""
from dotenv import load_dotenv
load_dotenv()

import os
import mysql.connector

# Parsear DATABASE_URL
database_url = os.getenv('DATABASE_URL')
parts = database_url.replace('mysql://', '').split('@')
user_pass = parts[0].split(':')
host_db = parts[1].split('/')
host_port = host_db[0].split(':')

user = user_pass[0]
password = ':'.join(user_pass[1:])
host = host_port[0]
port = int(host_port[1]) if len(host_port) > 1 else 3306
database = host_db[1]

print("=" * 60)
print("MIGRACIÓN: Arreglar tabla activity_log")
print("=" * 60)
print(f"\nConectando a: {host}:{port}/{database}")

try:
    conn = mysql.connector.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database
    )
    
    cursor = conn.cursor()
    
    # Verificar si las columnas existen
    cursor.execute("""
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = %s 
        AND TABLE_NAME = 'activity_log'
        AND COLUMN_NAME IN ('backup_path', 'file_size', 'success', 'error_message')
    """, (database,))
    
    existing_columns = [row[0] for row in cursor.fetchall()]
    
    if not existing_columns:
        print("\n✓ La tabla activity_log ya está correcta (no tiene columnas de backup)")
        cursor.close()
        conn.close()
        exit(0)
    
    print(f"\n⚠️  Columnas a eliminar: {existing_columns}")
    print("\nEsto eliminará las siguientes columnas de la tabla activity_log:")
    for col in existing_columns:
        print(f"  - {col}")
    
    response = input("\n¿Continuar? (s/n): ")
    if response.lower() != 's':
        print("Migración cancelada")
        cursor.close()
        conn.close()
        exit(0)
    
    # Eliminar cada columna
    for column in existing_columns:
        print(f"\nEliminando columna '{column}'...")
        try:
            cursor.execute(f"ALTER TABLE activity_log DROP COLUMN {column}")
            print(f"  ✓ Columna '{column}' eliminada")
        except Exception as e:
            print(f"  ❌ Error eliminando '{column}': {e}")
    
    # Commit de los cambios
    conn.commit()
    
    print("\n" + "=" * 60)
    print("✅ MIGRACIÓN COMPLETADA")
    print("=" * 60)
    print("\nAhora reinicia el bot con: docker-compose restart bot")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"\n❌ Error de conexión: {e}")
    print("\nNOTA: Si estás usando Docker, ejecuta este script dentro del contenedor:")
    print("  docker-compose exec bot python fix_activity_log.py")
