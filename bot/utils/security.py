"""
Funciones de seguridad (hashing, tokens, etc.)
"""
import bcrypt
import secrets
import string
from typing import List

def hash_password(password: str) -> str:
    """
    Hash de contraseña usando bcrypt
    
    Args:
        password: Contraseña en texto plano
    
    Returns:
        Hash de la contraseña
    """
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """
    Verificar contraseña contra hash
    
    Args:
        password: Contraseña en texto plano
        hashed: Hash almacenado
    
    Returns:
        True si coincide, False si no
    """
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def generate_recovery_codes(count: int = 10) -> List[str]:
    """
    Generar códigos de recuperación para MFA
    
    Args:
        count: Cantidad de códigos a generar
    
    Returns:
        Lista de códigos de recuperación
    """
    codes = []
    for _ in range(count):
        code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        # Formato: XXXX-XXXX
        formatted_code = f"{code[:4]}-{code[4:]}"
        codes.append(formatted_code)
    return codes

def generate_secret_key(length: int = 32) -> str:
    """
    Generar clave secreta aleatoria
    
    Args:
        length: Longitud de la clave
    
    Returns:
        Clave secreta
    """
    return secrets.token_urlsafe(length)

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitizar entrada de usuario
    
    Args:
        text: Texto a sanitizar
        max_length: Longitud máxima permitida
    
    Returns:
        Texto sanitizado
    """
    # Eliminar caracteres nulos y limitar longitud
    sanitized = text.replace('\x00', '').strip()
    return sanitized[:max_length]
