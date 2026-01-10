#!/bin/bash

# =============================================================================
# Discord Bot - Production Initialization Script
# =============================================================================
# This script sets up the bot for the first time in production
# Run this ONCE after cloning the repository to your VPS
# =============================================================================

set -e  # Exit on error

echo "🚀 Discord Bot - Production Setup"
echo "=================================="
echo ""

# Check if running in correct directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Check if .env already exists
if [ -f ".env" ]; then
    echo "⚠️  Warning: .env file already exists"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing .env file"
    else
        rm .env
    fi
fi

# Create .env from template if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    
    # Copy template
    cp .env.example .env
    
    # Prompt for Discord token
    echo ""
    read -p "Enter your Discord Bot Token: " discord_token
    sed -i "s/your_discord_bot_token_here/$discord_token/" .env
    
    # Prompt for Guild ID
    read -p "Enter your Discord Guild (Server) ID: " guild_id
    sed -i "s/your_guild_id_here/$guild_id/" .env
    
    # Prompt for Admin User ID
    read -p "Enter your Discord User ID (for admin access): " admin_id
    sed -i "s/your_discord_user_id_here/$admin_id/" .env
    
    # Generate secure secret key
    echo "🔐 Generating secure secret key..."
    secret_key=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    sed -i "s/change_this_to_a_random_secure_string/$secret_key/" .env
    
    echo "✅ .env file created successfully"
fi

# Stop any existing containers
echo ""
echo "🛑 Stopping existing containers..."
docker compose down -v 2>/dev/null || true

# Build and start containers
echo ""
echo "🏗️  Building Docker images..."
docker compose build

echo ""
echo "🚀 Starting services..."
docker compose up -d

# Wait for database to be ready
echo ""
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 10

# Check if database is ready
until docker exec discord_db pg_isready -U postgres >/dev/null 2>&1; do
    echo "   Waiting for database..."
    sleep 2
done

echo "✅ PostgreSQL is ready"

# Initialize database
echo ""
echo "📊 Initializing database..."
docker exec -it discord_bot python init_db.py

# Create admin user
echo ""
echo "👤 Creating admin user..."
echo ""
read -p "Admin username [xampl3]: " admin_username
admin_username=${admin_username:-xampl3}

read -sp "Admin password: " admin_password
echo ""

if [ -z "$admin_password" ]; then
    admin_password="change_me_please"
    echo "⚠️  Using default password: $admin_password"
fi

docker exec -it discord_bot python -c "
from bot.database.connection import SessionLocal
from bot.database.models import AdminUser
from bot.utils.security import hash_password

db = SessionLocal()
try:
    admin = AdminUser(
        username='$admin_username',
        password_hash=hash_password('$admin_password'),
        discord_id=$admin_id,
        is_active=True,
        mfa_enabled=False
    )
    db.add(admin)
    db.commit()
    print('✅ Admin user created successfully!')
except Exception as e:
    if 'unique' in str(e).lower():
        print('⚠️  Admin user already exists')
    else:
        print(f'❌ Error: {e}')
finally:
    db.close()
"

# Show status
echo ""
echo "📊 Container Status:"
docker compose ps

echo ""
echo "✅ Setup Complete!"
echo ""
echo "🌐 Web Panel: http://$(hostname -I | awk '{print $1}'):8010"
echo "👤 Username: $admin_username"
echo "🔑 Password: $admin_password"
echo ""
echo "📝 Next steps:"
echo "   1. Access the web panel at the URL above"
echo "   2. Change your admin password in Settings"
echo "   3. Configure your Discord bot settings"
echo ""
echo "🔧 Useful commands:"
echo "   docker compose logs -f        # View logs"
echo "   docker compose restart        # Restart services"
echo "   docker compose down           # Stop services"
echo ""
