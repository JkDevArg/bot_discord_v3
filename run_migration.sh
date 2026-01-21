#!/bin/bash
# Script para ejecutar la migración de la base de datos

echo "=========================================="
echo "Arreglando tabla activity_log"
echo "=========================================="

# Obtener credenciales del .env
source .env

# Ejecutar SQL dentro del contenedor de MySQL
docker compose exec -T db mysql -u${MYSQL_USER} -p${MYSQL_PASSWORD} ${MYSQL_DATABASE} < fix_activity_log.sql

echo ""
echo "✅ Migración completada"
echo "Ahora reinicia el bot: docker compose restart bot"
