#!/bin/bash

# =============================================================================
# Discord Bot - Deployment Script
# =============================================================================
# Use this script to deploy updates after git pull
# This script is safe to run multiple times
# =============================================================================

set -e  # Exit on error

echo "🚀 Discord Bot - Deployment"
echo "==========================="
echo ""

# Check if running in correct directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found"
    echo "Please run ./init_production.sh first for initial setup"
    exit 1
fi

# Pull latest changes
echo "📥 Pulling latest changes..."
git pull origin main

# Rebuild and restart services
echo ""
echo "🏗️  Rebuilding services..."
docker compose build

echo ""
echo "🔄 Restarting services..."
docker compose up -d

# Wait for database
echo ""
echo "⏳ Waiting for database..."
sleep 5

# Show status
echo ""
echo "📊 Container Status:"
docker compose ps

echo ""
echo "✅ Deployment Complete!"
echo ""
echo "📝 View logs with: docker compose logs -f"
echo ""
