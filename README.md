# Discord Bot with Web Panel

A feature-rich Discord bot with points system, shop, events, and a modern web administration panel.

## Features

- 🎯 **Points System**: Reward users for activity with customizable points
- 🛒 **Shop System**: Create items, categories, and manage purchases
- 👥 **User Management**: Track users, roles, and statistics
- 📊 **Web Panel**: Modern admin interface for managing everything
- 🎉 **Events**: Create and manage server events
- 🔔 **Webhooks**: Automated notifications for important events
- 📈 **Analytics**: Track user activity and engagement

## Quick Start (Production)

### Prerequisites

- Docker and Docker Compose installed
- A Discord bot token ([Get one here](https://discord.com/developers/applications))
- Your Discord server (guild) ID
- Your Discord user ID (for admin access)

### Initial Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url> /opt/bot_discord
   cd /opt/bot_discord
   ```

2. **Run the initialization script**
   ```bash
   chmod +x init_production.sh
   ./init_production.sh
   ```

   This script will:
   - Create your `.env` file with your Discord credentials
   - Generate a secure secret key
   - Build and start Docker containers
   - Initialize the database
   - Create your admin user

3. **Access the web panel**
   - URL: `http://your-server-ip:8010`
   - Login with the credentials you created

### Deploying Updates

When you want to update the bot with new code:

```bash
cd /opt/bot_discord
./deploy.sh
```

This will:
- Pull the latest changes from git
- Rebuild the Docker images
- Restart the services

**Important**: Your `.env` file and database are preserved during updates.

## Environment Variables

All configuration is done through the `.env` file. See `.env.example` for all available options.

### Required Variables

- `DISCORD_TOKEN`: Your bot token
- `DISCORD_GUILD_ID`: Your server ID
- `ADMIN_USER_IDS`: Your Discord user ID
- `DATABASE_URL`: PostgreSQL connection string (auto-configured for Docker)
- `WEB_SECRET_KEY`: Secret key for web panel (auto-generated)

### Optional Variables

- `POINTS_PER_MESSAGE`: Points per message (default: 10)
- `MESSAGE_COOLDOWN`: Cooldown in seconds (default: 10)
- `MAX_POINTS_PER_HOUR`: Max points per hour (default: 100)
- See `.env.example` for more options

## Manual Commands

### View Logs
```bash
docker compose logs -f          # All services
docker compose logs -f bot      # Bot only
docker compose logs -f web      # Web panel only
```

### Restart Services
```bash
docker compose restart          # All services
docker compose restart web      # Web panel only
```

### Stop Services
```bash
docker compose down             # Stop all
docker compose down -v          # Stop and remove volumes (⚠️ deletes database)
```

### Create Additional Admin Users
```bash
docker exec -it discord_bot python create_admin.py
```

### Database Backup
```bash
docker exec discord_db pg_dump -U postgres botdiscord > backup_$(date +%Y%m%d).sql
```

### Database Restore
```bash
cat backup_20260110.sql | docker exec -i discord_db psql -U postgres botdiscord
```

## Troubleshooting

### Bot won't start
- Check logs: `docker compose logs bot`
- Verify Discord token in `.env`
- Ensure database is running: `docker compose ps`

### Can't access web panel
- Check if port 8010 is open in your firewall
- Verify web service is running: `docker compose ps`
- Check logs: `docker compose logs web`

### Database connection errors
- Ensure `.env` has correct `DATABASE_URL`
- Restart services: `docker compose restart`
- Check database health: `docker exec discord_db pg_isready -U postgres`

### After git pull, services won't start
- Your `.env` file should be preserved
- If issues persist, run: `docker compose down && docker compose up -d`
- Check logs for specific errors

## Project Structure

```
.
├── bot/                    # Discord bot code
│   ├── cogs/              # Bot commands and features
│   ├── database/          # Database models and connection
│   └── services/          # Business logic
├── web/                    # Web panel
│   ├── api/               # API endpoints
│   ├── templates/         # HTML templates
│   └── static/            # CSS, JS, images
├── data/                   # Database and uploads (gitignored)
├── logs/                   # Application logs (gitignored)
├── docker-compose.yml      # Docker configuration
├── Dockerfile              # Docker image definition
├── requirements.txt        # Python dependencies
├── init_production.sh      # Initial setup script
└── deploy.sh              # Update deployment script
```

## Security Notes

- ⚠️ **Never commit `.env` to git** - It contains sensitive credentials
- 🔒 Change the default admin password after first login
- 🔐 Use strong, unique passwords for production
- 🛡️ Keep your Discord bot token secret
- 🔄 Regularly update dependencies and Docker images

## Support

For issues or questions:
1. Check the logs: `docker compose logs -f`
2. Review this README
3. Check `.env.example` for configuration options

## License

[Your License Here]
