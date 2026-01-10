#!/bin/bash
# Script de despliegue para el bot de Discord
# Uso: ./deploy.sh

set -e  # Salir si hay algún error

echo "🚀 Iniciando despliegue del bot de Discord..."
echo ""

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
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
        echo -e "${YELLOW}⚠️  IMPORTANTE: Edita el archivo .env con tus credenciales${NC}"
        echo "Presiona Enter para continuar después de editar .env..."
        read
    else
        echo -e "${RED}❌ Error: .env.example tampoco existe${NC}"
        exit 1
    fi
fi

# Verificar que DATABASE_URL usa PostgreSQL
if grep -q "sqlite" .env; then
    echo -e "${RED}❌ Error: .env está configurado para SQLite${NC}"
    echo "Actualizando a PostgreSQL..."
    sed -i 's|DATABASE_URL=sqlite:///data/bot.db|DATABASE_URL=postgresql://postgres:postgres@db:5432/botdiscord|g' .env
    echo -e "${GREEN}✅ DATABASE_URL actualizado a PostgreSQL${NC}"
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
echo "⏳ Esperando a que PostgreSQL esté listo..."
sleep 10

echo ""
echo "📊 Estado de los contenedores:"
docker compose ps

echo ""
echo -e "${GREEN}✅ Despliegue completado${NC}"
echo ""
echo "📝 Comandos útiles:"
echo "  - Ver logs:           docker compose logs -f"
echo "  - Ver logs del bot:   docker compose logs -f bot"
echo "  - Ver logs del web:   docker compose logs -f web"
echo "  - Reiniciar:          docker compose restart"
echo "  - Detener:            docker compose down"
echo ""
echo "🌐 Panel web disponible en: http://localhost:8010"
echo ""
