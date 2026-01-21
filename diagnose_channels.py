"""
Script simple para verificar la configuración de canales directamente en MySQL
"""
import mysql.connector
import json
from dotenv import load_dotenv
import os

load_dotenv()

# Parsear DATABASE_URL
# Formato: mysql://user:password@host:port/database
database_url = os.getenv('DATABASE_URL')
print(f"DATABASE_URL: {database_url}\n")

# Extraer componentes
# mysql://botuser:HaoE%*pZBNV2TJpW&j9!*d^@db:3306/botdiscord
parts = database_url.replace('mysql://', '').split('@')
user_pass = parts[0].split(':')
host_db = parts[1].split('/')
host_port = host_db[0].split(':')

user = user_pass[0]
password = ':'.join(user_pass[1:])  # En caso de que la contraseña tenga :
host = host_port[0]
port = int(host_port[1]) if len(host_port) > 1 else 3306
database = host_db[1]

print(f"Conectando a MySQL:")
print(f"  Host: {host}:{port}")
print(f"  Database: {database}")
print(f"  User: {user}")
print()

try:
    conn = mysql.connector.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database
    )
    
    cursor = conn.cursor()
    
    # Consultar configuración de canales
    cursor.execute("""
        SELECT id, config_type, channel_ids, is_enabled 
        FROM channel_config 
        WHERE config_type = 'points_channels'
    """)
    
    result = cursor.fetchone()
    
    if not result:
        print("❌ NO HAY CONFIGURACIÓN DE CANALES EN LA BASE DE DATOS")
    else:
        config_id, config_type, channel_ids, is_enabled = result
        print("✓ Configuración encontrada:")
        print(f"  ID: {config_id}")
        print(f"  Tipo: {config_type}")
        print(f"  Habilitado: {is_enabled}")
        print(f"  channel_ids (raw): {repr(channel_ids)}")
        print(f"  Tipo: {type(channel_ids)}")
        print()
        
        if channel_ids:
            try:
                channels = json.loads(channel_ids)
                print(f"✓ Canales parseados:")
                print(f"  Cantidad: {len(channels)}")
                for i, ch in enumerate(channels, 1):
                    print(f"  Canal {i}: {repr(ch)} (tipo: {type(ch).__name__})")
                
                print()
                print("✓ Conversión a strings:")
                channels_str = [str(ch) for ch in channels]
                for i, ch in enumerate(channels_str, 1):
                    print(f"  Canal {i}: '{ch}'")
                
                print()
                print("✓ Prueba de comparación:")
                test_id = 1456356805468074088
                print(f"  ID de prueba: {test_id}")
                print(f"  str(ID): '{str(test_id)}'")
                print(f"  ¿Está en lista? {str(test_id) in channels_str}")
                
            except Exception as e:
                print(f"❌ Error parseando: {e}")
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error de conexión: {e}")
