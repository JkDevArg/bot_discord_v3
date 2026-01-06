"""
Validadores de entrada
"""
import re
from typing import Optional

def validate_discord_id(discord_id: int) -> bool:
    """
    Validar que un Discord ID sea válido
    
    Args:
        discord_id: ID de Discord
    
    Returns:
        True si es válido, False si no
    """
    # Discord IDs son snowflakes de 64 bits
    return 17 <= len(str(discord_id)) <= 20

def validate_points(points: int, min_val: int = -999999, max_val: int = 999999) -> bool:
    """
    Validar cantidad de puntos
    
    Args:
        points: Cantidad de puntos
        min_val: Valor mínimo permitido
        max_val: Valor máximo permitido
    
    Returns:
        True si es válido, False si no
    """
    return min_val <= points <= max_val

def validate_hex_color(color: str) -> bool:
    """
    Validar código de color hexadecimal
    
    Args:
        color: Color en formato #RRGGBB
    
    Returns:
        True si es válido, False si no
    """
    pattern = r'^#[0-9A-Fa-f]{6}$'
    return bool(re.match(pattern, color))

def validate_username(username: str) -> tuple[bool, Optional[str]]:
    """
    Validar nombre de usuario para admin
    
    Args:
        username: Nombre de usuario
    
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    if len(username) < 3:
        return False, "El nombre de usuario debe tener al menos 3 caracteres"
    
    if len(username) > 50:
        return False, "El nombre de usuario no puede tener más de 50 caracteres"
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "El nombre de usuario solo puede contener letras, números, guiones y guiones bajos"
    
    return True, None

def validate_password(password: str) -> tuple[bool, Optional[str]]:
    """
    Validar contraseña
    
    Args:
        password: Contraseña
    
    Returns:
        Tupla (es_válida, mensaje_error)
    """
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"
    
    if len(password) > 128:
        return False, "La contraseña no puede tener más de 128 caracteres"
    
    # Verificar que tenga al menos una letra y un número
    if not re.search(r'[a-zA-Z]', password):
        return False, "La contraseña debe contener al menos una letra"
    
    if not re.search(r'[0-9]', password):
        return False, "La contraseña debe contener al menos un número"
    
    return True, None

def validate_item_type(item_type: str) -> bool:
    """
    Validar tipo de item de tienda
    
    Args:
        item_type: Tipo de item
    
    Returns:
        True si es válido, False si no
    """
    valid_types = ['role', 'benefit', 'custom']
    return item_type in valid_types

def validate_announcement_type(announcement_type: str) -> bool:
    """
    Validar tipo de anuncio
    
    Args:
        announcement_type: Tipo de anuncio
    
    Returns:
        True si es válido, False si no
    """
    valid_types = ['level_up', 'purchase', 'event']
    return announcement_type in valid_types
