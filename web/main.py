"""
Aplicación principal de FastAPI
"""
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from bot.config import WEB_HOST, WEB_PORT, ENVIRONMENT
from bot.utils.logger import web_logger
from bot.database.connection import init_db
from web.auth_cookie import get_current_user_cookie

# Importar routers
from web.api.auth_routes import router as auth_router
from web.api.users import router as users_router

# Crear aplicación FastAPI
app = FastAPI(
    title="Discord Bot Admin Panel",
    description="Panel administrativo para gestionar el bot de Discord",
    version="1.0.0",
    docs_url="/api/docs" if ENVIRONMENT == "development" else None,
    redoc_url="/api/redoc" if ENVIRONMENT == "development" else None
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if ENVIRONMENT == "development" else ["https://tu-dominio.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar archivos estáticos
try:
    app.mount("/static", StaticFiles(directory="web/static"), name="static")
except:
    web_logger.warning("Directorio static no encontrado, se creará automáticamente")
    os.makedirs("web/static", exist_ok=True)
    app.mount("/static", StaticFiles(directory="web/static"), name="static")

# Configurar templates
templates = Jinja2Templates(directory="web/templates")

# Registrar routers
app.include_router(auth_router, prefix="/api")
app.include_router(users_router, prefix="/api")

# Importar router de moderación
from web.api.moderation import router as moderation_router
app.include_router(moderation_router, prefix="/api")

# Importar router de configuración
from web.api.config import router as config_router
app.include_router(config_router, prefix="/api")

# Importar router de pruebas
from web.api.test import router as test_router
app.include_router(test_router, prefix="/api")

# Importar router de roles
from web.api.roles import router as roles_router
app.include_router(roles_router, prefix="/api")

# Importar router de tienda
from web.api.shop import router as shop_router
app.include_router(shop_router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    """Evento de inicio"""
    web_logger.info("Iniciando panel web administrativo...")
    web_logger.info(f"Entorno: {ENVIRONMENT}")
    
    # Asegurar que la base de datos está inicializada
    try:
        init_db()
        web_logger.info("Base de datos verificada")
    except Exception as e:
        web_logger.error(f"Error inicializando base de datos: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Evento de cierre"""
    web_logger.info("Cerrando panel web administrativo...")


@app.get("/")
async def root():
    """Ruta raíz - redirigir al login"""
    return RedirectResponse(url="/login")


@app.get("/login")
async def login_page(request: Request):
    """Página de login"""
    # Si ya tiene cookie válida, ir al dashboard
    user = await get_current_user_cookie(request)
    if user:
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/dashboard")
async def dashboard_page(request: Request, user = Depends(get_current_user_cookie)):
    """Dashboard principal"""
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user})


@app.get("/users")
async def users_page(request: Request, user = Depends(get_current_user_cookie)):
    """Página de gestión de usuarios"""
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("users.html", {"request": request, "user": user})


@app.get("/roles")
async def roles_page(request: Request, user = Depends(get_current_user_cookie)):
    """Página de gestión de roles"""
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("roles.html", {"request": request, "user": user})


@app.get("/shop")
async def shop_page(request: Request, user = Depends(get_current_user_cookie)):
    """Página de gestión de tienda"""
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("shop.html", {"request": request, "user": user})


@app.get("/events")
async def events_page(request: Request, user = Depends(get_current_user_cookie)):
    """Página de gestión de eventos"""
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("events.html", {"request": request, "user": user})


@app.get("/settings")
async def settings_page(request: Request, user = Depends(get_current_user_cookie)):
    """Página de configuración"""
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("settings.html", {"request": request, "user": user})


@app.get("/test-log")
async def test_log_page(request: Request):
    """Página de prueba de logging"""
    return templates.TemplateResponse("test_log.html", {"request": request})


@app.get("/test-level")
async def test_level_page(request: Request):
    """Página de prueba de anuncios de nivel"""
    return templates.TemplateResponse("test_level.html", {"request": request})


@app.get("/api/health")
async def health_check():
    """Health check para monitoring"""
    from datetime import datetime
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": ENVIRONMENT
    }


def main():
    """Función principal para iniciar el servidor"""
    import uvicorn
    
    web_logger.info(f"Iniciando servidor en {WEB_HOST}:{WEB_PORT}")
    
    uvicorn.run(
        "web.main:app",
        host=WEB_HOST,
        port=WEB_PORT,
        reload=ENVIRONMENT == "development",
        log_level="info"
    )


if __name__ == "__main__":
    main()
