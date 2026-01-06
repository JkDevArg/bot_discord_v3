# Panel Web Administrativo - Guía de Uso

## 🌐 Descripción

Panel web administrativo construido con **FastAPI** para gestionar el bot de Discord. Incluye autenticación JWT, MFA (TOTP), y gestión completa de usuarios, puntos, niveles, roles, tienda y eventos.

## 🚀 Iniciar el Panel Web

```bash
# Asegúrate de tener el bot configurado primero
python init_db.py

# Iniciar el panel web
python -m web.main
```

El panel estará disponible en: `http://localhost:8000`

## 🔐 Autenticación

### Login Inicial

1. Accede a `http://localhost:8000/login`
2. Usa las credenciales del admin creado:
   - Usuario: `admin`
   - Contraseña: `admin123`

**⚠️ IMPORTANTE:** Cambia la contraseña después del primer login.

### Autenticación de Dos Factores (MFA)

El panel soporta MFA con TOTP (compatible con Google Authenticator, Authy, Microsoft Authenticator, etc.).

**Configurar MFA:**

1. Login al panel
2. Ve a Configuración
3. Click en "Configurar MFA"
4. Escanea el código QR con tu app de autenticación
5. Ingresa el código de 6 dígitos para confirmar
6. Guarda los códigos de recuperación en un lugar seguro

**Login con MFA:**

1. Ingresa usuario y contraseña
2. Ingresa el código de 6 dígitos de tu app

**Códigos de Recuperación:**

Si pierdes acceso a tu app de autenticación, puedes usar uno de los 10 códigos de recuperación generados durante la configuración. Cada código solo se puede usar una vez.

## 📊 Dashboard

El dashboard muestra:

- **Estadísticas en tiempo real:**
  - Total de usuarios
  - Puntos totales en circulación
  - Nivel promedio
  - EXP total ganada

- **Top Usuarios:**
  - Usuario con más puntos
  - Usuario con nivel más alto

- **Acciones Rápidas:**
  - Gestionar Usuarios
  - Gestionar Roles
  - Gestionar Tienda
  - Crear Eventos

## 🔧 API Endpoints

### Autenticación

**POST** `/api/auth/login`
```json
{
  "username": "admin",
  "password": "admin123"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "mfa_required": false
}
```

**POST** `/api/auth/verify-mfa`
```json
{
  "username": "admin",
  "token": "123456",
  "use_recovery": false
}
```

**GET** `/api/auth/me`
- Headers: `Authorization: Bearer <token>`
- Retorna información del usuario actual

**GET** `/api/auth/mfa/setup`
- Obtener QR code y secret para configurar MFA

**POST** `/api/auth/mfa/enable`
```json
{
  "token": "123456"
}
```

**POST** `/api/auth/mfa/disable`
- Desactivar MFA

### Usuarios

**GET** `/api/users/`
- Listar usuarios (paginado)
- Query params: `skip`, `limit`

**GET** `/api/users/stats`
- Estadísticas de usuarios

**GET** `/api/users/{user_id}`
- Obtener usuario específico

**PUT** `/api/users/{user_id}/points`
```json
{
  "points": 1000
}
```

**PUT** `/api/users/{user_id}/level`
```json
{
  "level": 20
}
```

## 🎨 Interfaz de Usuario

### Tema Discord

El panel usa un tema inspirado en Discord con:
- Colores oscuros (#2C2F33, #23272A)
- Color primario Discord (#5865F2)
- Sidebar con navegación
- Cards con sombras
- Iconos Bootstrap Icons

### Páginas Disponibles

- `/login` - Página de login con MFA
- `/dashboard` - Dashboard principal
- `/users` - Gestión de usuarios (próximamente)
- `/roles` - Gestión de roles (próximamente)
- `/shop` - Gestión de tienda (próximamente)
- `/events` - Gestión de eventos (próximamente)
- `/settings` - Configuración y MFA

## 🔒 Seguridad

### JWT Tokens

- Expiración: 60 minutos
- Algoritmo: HS256
- Secret key: Configurada en `.env` (`WEB_SECRET_KEY`)

### MFA (TOTP)

- Algoritmo: TOTP (Time-based One-Time Password)
- Ventana de validación: ±30 segundos
- Códigos de 6 dígitos
- 10 códigos de recuperación de un solo uso

### Protecciones

- ✅ Autenticación requerida en todos los endpoints (excepto login)
- ✅ Tokens JWT con expiración
- ✅ MFA opcional pero recomendado
- ✅ Códigos de recuperación para MFA
- ✅ CORS configurado
- ✅ Passwords hasheados con bcrypt

## 📝 Configuración

Variables de entorno en `.env`:

```env
# Panel Web
WEB_HOST=0.0.0.0
WEB_PORT=8000
WEB_SECRET_KEY=cambia_esto_en_produccion_usa_algo_muy_seguro
```

## 🛠️ Desarrollo

### Modo Desarrollo

```bash
# El panel se recarga automáticamente al detectar cambios
python -m web.main
```

- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

### Estructura

```
web/
├── __init__.py
├── main.py              # Aplicación FastAPI
├── auth.py              # Autenticación JWT
├── mfa.py               # Sistema MFA (TOTP)
├── api/
│   ├── __init__.py
│   ├── auth_routes.py   # Endpoints de auth
│   └── users.py         # Endpoints de usuarios
├── static/              # CSS, JS, imágenes
└── templates/           # HTML templates
    ├── base.html        # Template base
    ├── login.html       # Página de login
    └── dashboard.html   # Dashboard
```

## 🚀 Producción

### Deployment

1. **Cambiar SECRET_KEY:**
```bash
# Generar nueva secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

2. **Configurar CORS:**
```python
# En web/main.py
allow_origins=["https://tu-dominio.com"]
```

3. **Usar HTTPS:**
- Configurar reverse proxy (nginx/Apache)
- Certificado SSL (Let's Encrypt)

4. **Process Manager:**
```bash
# Usar supervisor, systemd, o PM2
```

### Ejemplo con systemd

```ini
[Unit]
Description=Discord Bot Web Panel
After=network.target

[Service]
Type=simple
User=botuser
WorkingDirectory=/path/to/botdiscord
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python -m web.main
Restart=always

[Install]
WantedBy=multi-user.target
```

## 📊 Monitoring

Health check endpoint:

```bash
curl http://localhost:8000/api/health
```

Response:
```json
{
  "status": "ok",
  "timestamp": "2026-01-03T07:00:00",
  "environment": "production"
}
```

## 🐛 Troubleshooting

### El panel no inicia

```bash
# Verificar que el puerto no esté en uso
netstat -ano | findstr :8000

# Verificar logs
tail -f logs/web.log
```

### Error de autenticación

- Verificar que `WEB_SECRET_KEY` esté configurada
- Verificar que la base de datos esté inicializada
- Verificar que exista un usuario admin

### MFA no funciona

- Verificar que la hora del servidor esté sincronizada (TOTP depende del tiempo)
- Usar códigos de recuperación si perdiste acceso a la app

---

**¡El panel web está listo para usar!** 🎉
