#!/bin/bash
# Script de despliegue para el bot de Discord
# Uso: ./deploy.sh [--create-admin]

set -e  # Salir si hay algún error

echo "🚀 Iniciando despliegue del bot de Discord..."
echo ""

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Verificar que estamos en el directorio correcto
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ Error: docker-compose.yml no encontrado${NC}"
    echo "Asegúrate de estar en el directorio del proyecto"
    exit 1
fi

# Verificar que existe el archivo .env
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  Archivo .env no encontrado${NC}"
    if [ -f ".env.example" ]; then
        echo "Copiando .env.example a .env..."
        cp .env.example .env
        echo -e "${GREEN}✅ Archivo .env creado desde .env.example${NC}"
    else
        echo -e "${RED}❌ Error: .env.example tampoco existe${NC}"
        exit 1
    fi
fi

# Verificar que DATABASE_URL usa PostgreSQL
echo -e "${BLUE}🔍 Verificando configuración de base de datos...${NC}"
if grep -q "sqlite" .env; then
    echo -e "${YELLOW}⚠️  .env está configurado para SQLite${NC}"
    echo "Actualizando a PostgreSQL..."
    sed -i 's|DATABASE_URL=sqlite:///data/bot.db|DATABASE_URL=postgresql://postgres:postgres@db:5432/botdiscord|g' .env
    echo -e "${GREEN}✅ DATABASE_URL actualizado a PostgreSQL${NC}"
else
    echo -e "${GREEN}✅ DATABASE_URL ya está configurado para PostgreSQL${NC}"
fi

echo ""
echo "📦 Deteniendo contenedores existentes..."
docker compose down

echo ""
echo "🔨 Construyendo imágenes..."
docker compose build --no-cache

echo ""
echo "🚀 Levantando servicios..."
docker compose up -d

echo ""
echo -e "${BLUE}⏳ Esperando a que PostgreSQL esté listo...${NC}"
for i in {1..30}; do
    if docker exec discord_db pg_isready -U postgres > /dev/null 2>&1; then
        echo -e "${GREEN}✅ PostgreSQL está listo${NC}"
        break
    fi
    echo -n "."
    sleep 1
done
echo ""

# Esperar un poco más para asegurar que el bot inicialice las tablas
echo -e "${BLUE}⏳ Esperando a que el bot inicialice las tablas...${NC}"
sleep 5

echo ""
echo "📊 Estado de los contenedores:"
docker compose ps

# Crear usuario administrador si se pasa el flag --create-admin o si es la primera vez
CREATE_ADMIN=false
if [ "$1" == "--create-admin" ]; then
    CREATE_ADMIN=true
fi

# Verificar si ya existe algún usuario admin
ADMIN_COUNT=$(docker exec discord_bot python -c "
from bot.database.connection import SessionLocal
from bot.database.models import AdminUser
db = SessionLocal()
try:
    count = db.query(AdminUser).count()
    print(count)
finally:
    db.close()
" 2>/dev/null || echo "0")

if [ "$ADMIN_COUNT" == "0" ]; then
    echo ""
    echo -e "${YELLOW}⚠️  No se encontraron usuarios administradores${NC}"
    CREATE_ADMIN=true
fi

if [ "$CREATE_ADMIN" == "true" ]; then
    echo ""
    echo -e "${BLUE}👤 Creando usuario administrador...${NC}"
    echo ""
    
    # Solicitar datos del usuario
    read -p "Nombre de usuario [xampl3]: " ADMIN_USER
    ADMIN_USER=${ADMIN_USER:-xampl3}
    
    read -sp "Contraseña [asd02322]: " ADMIN_PASS
    ADMIN_PASS=${ADMIN_PASS:-asd02322}
    echo ""
    
    read -p "Discord ID [1008954720079065139]: " DISCORD_ID
    DISCORD_ID=${DISCORD_ID:-1008954720079065139}
    
    # Crear el usuario
    docker exec discord_bot python -c "
from bot.database.connection import SessionLocal
from bot.database.models import AdminUser
from bot.utils.security import hash_password

db = SessionLocal()
try:
    admin = AdminUser(
        username='$ADMIN_USER',
        password_hash=hash_password('$ADMIN_PASS'),
        discord_id=$DISCORD_ID,
        is_active=True,
        mfa_enabled=False
    )
    db.add(admin)
    db.commit()
    print('✅ Usuario administrador creado exitosamente!')
    print('   Username: $ADMIN_USER')
    print('   Discord ID: $DISCORD_ID')
except Exception as e:
    if 'unique' in str(e).lower():
        print('⚠️  El usuario ya existe')
    else:
        print(f'❌ Error: {e}')
finally:
    db.close()
"
fi

echo ""
echo -e "${GREEN}✅ Despliegue completado${NC}"
echo ""
echo "📝 Comandos útiles:"
echo "  - Ver logs:           docker compose logs -f"
echo "  - Ver logs del bot:   docker compose logs -f bot"
echo "  - Ver logs del web:   docker compose logs -f web"
echo "  - Reiniciar:          docker compose restart"
echo "  - Detener:            docker compose down"
echo "  - Crear admin:        ./deploy.sh --create-admin"
echo ""
echo "🌐 Panel web disponible en: http://localhost:8010"
echo ""
