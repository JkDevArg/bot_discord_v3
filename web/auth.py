"""
Sistema de autenticación JWT
"""
from datetime import datetime, timedelta
from typing import Optional
import jwt
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from bot.config import WEB_SECRET_KEY
from bot.database.connection import SessionLocal
from bot.database.models import AdminUser
from bot.utils.security import verify_password
from web.mfa import MFAService


# Configuración JWT
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

security = HTTPBearer()


class AuthService:
    """Servicio de autenticación"""
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Crear token JWT
        
        Args:
            data: Datos a incluir en el token
            expires_delta: Tiempo de expiración
        
        Returns:
            Token JWT
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, WEB_SECRET_KEY, algorithm=ALGORITHM)
        
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> dict:
        """
        Verificar y decodificar token JWT
        
        Args:
            token: Token JWT
        
        Returns:
            Payload del token
        
        Raises:
            HTTPException si el token es inválido
        """
        try:
            payload = jwt.decode(token, WEB_SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expirado")
        except jwt.JWTError:
            raise HTTPException(status_code=401, detail="Token inválido")
    
    @staticmethod
    def authenticate_user(username: str, password: str) -> Optional[AdminUser]:
        """
        Autenticar usuario (fase 1: usuario/contraseña)
        
        Args:
            username: Nombre de usuario
            password: Contraseña
        
        Returns:
            Usuario si las credenciales son válidas, None si no
        """
        db = SessionLocal()
        try:
            user = db.query(AdminUser).filter(
                AdminUser.username == username,
                AdminUser.is_active == True
            ).first()
            
            if not user:
                return None
            
            if not verify_password(password, user.password_hash):
                return None
            
            return user
        finally:
            db.close()
    
    @staticmethod
    def verify_mfa_token(user: AdminUser, token: str, use_recovery: bool = False) -> bool:
        """
        Verificar token MFA (fase 2)
        
        Args:
            user: Usuario
            token: Código TOTP o código de recuperación
            use_recovery: Si es True, usar código de recuperación
        
        Returns:
            True si el token es válido
        """
        if not user.mfa_enabled:
            return True  # MFA no habilitado, pasar
        
        if use_recovery:
            # Verificar código de recuperación
            valid, updated_codes = MFAService.verify_recovery_code(
                user.recovery_codes, token
            )
            
            if valid:
                # Actualizar códigos en base de datos
                db = SessionLocal()
                try:
                    db_user = db.query(AdminUser).filter(AdminUser.id == user.id).first()
                    db_user.recovery_codes = updated_codes
                    db.commit()
                finally:
                    db.close()
            
            return valid
        else:
            # Verificar TOTP
            return MFAService.verify_totp(user.mfa_secret, token)


async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> AdminUser:
    """
    Dependency para obtener usuario actual desde token JWT
    
    Args:
        credentials: Credenciales HTTP Bearer
    
    Returns:
        Usuario actual
    
    Raises:
        HTTPException si no está autenticado
    """
    token = credentials.credentials
    payload = AuthService.verify_token(token)
    
    username = payload.get("sub")
    if username is None:
        raise HTTPException(status_code=401, detail="Token inválido")
    
    db = SessionLocal()
    try:
        user = db.query(AdminUser).filter(
            AdminUser.username == username,
            AdminUser.is_active == True
        ).first()
        
        if user is None:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")
        
        return user
    finally:
        db.close()
