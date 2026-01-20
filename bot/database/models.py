"""
Modelos de base de datos usando SQLAlchemy ORM
"""
from sqlalchemy import (
    Column, Integer, String, BigInteger, Float, Boolean,
    DateTime, Text, ForeignKey, Index, CheckConstraint, func
)
from sqlalchemy.orm import relationship
from bot.database.connection import Base
from datetime import datetime


class User(Base):
    """Usuario de Discord con puntos y estadísticas"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    discord_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=False)
    discriminator = Column(String(10))
    avatar_url = Column(String(255))  # URL del avatar de Discord
    points = Column(Integer, default=0, nullable=False)
    total_points_earned = Column(Integer, default=0, nullable=False)
    total_messages = Column(Integer, default=0, nullable=False)
    
    # Sistema de niveles y experiencia
    level = Column(Integer, default=1, nullable=False)
    exp = Column(Integer, default=0, nullable=False)
    total_exp_earned = Column(Integer, default=0, nullable=False)
    
    last_activity = Column(DateTime, default=func.now(), nullable=False)
    joined_at = Column(DateTime, default=func.now(), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relaciones
    user_roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")
    purchases = relationship("Purchase", back_populates="user")
    event_participations = relationship("EventParticipant", back_populates="user")
    activity_logs = relationship("ActivityLog", back_populates="user", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint('points >= 0', name='check_points_positive'),
        Index('idx_user_points', 'points'),
        Index('idx_user_last_activity', 'last_activity'),
    )
    
    def __repr__(self):
        return f"<User {self.username} ({self.discord_id}) - Lvl {self.level} - {self.points} pts>"


class Role(Base):
    """Configuración de roles del servidor"""
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    discord_role_id = Column(BigInteger, unique=True, nullable=False, index=True)
    points_required = Column(Integer, default=0, nullable=False)
    color = Column(String(7), default="#FFFFFF")  # Hex color
    benefits = Column(Text)
    auto_assign = Column(Boolean, default=True)
    is_purchasable = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relaciones
    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint('points_required >= 0', name='check_points_required_positive'),
        Index('idx_role_points', 'points_required'),
    )
    
    def __repr__(self):
        return f"<Role {self.name} - {self.points_required} pts>"


class UserRole(Base):
    """Relación muchos-a-muchos entre usuarios y roles"""
    __tablename__ = "user_roles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    assigned_at = Column(DateTime, default=func.now())
    
    # Relaciones
    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")
    
    __table_args__ = (
        Index('idx_user_role', 'user_id', 'role_id', unique=True),
    )
    
    def __repr__(self):
        return f"<UserRole user_id={self.user_id} role_id={self.role_id}>"


class ItemCategory(Base):
    """Categorías de items de la tienda"""
    __tablename__ = "item_categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    icon = Column(String(50))  # Emoji o clase de icono
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relaciones
    items = relationship("ShopItem", back_populates="category")

    def __repr__(self):
        return f"<Category {self.name}>"


class ShopItem(Base):
    """Items disponibles en la tienda"""
    __tablename__ = "shop_items"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey("item_categories.id"), nullable=True)  # Nullable para compatibilidad inicial
    name = Column(String(100), nullable=False)
    description = Column(Text)
    image_url = Column(String(500))  # URL de la imagen del item
    price = Column(Integer, nullable=False)
    item_type = Column(String(50), nullable=False)  # role, benefit, custom
    discord_role_id = Column(BigInteger, nullable=True)  # Si es tipo role
    stock = Column(Integer, default=-1)  # -1 = ilimitado
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relaciones
    category = relationship("ItemCategory", back_populates="items")
    purchases = relationship("Purchase", back_populates="item")
    
    __table_args__ = (
        CheckConstraint('price > 0', name='check_price_positive'),
        Index('idx_shop_active', 'is_active'),
        Index('idx_shop_category', 'category_id'),
    )
    
    def __repr__(self):
        return f"<ShopItem {self.name} - {self.price} pts>"


class Purchase(Base):
    """Historial de compras"""
    __tablename__ = "purchases"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    item_id = Column(Integer, ForeignKey("shop_items.id"), nullable=False)
    price_paid = Column(Integer, nullable=False)
    purchased_at = Column(DateTime, default=func.now())
    
    # Relaciones
    user = relationship("User", back_populates="purchases")
    item = relationship("ShopItem", back_populates="purchases")
    
    __table_args__ = (
        Index('idx_purchase_user', 'user_id'),
        Index('idx_purchase_date', 'purchased_at'),
    )
    
    def __repr__(self):
        return f"<Purchase user_id={self.user_id} item_id={self.item_id}>"


class Event(Base):
    """Eventos del servidor"""
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    reward_points = Column(Integer, default=0)
    min_activity = Column(Integer, default=10)  # Mensajes mínimos
    is_active = Column(Boolean, default=True)
    is_finished = Column(Boolean, default=False)
    created_by = Column(BigInteger, nullable=False)  # Discord ID del admin
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relaciones
    participants = relationship("EventParticipant", back_populates="event", cascade="all, delete-orphan")
    
    __table_args__ = (
        CheckConstraint('end_time > start_time', name='check_event_times'),
        Index('idx_event_times', 'start_time', 'end_time'),
    )
    
    def __repr__(self):
        return f"<Event {self.name} - {self.start_time}>"


class EventParticipant(Base):
    """Participantes de eventos con validación"""
    __tablename__ = "event_participants"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    joined_at = Column(DateTime, default=func.now())
    was_present_at_start = Column(Boolean, default=False)
    was_present_at_end = Column(Boolean, default=False)
    activity_count = Column(Integer, default=0)  # Mensajes durante evento
    is_eligible = Column(Boolean, default=False)  # Cumple requisitos
    reward_received = Column(Boolean, default=False)
    
    # Relaciones
    event = relationship("Event", back_populates="participants")
    user = relationship("User", back_populates="event_participations")
    
    __table_args__ = (
        Index('idx_event_participant', 'event_id', 'user_id', unique=True),
    )
    
    def __repr__(self):
        return f"<EventParticipant event_id={self.event_id} user_id={self.user_id}>"


class AnnouncementConfig(Base):
    """Configuración de canales de anuncios"""
    __tablename__ = "announcement_config"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    announcement_type = Column(String(50), nullable=False, unique=True)  # level_up, purchase, event
    channel_id = Column(BigInteger, nullable=False)
    is_enabled = Column(Boolean, default=True)
    message_template = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<AnnouncementConfig {self.announcement_type}>"


class AdminUser(Base):
    """Usuarios con permisos administrativos para el panel web"""
    __tablename__ = "admin_users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    discord_id = Column(BigInteger, unique=True, nullable=True)  # Opcional
    mfa_secret = Column(String(32), nullable=True)
    mfa_enabled = Column(Boolean, default=False)
    recovery_codes = Column(Text, nullable=True)  # JSON array de códigos
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relaciones
    audit_logs = relationship("AuditLog", back_populates="admin")
    
    def __repr__(self):
        return f"<AdminUser {self.username}>"


class AuditLog(Base):
    """Registro de acciones administrativas"""
    __tablename__ = "audit_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(Integer, ForeignKey("admin_users.id"), nullable=False)
    action = Column(String(100), nullable=False)
    target_type = Column(String(50))  # user, role, shop_item, event
    target_id = Column(Integer)
    details = Column(Text)  # JSON con detalles
    ip_address = Column(String(45))
    created_at = Column(DateTime, default=func.now())
    
    # Relaciones
    admin = relationship("AdminUser", back_populates="audit_logs")
    
    __table_args__ = (
        Index('idx_audit_admin', 'admin_id'),
        Index('idx_audit_date', 'created_at'),
    )
    
    def __repr__(self):
        return f"<AuditLog {self.action} by admin_id={self.admin_id}>"


class ActivityLog(Base):
    """Registro de actividad de usuarios (para anti-spam y cooldowns)"""
    __tablename__ = "activity_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    activity_type = Column(String(50), nullable=False)  # message, command, etc
    channel_id = Column(BigInteger)
    points_awarded = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    
    # Relaciones
    user = relationship("User", back_populates="activity_logs")
    
    __table_args__ = (
        Index('idx_activity_user_date', 'user_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<ActivityLog user_id={self.user_id} type={self.activity_type}>"


class BackupLog(Base):
    """Registro de backups realizados"""
    __tablename__ = "backup_log"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    backup_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger)  # Bytes
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_backup_date', 'created_at'),
    )
    
    def __repr__(self):
        return f"<BackupLog {self.backup_path} - {'OK' if self.success else 'FAIL'}>"


# ============================================================================
# NUEVOS MODELOS - FUNCIONALIDADES AVANZADAS
# ============================================================================

class DailyStats(Base):
    """Estadísticas diarias para gráficos de actividad"""
    __tablename__ = "daily_stats"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False, unique=True, index=True)
    active_users = Column(Integer, default=0, nullable=False)
    total_messages = Column(Integer, default=0, nullable=False)
    points_awarded = Column(Integer, default=0, nullable=False)
    new_users = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_daily_stats_date', 'date'),
    )
    
    def __repr__(self):
        return f"<DailyStats {self.date.strftime('%Y-%m-%d')} - {self.active_users} users>"


class DailyReward(Base):
    """Sistema de recompensas diarias con streaks"""
    __tablename__ = "daily_rewards"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    last_claim = Column(DateTime, nullable=False)
    streak_days = Column(Integer, default=1, nullable=False)
    total_claims = Column(Integer, default=1, nullable=False)
    best_streak = Column(Integer, default=1, nullable=False)
    
    # Relación
    user = relationship("User", backref="daily_reward")
    
    __table_args__ = (
        Index('idx_daily_reward_user', 'user_id', unique=True),
        Index('idx_daily_reward_last_claim', 'last_claim'),
    )
    
    def __repr__(self):
        return f"<DailyReward user_id={self.user_id} streak={self.streak_days}>"


class LeaderboardHistory(Base):
    """Historial de leaderboards semanales y mensuales"""
    __tablename__ = "leaderboard_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    period_type = Column(String(20), nullable=False)  # weekly, monthly
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    rank = Column(Integer, nullable=False)
    points = Column(Integer, nullable=False)
    level = Column(Integer, nullable=False)
    reward_given = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relación
    user = relationship("User", backref="leaderboard_entries")
    
    __table_args__ = (
        Index('idx_leaderboard_period', 'period_type', 'period_start', 'period_end'),
        Index('idx_leaderboard_rank', 'rank'),
    )
    
    def __repr__(self):
        return f"<LeaderboardHistory {self.period_type} rank={self.rank} user_id={self.user_id}>"


class ModerationConfig(Base):
    """Configuración de auto-moderación"""
    __tablename__ = "moderation_config"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(BigInteger, nullable=False, unique=True)
    
    # Configuración de spam
    spam_enabled = Column(Boolean, default=True)
    spam_threshold = Column(Integer, default=5)  # mensajes
    spam_timeframe = Column(Integer, default=5)  # segundos
    spam_mute_duration = Column(Integer, default=300)  # segundos
    
    # Configuración de filtro de palabras
    filter_enabled = Column(Boolean, default=True)
    filter_action = Column(String(20), default="delete")  # delete, mute, warn
    
    # Configuración general
    log_channel_id = Column(BigInteger, nullable=True)
    mute_role_id = Column(BigInteger, nullable=True)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<ModerationConfig guild={self.guild_id}>"


class FilteredWord(Base):
    """Palabras filtradas para auto-moderación"""
    __tablename__ = "filtered_words"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    word = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    severity = Column(String(20), default="medium")  # low, medium, high
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_filtered_word', 'word'),
        Index('idx_filtered_active', 'is_active'),
    )
    
    def __repr__(self):
        return f"<FilteredWord '{self.word}' severity={self.severity}>"


class ModerationLog(Base):
    """Registro de acciones de auto-moderación"""
    __tablename__ = "moderation_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, nullable=False)
    username = Column(String(100))
    action = Column(String(50), nullable=False)  # mute, delete, warn, kick
    reason = Column(Text)
    auto_moderated = Column(Boolean, default=True)
    message_content = Column(Text, nullable=True)
    channel_id = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, default=func.now())
    
    __table_args__ = (
        Index('idx_moderation_user', 'user_id'),
        Index('idx_moderation_date', 'created_at'),
        Index('idx_moderation_action', 'action'),
    )
    
    def __repr__(self):
        return f"<ModerationLog {self.action} user={self.username}>"
