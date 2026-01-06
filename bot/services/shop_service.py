"""
Servicio de gestión de tienda
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from bot.database.models import ShopItem, Purchase, User
from bot.utils.logger import bot_logger
from bot.utils.validators import validate_item_type
from datetime import datetime


class ShopService:
    """Servicio para gestionar la tienda"""
    
    @staticmethod
    def create_item(
        db: Session,
        name: str,
        price: int,
        item_type: str,
        description: str = "",
        discord_role_id: int = None,
        stock: int = -1
    ) -> ShopItem:
        """
        Crear un nuevo item en la tienda
        
        Args:
            db: Sesión de base de datos
            name: Nombre del item
            price: Precio en puntos
            item_type: Tipo de item (role, benefit, custom)
            description: Descripción
            discord_role_id: ID del rol de Discord (si es tipo role)
            stock: Stock disponible (-1 = ilimitado)
        
        Returns:
            Item creado
        """
        if not validate_item_type(item_type):
            raise ValueError(f"Tipo de item inválido: {item_type}")
        
        if price <= 0:
            raise ValueError("El precio debe ser mayor a 0")
        
        item = ShopItem(
            name=name,
            description=description,
            price=price,
            item_type=item_type,
            discord_role_id=discord_role_id,
            stock=stock,
            is_active=True
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        
        bot_logger.info(f"Item creado en tienda: {name} - {price} pts")
        return item
    
    @staticmethod
    def get_item_by_id(db: Session, item_id: int) -> ShopItem:
        """Obtener item por ID"""
        return db.query(ShopItem).filter(ShopItem.id == item_id).first()
    
    @staticmethod
    def get_active_items(db: Session) -> list[ShopItem]:
        """Obtener items activos ordenados por precio"""
        return db.query(ShopItem).filter(
            ShopItem.is_active == True
        ).order_by(ShopItem.price).all()
    
    @staticmethod
    def update_item(db: Session, item: ShopItem, **kwargs) -> ShopItem:
        """
        Actualizar item
        
        Args:
            db: Sesión de base de datos
            item: Item a actualizar
            **kwargs: Campos a actualizar
        
        Returns:
            Item actualizado
        """
        for key, value in kwargs.items():
            if hasattr(item, key):
                setattr(item, key, value)
        
        item.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(item)
        
        bot_logger.info(f"Item actualizado: {item.name}")
        return item
    
    @staticmethod
    def delete_item(db: Session, item: ShopItem) -> bool:
        """
        Eliminar item (soft delete)
        
        Args:
            db: Sesión de base de datos
            item: Item a eliminar
        
        Returns:
            True si fue exitoso
        """
        item.is_active = False
        item.updated_at = datetime.utcnow()
        db.commit()
        
        bot_logger.info(f"Item desactivado: {item.name}")
        return True
    
    @staticmethod
    def can_purchase(db: Session, user: User, item: ShopItem) -> tuple[bool, str]:
        """
        Verificar si el usuario puede comprar el item
        
        Args:
            db: Sesión de base de datos
            user: Usuario
            item: Item
        
        Returns:
            Tupla (puede_comprar, razón)
        """
        # Verificar si el item está activo
        if not item.is_active:
            return False, "Este item no está disponible"
        
        # Verificar puntos suficientes
        if user.points < item.price:
            needed = item.price - user.points
            return False, f"No tienes suficientes puntos. Te faltan {needed} pts"
        
        # Verificar stock
        if item.stock == 0:
            return False, "Este item está agotado"
        
        # Verificar si ya compró este item (solo para roles)
        if item.item_type == 'role':
            existing_purchase = db.query(Purchase).filter(
                and_(Purchase.user_id == user.id, Purchase.item_id == item.id)
            ).first()
            if existing_purchase:
                return False, "Ya compraste este item"
        
        return True, ""
    
    @staticmethod
    def purchase_item(db: Session, user: User, item: ShopItem) -> tuple[bool, str, Purchase]:
        """
        Procesar compra de un item
        
        Args:
            db: Sesión de base de datos
            user: Usuario
            item: Item
        
        Returns:
            Tupla (éxito, mensaje, purchase)
        """
        # Verificar si puede comprar
        can_buy, reason = ShopService.can_purchase(db, user, item)
        if not can_buy:
            return False, reason, None
        
        # Deducir puntos
        user.points -= item.price
        user.updated_at = datetime.utcnow()
        
        # Reducir stock si no es ilimitado
        if item.stock > 0:
            item.stock -= 1
            item.updated_at = datetime.utcnow()
        
        # Crear registro de compra
        purchase = Purchase(
            user_id=user.id,
            item_id=item.id,
            price_paid=item.price
        )
        db.add(purchase)
        db.commit()
        db.refresh(purchase)
        
        bot_logger.info(
            f"Compra realizada: {user.username} compró {item.name} por {item.price} pts"
        )
        
        return True, f"¡Compraste {item.name}!", purchase
    
    @staticmethod
    def get_user_purchases(db: Session, user: User) -> list[Purchase]:
        """
        Obtener historial de compras de un usuario
        
        Args:
            db: Sesión de base de datos
            user: Usuario
        
        Returns:
            Lista de compras
        """
        return db.query(Purchase).filter(
            Purchase.user_id == user.id
        ).order_by(Purchase.purchased_at.desc()).all()
    
    @staticmethod
    def get_recent_purchases(db: Session, limit: int = 10) -> list[Purchase]:
        """
        Obtener compras recientes
        
        Args:
            db: Sesión de base de datos
            limit: Cantidad de compras a retornar
        
        Returns:
            Lista de compras
        """
        return db.query(Purchase).order_by(
            Purchase.purchased_at.desc()
        ).limit(limit).all()
    
    @staticmethod
    def get_shop_stats(db: Session) -> dict:
        """
        Obtener estadísticas de la tienda
        
        Args:
            db: Sesión de base de datos
        
        Returns:
            Diccionario con estadísticas
        """
        from sqlalchemy import func
        
        total_items = db.query(func.count(ShopItem.id)).filter(
            ShopItem.is_active == True
        ).scalar()
        
        total_purchases = db.query(func.count(Purchase.id)).scalar()
        
        total_points_spent = db.query(func.sum(Purchase.price_paid)).scalar() or 0
        
        most_popular = db.query(
            ShopItem.name,
            func.count(Purchase.id).label('purchase_count')
        ).join(Purchase).group_by(ShopItem.id).order_by(
            func.count(Purchase.id).desc()
        ).first()
        
        return {
            'total_items': total_items,
            'total_purchases': total_purchases,
            'total_points_spent': total_points_spent,
            'most_popular_item': most_popular[0] if most_popular else None,
            'most_popular_count': most_popular[1] if most_popular else 0
        }
