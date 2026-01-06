"""
Endpoints de autenticación
"""
from fastapi import APIRouter, HTTPException, Depends, Response
from pydantic import BaseModel
from datetime import timedelta
from bot.database.connection import SessionLocal
from bot.database.models import AdminUser
from web.auth import AuthService, get_current_user, ACCESS_TOKEN_EXPIRE_MINUTES
from web.mfa import MFAService
from bot.utils.logger import web_logger
import json


router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    username: str
    password: str


class MFAVerifyRequest(BaseModel):
    username: str
    token: str
    use_recovery: bool = False


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    mfa_required: bool = False


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, response: Response):
    """
    Login - Fase 1: Verificar usuario/contraseña
    """
    user = AuthService.authenticate_user(request.username, request.password)
    
    if not user:
        web_logger.warning(f"Intento de login fallido: {request.username}")
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    # Si MFA está habilitado, requerir verificación
    if user.mfa_enabled:
        web_logger.info(f"Login exitoso (MFA pendiente): {request.username}")
        return TokenResponse(
            access_token="",
            token_type="bearer",
            mfa_required=True
        )
    
    # MFA no habilitado, generar token directamente
    access_token = AuthService.create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    # Set Cookie
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    
    # Actualizar último login
    db = SessionLocal()
    try:
        from datetime import datetime
        db_user = db.query(AdminUser).filter(AdminUser.id == user.id).first()
        db_user.last_login = datetime.utcnow()
        db.commit()
    finally:
        db.close()
    
    web_logger.info(f"Login exitoso: {request.username}")
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        mfa_required=False
    )


@router.post("/verify-mfa", response_model=TokenResponse)
async def verify_mfa(request: MFAVerifyRequest, response: Response):
    """
    Login - Fase 2: Verificar código MFA
    """
    # Primero verificar credenciales básicas
    db = SessionLocal()
    try:
        user = db.query(AdminUser).filter(
            AdminUser.username == request.username,
            AdminUser.is_active == True
        ).first()
        
        if not user or not user.mfa_enabled:
            raise HTTPException(status_code=401, detail="Usuario inválido o MFA no habilitado")
        
        # Verificar token MFA
        if not AuthService.verify_mfa_token(user, request.token, request.use_recovery):
            web_logger.warning(f"Código MFA inválido: {request.username}")
            raise HTTPException(status_code=401, detail="Código MFA inválido")
        
        # Generar token JWT
        access_token = AuthService.create_access_token(
            data={"sub": user.username},
            expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        )

        # Set Cookie
        response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",
            httponly=True,
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            expires=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
        
        # Actualizar último login
        from datetime import datetime
        user.last_login = datetime.utcnow()
        db.commit()
        
        web_logger.info(f"Login con MFA exitoso: {request.username}")
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            mfa_required=False
        )
    
    finally:
        db.close()


@router.get("/mfa/setup")
async def setup_mfa(current_user: AdminUser = Depends(get_current_user)):
    """
    Obtener información para configurar MFA
    """
    if current_user.mfa_enabled:
        return {"message": "MFA ya está habilitado"}
    
    # Generar nuevo secreto y QR
    mfa_data = MFAService.setup_mfa_for_user(current_user.username)
    
    # Guardar secreto temporalmente (no activar hasta confirmar)
    db = SessionLocal()
    try:
        db_user = db.query(AdminUser).filter(AdminUser.id == current_user.id).first()
        db_user.mfa_secret = mfa_data['secret']
        db_user.recovery_codes = json.dumps(mfa_data['recovery_codes'])
        db.commit()
    finally:
        db.close()
    
    return {
        "qr_code": mfa_data['qr_code'],
        "secret": mfa_data['secret'],
        "recovery_codes": mfa_data['recovery_codes']
    }


class EnableMFARequest(BaseModel):
    token: str


@router.post("/mfa/enable")
async def enable_mfa(request: EnableMFARequest, current_user: AdminUser = Depends(get_current_user)):
    """
    Activar MFA después de verificar que funciona
    """
    if current_user.mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA ya está habilitado")
    
    if not current_user.mfa_secret:
        raise HTTPException(status_code=400, detail="Primero configura MFA con /mfa/setup")
    
    # Verificar que el token funciona
    if not MFAService.verify_totp(current_user.mfa_secret, request.token):
        raise HTTPException(status_code=401, detail="Código MFA inválido")
    
    # Activar MFA
    db = SessionLocal()
    try:
        db_user = db.query(AdminUser).filter(AdminUser.id == current_user.id).first()
        db_user.mfa_enabled = True
        db.commit()
        
        web_logger.info(f"MFA habilitado para: {current_user.username}")
    finally:
        db.close()
    
    return {"message": "MFA habilitado exitosamente"}


@router.post("/mfa/disable")
async def disable_mfa(current_user: AdminUser = Depends(get_current_user)):
    """
    Desactivar MFA
    """
    if not current_user.mfa_enabled:
        raise HTTPException(status_code=400, detail="MFA no está habilitado")
    
    db = SessionLocal()
    try:
        db_user = db.query(AdminUser).filter(AdminUser.id == current_user.id).first()
        db_user.mfa_enabled = False
        db_user.mfa_secret = None
        db_user.recovery_codes = None
        db.commit()
        
        web_logger.info(f"MFA deshabilitado para: {current_user.username}")
    finally:
        db.close()
    
    return {"message": "MFA deshabilitado"}


@router.get("/me")
async def get_current_user_info(current_user: AdminUser = Depends(get_current_user)):
    """
    Obtener información del usuario actual
    """
    return {
        "id": current_user.id,
        "username": current_user.username,
        "mfa_enabled": current_user.mfa_enabled,
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
        "created_at": current_user.created_at.isoformat()
    }


@router.post("/logout")
async def logout(response: Response):
    """
    Cerrar sesión eliminando la cookie de autenticación
    """
    response.delete_cookie(key="access_token")
    web_logger.info("Logout exitoso")
    return {"message": "Sesión cerrada correctamente"}
