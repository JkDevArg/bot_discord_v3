"""
API endpoints para gestión de tienda
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import List, Optional
from bot.database.connection import SessionLocal
from bot.database.models import ShopItem
from web.auth import get_current_user, AdminUser
import os
import uuid
from datetime import datetime

router = APIRouter(prefix="/shop", tags=["Shop"])


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    icon: Optional[str] = None
    is_active: bool = True

class CategoryCreate(CategoryBase):
    pass

class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class ShopItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    price: int = Field(..., gt=0)
    item_type: str = Field(..., pattern="^(role|benefit|custom)$")
    stock: int = -1
    image_url: Optional[str] = None
    is_active: bool = True
    category_id: Optional[int] = None  # New field

class ShopItemCreate(ShopItemBase):
    pass

class ShopItemResponse(ShopItemBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ShopItemUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    price: Optional[int] = None
    item_type: Optional[str] = None
    discord_role_id: Optional[int] = None
    stock: Optional[int] = None
    is_active: Optional[bool] = None
    category_id: Optional[int] = None


class ShopItemResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    image_url: Optional[str]
    price: int
    item_type: str
    discord_role_id: Optional[int]
    stock: int
    is_active: bool
    category_id: Optional[int]
    
    class Config:
        from_attributes = True


@router.get("/categories", response_model=List[CategoryResponse])
async def get_categories(current_user: AdminUser = Depends(get_current_user)):
    """Obtener todas las categorías"""
    db = SessionLocal()
    try:
        from bot.database.models import ItemCategory
        return db.query(ItemCategory).filter(ItemCategory.is_active == True).all()
    finally:
        db.close()

@router.post("/categories", response_model=CategoryResponse)
async def create_category(category: CategoryCreate, current_user: AdminUser = Depends(get_current_user)):
    """Crear categoría"""
    db = SessionLocal()
    try:
        from bot.database.models import ItemCategory
        db_cat = ItemCategory(
            name=category.name,
            icon=category.icon,
            is_active=category.is_active
        )
        db.add(db_cat)
        db.commit()
        db.refresh(db_cat)
        return db_cat
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


class ShopItemResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    image_url: Optional[str]
    price: int
    item_type: str
    discord_role_id: Optional[int]
    stock: int
    is_active: bool
    
    class Config:
        from_attributes = True


@router.get("/items", response_model=List[ShopItemResponse])
async def get_shop_items(
    active_only: bool = False,
    current_user: AdminUser = Depends(get_current_user)
):
    """Obtener todos los items de la tienda"""
    db = SessionLocal()
    try:
        query = db.query(ShopItem)
        if active_only:
            query = query.filter(ShopItem.is_active == True)
        
        items = query.order_by(ShopItem.price.asc()).all()
        return items
    finally:
        db.close()


@router.get("/stats")
async def get_shop_stats(current_user: AdminUser = Depends(get_current_user)):
    """Obtener estadísticas de la tienda"""
    db = SessionLocal()
    try:
        from sqlalchemy import func
        from bot.database.models import Purchase
        from bot.services.shop_service import ShopService
        
        total_purchases = db.query(func.count(Purchase.id)).scalar() or 0
        total_spent = db.query(func.sum(Purchase.price_paid)).scalar() or 0
        
        # Top item (simple query)
        stats = ShopService.get_shop_stats(db)
        
        return {
            "total_purchases": total_purchases,
            "total_spent": total_spent,
            "popular_item": stats.get('most_popular_item', 'N/A')
        }
    finally:
        db.close()

@router.get("/history")
async def get_purchase_history(current_user: AdminUser = Depends(get_current_user)):
    """Obtener historial de compras reciente"""
    db = SessionLocal()
    try:
        from bot.database.models import Purchase, User, ShopItem
        
        # Get last 50 purchases
        purchases = db.query(Purchase).join(User).join(ShopItem).order_by(
            Purchase.purchased_at.desc()
        ).limit(50).all()
        
        return [
            {
                "id": p.id,
                "user_name": p.user.username,
                "item_name": p.item.name,
                "price": p.price_paid,
                "date": p.purchased_at.isoformat()
            }
            for p in purchases
        ]
    finally:
        db.close()


@router.post("/items", response_model=ShopItemResponse)
async def create_shop_item(
    item: ShopItemCreate,
    current_user: AdminUser = Depends(get_current_user)
):
    """Crear nuevo item en la tienda"""
    db = SessionLocal()
    try:
        # Note: Need to update ShopService to accept category_id
        # For now, manually creating or updating service signature
        from bot.database.models import ShopItem
        
        db_item = ShopItem(
            name=item.name,
            price=item.price,
            item_type=item.item_type,
            description=item.description,
            stock=item.stock,
            image_url=item.image_url,
            is_active=item.is_active,
            category_id=item.category_id
        )
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


@router.put("/items/{item_id}", response_model=ShopItemResponse)
async def update_shop_item(
    item_id: int,
    item_update: ShopItemUpdate,
    current_user: AdminUser = Depends(get_current_user)
):
    """Actualizar item existente"""
    db = SessionLocal()
    try:
        item = db.query(ShopItem).filter(ShopItem.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item no encontrado")
        
        # Actualizar campos
        if item_update.name is not None:
            item.name = item_update.name
        if item_update.description is not None:
            item.description = item_update.description
        if item_update.image_url is not None:
            item.image_url = item_update.image_url
        if item_update.price is not None:
            item.price = item_update.price
        if item_update.item_type is not None:
            item.item_type = item_update.item_type
        if item_update.discord_role_id is not None:
            item.discord_role_id = item_update.discord_role_id
        if item_update.stock is not None:
            item.stock = item_update.stock
        if item_update.is_active is not None:
            item.is_active = item_update.is_active
        if item_update.category_id is not None:
            item.category_id = item_update.category_id if item_update.category_id != 0 else None
        
        db.commit()
        db.refresh(item)
        
        return item
    finally:
        db.close()


@router.delete("/items/{item_id}")
async def delete_shop_item(
    item_id: int,
    current_user: AdminUser = Depends(get_current_user)
):
    """Eliminar item de la tienda"""
    db = SessionLocal()
    try:
        item = db.query(ShopItem).filter(ShopItem.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item no encontrado")
        
        db.delete(item)
        db.commit()
        
        return {"message": "Item eliminado correctamente"}
    finally:
        db.close()


@router.post("/upload-image")
async def upload_item_image(
    file: UploadFile = File(...),
    current_user: AdminUser = Depends(get_current_user)
):
    """Subir imagen para un item"""
    # Validar tipo de archivo
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Tipo de archivo no permitido. Solo se permiten imágenes (JPEG, PNG, GIF, WebP)"
        )
    
    # Crear directorio si no existe
    upload_dir = "web/static/uploads/shop"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generar nombre único
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{uuid.uuid4()}.{file_extension}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # Guardar archivo
    try:
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)
        
        # Retornar URL relativa
        image_url = f"/static/uploads/shop/{unique_filename}"
        return {"image_url": image_url}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error subiendo imagen: {str(e)}")
