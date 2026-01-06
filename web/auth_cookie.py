from fastapi import Request
import jwt
from web.auth import ALGORITHM
from bot.config import WEB_SECRET_KEY
from bot.database.connection import SessionLocal
from bot.database.models import AdminUser

async def get_current_user_cookie(request: Request):
    """
    Dependency that checks for a valid 'access_token' cookie.
    If missing or invalid, it returns None (and the route handler will redirect).
    """
    token = request.cookies.get("access_token")
    if not token:
        return None

    try:
        # Remove 'Bearer ' prefix if present
        if token.startswith("Bearer "):
            token = token.split(" ")[1]
            
        payload = jwt.decode(token, WEB_SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
    except jwt.PyJWTError:
        return None

    # Database check
    db = SessionLocal()
    try:
        user = db.query(AdminUser).filter(AdminUser.username == username).first()
        if user is None:
            return None
        return user
    finally:
        db.close()
