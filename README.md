# Bot de Discord Profesional

Bot de Discord completo con sistema de puntos, roles automáticos, tienda, eventos y panel web administrativo.

## 🚀 Características

- **Sistema de Puntos**: Gana puntos por actividad con cooldown anti-spam
- **Roles Automáticos**: Asignación automática de roles según puntos alcanzados
- **Tienda**: Compra roles y beneficios con puntos
- **Eventos**: Sistema de eventos con validación de participación y recompensas
- **Anuncios**: Notificaciones automáticas de level-ups y compras
- **Panel Web**: Administración completa desde el navegador con MFA
- **Backups Automáticos**: Backups diarios con rotación de 30 días
- **Seguridad**: Protección contra spam, SQL injection, y autenticación MFA

## 📋 Requisitos

- Python 3.10 o superior
- Discord Bot Token ([Crear bot](https://discord.com/developers/applications))
- Servidor Discord con permisos de administrador

## ⚙️ Instalación

### 1. Clonar el repositorio

```bash
git clone <tu-repositorio>
cd botdiscord
```

### 2. Crear entorno virtual

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

```bash
# Copiar archivo de ejemplo
copy .env.example .env

# Editar .env con tus valores
notepad .env
```

**Variables importantes:**

```env
# Token del bot (obtener en Discord Developer Portal)
DISCORD_TOKEN=tu_token_aqui

# ID de tu servidor de Discord
DISCORD_GUILD_ID=123456789

# IDs de administradores (separados por comas)
ADMIN_USER_IDS=123456789,987654321

# Configuración de puntos
POINTS_PER_MESSAGE=10
MESSAGE_COOLDOWN=60
INACTIVITY_DAYS=60
INACTIVITY_PENALTY=0.25

# Clave secreta para panel web (cambiar en producción)
WEB_SECRET_KEY=cambia_esto_en_produccion
```

### 5. Inicializar base de datos

```bash
python -c "from bot.database.connection import init_db; init_db()"
```

### 6. Crear usuario administrador para panel web

```bash
python -c "
from bot.database.connection import SessionLocal
from bot.database.models import AdminUser
from bot.utils.security import hash_password

db = SessionLocal()
admin = AdminUser(
    username='admin',
    password_hash=hash_password('admin123'),
    is_active=True
)
db.add(admin)
db.commit()
print('Usuario admin creado: admin / admin123')
db.close()
"
```

**⚠️ IMPORTANTE:** Cambia la contraseña después del primer login.

## 🎮 Uso

### Iniciar el Bot

```bash
python -m bot.main
```

### Iniciar el Panel Web

```bash
python -m web.main
```

Acceder a: `http://localhost:8000`

## 📝 Comandos del Bot

### Comandos de Usuario

- `/points` - Ver tus puntos
- `/points @usuario` - Ver puntos de otro usuario
- `/leaderboard` - Ver top de usuarios
- `/roles` - Ver roles disponibles
- `/myroles` - Ver tus roles actuales
- `/shop` - Ver tienda
- `/buy <id>` - Comprar item
- `/purchases` - Ver historial de compras
- `/events` - Ver eventos activos
- `/event-join <id>` - Unirse a evento
- `/help` - Ver ayuda

### Comandos de Admin

- `/admin-add-points @usuario <puntos>` - Añadir puntos
- `/admin-set-points @usuario <puntos>` - Establecer puntos
- `/admin-create-role` - Crear rol
- `/admin-create-item` - Crear item de tienda
- `/admin-create-event` - Crear evento
- `/admin-stats` - Ver estadísticas del servidor

## 🗄️ Estructura del Proyecto

```
botdiscord/
├── bot/                    # Bot de Discord
│   ├── cogs/              # Comandos (points, roles, shop, events, admin)
│   ├── database/          # Modelos y conexión
│   ├── services/          # Lógica de negocio
│   ├── tasks/             # Tareas programadas
│   ├── utils/             # Utilidades
│   ├── config.py          # Configuración
│   └── main.py            # Punto de entrada
├── web/                    # Panel web (próximamente)
├── data/                   # Base de datos SQLite
├── backups/                # Backups automáticos
├── logs/                   # Logs del sistema
├── .env                    # Variables de entorno
└── requirements.txt        # Dependencias
```

## 🔧 Configuración Avanzada

### Configurar Canales de Anuncios

Desde el panel web o directamente en la base de datos:

```sql
INSERT INTO announcement_config (announcement_type, channel_id, is_enabled)
VALUES ('level_up', 123456789, 1);

INSERT INTO announcement_config (announcement_type, channel_id, is_enabled)
VALUES ('purchase', 123456789, 1);

INSERT INTO announcement_config (announcement_type, channel_id, is_enabled)
VALUES ('event', 123456789, 1);
```

### Crear Roles Iniciales

```python
python -c "
from bot.database.connection import SessionLocal
from bot.services.role_service import RoleService

db = SessionLocal()

# Rol Bronce
RoleService.create_role(
    db, 'Bronce', 123456789, points_required=100, 
    color='#CD7F32', auto_assign=True
)

# Rol Plata
RoleService.create_role(
    db, 'Plata', 987654321, points_required=500,
    color='#C0C0C0', auto_assign=True
)

# Rol Oro
RoleService.create_role(
    db, 'Oro', 111222333, points_required=1000,
    color='#FFD700', auto_assign=True
)

print('Roles creados')
db.close()
"
```

## 🔒 Seguridad

- **Nunca** compartas tu `.env` o `DISCORD_TOKEN`
- Cambia `WEB_SECRET_KEY` en producción
- Activa MFA para usuarios admin del panel web
- Mantén las dependencias actualizadas: `pip install --upgrade -r requirements.txt`

## 📊 Backups

Los backups se crean automáticamente cada día a las 04:00 AM en la carpeta `backups/`.

### Restaurar un Backup

```python
python -c "
from bot.tasks.backup import BackupService
BackupService.restore_backup('bot_backup_2026-01-03_04-00-00.db.gz')
"
```

## 🐛 Troubleshooting

### El bot no se conecta

- Verifica que `DISCORD_TOKEN` sea correcto
- Asegúrate de que el bot tenga los intents habilitados en Discord Developer Portal:
  - Message Content Intent
  - Server Members Intent
  - Presence Intent

### Los comandos no aparecen

- Espera unos minutos (Discord puede tardar en sincronizar)
- Verifica que el bot tenga permisos de "applications.commands"

### Error de base de datos

```bash
# Recrear base de datos (CUIDADO: borra todos los datos)
python -c "from bot.database.connection import drop_all, init_db; drop_all(); init_db()"
```

## 📚 Documentación Adicional

- [Guía de Monitoring](monitoring_guide.md) - Configurar UptimeRobot, Sentry, Healthchecks.io
- [Plan de Implementación](implementation_plan.md) - Arquitectura y decisiones de diseño

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/nueva-caracteristica`)
3. Commit tus cambios (`git commit -am 'Añadir nueva característica'`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Crea un Pull Request

## 📄 Licencia

Este proyecto es de código abierto. Úsalo como quieras.

## ✨ Créditos

Desarrollado con ❤️ usando:
- [discord.py](https://github.com/Rapptz/discord.py)
- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://www.sqlalchemy.org/)
- [APScheduler](https://apscheduler.readthedocs.io/)

---

**¿Necesitas ayuda?** Abre un issue en GitHub o contacta al desarrollador.
