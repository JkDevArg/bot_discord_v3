#!/bin/bash

# =============================================================================
# Discord Bot - Automated MySQL Installation Script
# =============================================================================
# This script automatically sets up the bot with MySQL in production
# Run this ONCE after cloning the repository to your server
# =============================================================================

set -e  # Exit on error

echo "🚀 Discord Bot - Automated MySQL Setup"
echo "======================================"
echo ""

# Check if running in correct directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ Error: docker-compose.yml not found"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Function to generate secure random password
generate_password() {
    python3 -c "import secrets, string; print(''.join(secrets.choice(string.ascii_letters + string.digits + '!@#$%^&*') for _ in range(24)))"
}

# Check if .env already exists
if [ -f ".env" ]; then
    echo "⚠️  Warning: .env file already exists"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Keeping existing .env file"
        echo "Skipping to Docker setup..."
        SKIP_ENV=true
    else
        rm .env
        SKIP_ENV=false
    fi
else
    SKIP_ENV=false
fi

# Create .env from template if needed
if [ "$SKIP_ENV" = false ]; then
    echo "📝 Creating .env file with secure credentials..."
    
    # Prompt for Discord credentials
    echo ""
    read -p "Enter your Discord Bot Token: " discord_token
    while [ -z "$discord_token" ]; do
        echo "❌ Discord token cannot be empty"
        read -p "Enter your Discord Bot Token: " discord_token
    done
    
    read -p "Enter your Discord Guild (Server) ID: " guild_id
    while [ -z "$guild_id" ]; do
        echo "❌ Guild ID cannot be empty"
        read -p "Enter your Discord Guild (Server) ID: " guild_id
    done
    
    read -p "Enter your Discord User ID (for admin access): " admin_id
    while [ -z "$admin_id" ]; do
        echo "❌ Admin User ID cannot be empty"
        read -p "Enter your Discord User ID (for admin access): " admin_id
    done
    
    # Generate secure credentials automatically
    echo ""
    echo "🔐 Generating secure credentials..."
    
    mysql_root_password=$(generate_password)
    mysql_password=$(generate_password)
    web_secret_key=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    
    # Create .env file
    cat > .env << EOF
# =============================================================================
# DISCORD BOT - ENVIRONMENT CONFIGURATION
# =============================================================================
# Auto-generated on $(date)
# =============================================================================

# -----------------------------------------------------------------------------
# Discord Configuration
# -----------------------------------------------------------------------------
DISCORD_TOKEN=$discord_token
DISCORD_GUILD_ID=$guild_id
ADMIN_USER_IDS=$admin_id

# -----------------------------------------------------------------------------
# Database Configuration (MySQL)
# -----------------------------------------------------------------------------
DATABASE_URL=mysql://botuser:$mysql_password@db:3306/botdiscord

# MySQL credentials (used by docker-compose.yml)
MYSQL_ROOT_PASSWORD=$mysql_root_password
MYSQL_DATABASE=botdiscord
MYSQL_USER=botuser
MYSQL_PASSWORD=$mysql_password

# -----------------------------------------------------------------------------
# Web Panel Configuration
# -----------------------------------------------------------------------------
WEB_SECRET_KEY=$web_secret_key
WEB_HOST=0.0.0.0
WEB_PORT=8000

# -----------------------------------------------------------------------------
# Points System Configuration
# -----------------------------------------------------------------------------
POINTS_PER_MESSAGE=10
MESSAGE_COOLDOWN=10
MAX_POINTS_PER_HOUR=100
INACTIVITY_DAYS=60
INACTIVITY_PENALTY=0.25

# -----------------------------------------------------------------------------
# Backup Configuration
# -----------------------------------------------------------------------------
BACKUP_ENABLED=true
BACKUP_RETENTION_DAYS=30

# -----------------------------------------------------------------------------
# Environment
# -----------------------------------------------------------------------------
ENVIRONMENT=production
EOF

    echo "✅ .env file created with secure auto-generated credentials"
    
    # Save credentials to a secure file
    cat > .credentials.txt << EOF
=============================================================================
DISCORD BOT - GENERATED CREDENTIALS
=============================================================================
Generated on: $(date)

IMPORTANT: Save these credentials securely and delete this file!

MySQL Root Password: $mysql_root_password
MySQL Bot User Password: $mysql_password
Web Secret Key: $web_secret_key

Admin User ID: $admin_id
=============================================================================
EOF
    
    chmod 600 .credentials.txt
    echo "📄 Credentials saved to .credentials.txt (delete after saving securely!)"
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

# Wait for MySQL to be ready
echo ""
echo "⏳ Waiting for MySQL to be ready..."
sleep 15

# Check if MySQL is ready
max_attempts=30
attempt=0
until docker exec discord_db mysqladmin ping -h localhost -u root -p"${MYSQL_ROOT_PASSWORD:-rootpassword}" --silent 2>/dev/null; do
    attempt=$((attempt + 1))
    if [ $attempt -ge $max_attempts ]; then
        echo "❌ MySQL failed to start after $max_attempts attempts"
        echo "Check logs with: docker compose logs db"
        exit 1
    fi
    echo "   Waiting for MySQL... (attempt $attempt/$max_attempts)"
    sleep 2
done

echo "✅ MySQL is ready"

# Initialize database
echo ""
echo "📊 Initializing database..."
docker exec discord_bot python init_db.py

# Create admin user automatically
echo ""
echo "👤 Creating admin user..."

# Prompt for admin credentials
read -p "Admin username [admin]: " admin_username
admin_username=${admin_username:-admin}

read -sp "Admin password (leave empty for auto-generated): " admin_password
echo ""

if [ -z "$admin_password" ]; then
    admin_password=$(generate_password)
    echo "🔐 Generated secure password for admin user"
fi

# Create admin user
docker exec discord_bot python -c "
from bot.database.connection import SessionLocal
from bot.database.models import AdminUser
from bot.utils.security import hash_password

db = SessionLocal()
try:
    # Check if admin already exists
    existing = db.query(AdminUser).filter(AdminUser.username == '$admin_username').first()
    if existing:
        print('⚠️  Admin user already exists, skipping...')
    else:
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
    print(f'❌ Error creating admin: {e}')
    db.rollback()
finally:
    db.close()
"

# Save admin credentials
if [ ! -f ".credentials.txt" ]; then
    cat > .credentials.txt << EOF
=============================================================================
DISCORD BOT - ADMIN CREDENTIALS
=============================================================================
Generated on: $(date)

Admin Username: $admin_username
Admin Password: $admin_password
=============================================================================
EOF
else
    cat >> .credentials.txt << EOF

Admin Username: $admin_username
Admin Password: $admin_password
EOF
fi

chmod 600 .credentials.txt

# Show status
echo ""
echo "📊 Container Status:"
docker compose ps

# Get server IP
SERVER_IP=$(hostname -I | awk '{print $1}')
if [ -z "$SERVER_IP" ]; then
    SERVER_IP="localhost"
fi

echo ""
echo "✅ ============================================"
echo "✅ SETUP COMPLETE!"
echo "✅ ============================================"
echo ""
echo "🌐 Web Panel: http://$SERVER_IP:8010"
echo "👤 Username: $admin_username"
echo "🔑 Password: $admin_password"
echo ""
echo "⚠️  IMPORTANT SECURITY NOTES:"
echo "   1. Credentials saved in .credentials.txt"
echo "   2. DELETE .credentials.txt after saving passwords securely!"
echo "   3. Change admin password after first login"
echo "   4. Never commit .env or .credentials.txt to git"
echo ""
echo "📝 Next steps:"
echo "   1. Access the web panel at the URL above"
echo "   2. Change your admin password in Settings"
echo "   3. Configure your Discord bot settings"
echo "   4. DELETE .credentials.txt file!"
echo ""
echo "🔧 Useful commands:"
echo "   docker compose logs -f        # View logs"
echo "   docker compose restart        # Restart services"
echo "   docker compose down           # Stop services"
echo "   docker compose ps             # Check status"
echo ""
echo "🔒 Security reminder:"
echo "   rm .credentials.txt           # Delete credentials file"
echo ""
