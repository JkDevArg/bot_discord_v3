"""
Utilidades para sanitización y validación de inputs
Protección contra XSS, SQL Injection y otros ataques
"""
import re
import bleach
from typing import Optional, Any
from html import escape

# Configuración de bleach para sanitización HTML
ALLOWED_TAGS = []  # No permitir ningún tag HTML por defecto
ALLOWED_ATTRIBUTES = {}
ALLOWED_PROTOCOLS = ['http', 'https']


def sanitize_html(text: str) -> str:
    """
    Sanitiza HTML eliminando todos los tags y atributos peligrosos
    
    Args:
        text: Texto a sanitizar
        
    Returns:
        Texto sanitizado sin HTML peligroso
    """
    if not text:
        return ""
    
    # Usar bleach para limpiar HTML
    cleaned = bleach.clean(
        text,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True
    )
    
    return cleaned.strip()


def sanitize_string(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitiza un string general eliminando caracteres peligrosos
    
    Args:
        text: Texto a sanitizar
        max_length: Longitud máxima permitida
        
    Returns:
        Texto sanitizado
    """
    if not text:
        return ""
    
    # Eliminar HTML
    cleaned = sanitize_html(text)
    
    # Escapar caracteres especiales
    cleaned = escape(cleaned)
    
    # Limitar longitud si se especifica
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
    
    return cleaned.strip()


def sanitize_username(username: str) -> str:
    """
    Sanitiza un nombre de usuario
    Solo permite letras, números, guiones y guiones bajos
    
    Args:
        username: Nombre de usuario a sanitizar
        
    Returns:
        Nombre de usuario sanitizado
    """
    if not username:
        return ""
    
    # Permitir solo caracteres alfanuméricos, guiones y guiones bajos
    cleaned = re.sub(r'[^\w\-]', '', username)
    
    # Limitar longitud
    return cleaned[:100]


def sanitize_discord_id(discord_id: Any) -> Optional[int]:
    """
    Valida y sanitiza un Discord ID
    
    Args:
        discord_id: ID de Discord a validar
        
    Returns:
        Discord ID como entero o None si es inválido
    """
    try:
        # Convertir a int y validar que sea positivo
        id_int = int(discord_id)
        if id_int > 0:
            return id_int
    except (ValueError, TypeError):
        pass
    
    return None


def sanitize_url(url: str) -> Optional[str]:
    """
    Valida y sanitiza una URL
    Solo permite HTTP y HTTPS
    
    Args:
        url: URL a validar
        
    Returns:
        URL sanitizada o None si es inválida
    """
    if not url:
        return None
    
    # Verificar que comience con http:// o https://
    if not re.match(r'^https?://', url, re.IGNORECASE):
        return None
    
    # Limpiar espacios
    url = url.strip()
    
    # Limitar longitud
    if len(url) > 2000:
        return None
    
    return url


def sanitize_integer(value: Any, min_value: Optional[int] = None, max_value: Optional[int] = None) -> Optional[int]:
    """
    Valida y sanitiza un valor entero
    
    Args:
        value: Valor a validar
        min_value: Valor mínimo permitido
        max_value: Valor máximo permitido
        
    Returns:
        Entero validado o None si es inválido
    """
    try:
        int_value = int(value)
        
        # Validar rango
        if min_value is not None and int_value < min_value:
            return None
        if max_value is not None and int_value > max_value:
            return None
        
        return int_value
    except (ValueError, TypeError):
        return None


def sanitize_float(value: Any, min_value: Optional[float] = None, max_value: Optional[float] = None) -> Optional[float]:
    """
    Valida y sanitiza un valor flotante
    
    Args:
        value: Valor a validar
        min_value: Valor mínimo permitido
        max_value: Valor máximo permitido
        
    Returns:
        Float validado o None si es inválido
    """
    try:
        float_value = float(value)
        
        # Validar rango
        if min_value is not None and float_value < min_value:
            return None
        if max_value is not None and float_value > max_value:
            return None
        
        return float_value
    except (ValueError, TypeError):
        return None


def validate_email(email: str) -> bool:
    """
    Valida formato de email
    
    Args:
        email: Email a validar
        
    Returns:
        True si el email es válido
    """
    if not email:
        return False
    
    # Patrón básico de validación de email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def sanitize_json_string(text: str) -> str:
    """
    Sanitiza un string que será almacenado como JSON
    
    Args:
        text: Texto a sanitizar
        
    Returns:
        Texto sanitizado para JSON
    """
    if not text:
        return ""
    
    # Eliminar caracteres de control
    cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    
    # Sanitizar HTML
    cleaned = sanitize_html(cleaned)
    
    return cleaned.strip()
