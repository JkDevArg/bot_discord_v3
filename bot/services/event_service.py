"""
Servicio de gestión de eventos
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from bot.database.models import Event, EventParticipant, User
from bot.utils.logger import bot_logger
from datetime import datetime


class EventService:
    """Servicio para gestionar eventos"""
    
    @staticmethod
    def create_event(
        db: Session,
        name: str,
        start_time: datetime,
        end_time: datetime,
        created_by: int,
        description: str = "",
        reward_points: int = 0,
        min_activity: int = 10
    ) -> Event:
        """
        Crear un nuevo evento
        
        Args:
            db: Sesión de base de datos
            name: Nombre del evento
            start_time: Fecha y hora de inicio
            end_time: Fecha y hora de fin
            created_by: Discord ID del admin creador
            description: Descripción del evento
            reward_points: Puntos de recompensa
            min_activity: Actividad mínima requerida
        
        Returns:
            Evento creado
        """
        if end_time <= start_time:
            raise ValueError("La hora de fin debe ser posterior a la de inicio")
        
        event = Event(
            name=name,
            description=description,
            start_time=start_time,
            end_time=end_time,
            reward_points=reward_points,
            min_activity=min_activity,
            is_active=True,
            is_finished=False,
            created_by=created_by
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        
        bot_logger.info(f"Evento creado: {name} ({start_time} - {end_time})")
        return event
    
    @staticmethod
    def get_event_by_id(db: Session, event_id: int) -> Event:
        """Obtener evento por ID"""
        return db.query(Event).filter(Event.id == event_id).first()
    
    @staticmethod
    def get_active_events(db: Session) -> list[Event]:
        """Obtener eventos activos"""
        return db.query(Event).filter(
            Event.is_active == True,
            Event.is_finished == False
        ).order_by(Event.start_time).all()
    
    @staticmethod
    def get_current_events(db: Session) -> list[Event]:
        """Obtener eventos que están ocurriendo ahora"""
        now = datetime.utcnow()
        return db.query(Event).filter(
            Event.is_active == True,
            Event.is_finished == False,
            Event.start_time <= now,
            Event.end_time >= now
        ).all()
    
    @staticmethod
    def join_event(db: Session, event: Event, user: User) -> tuple[bool, str]:
        """
        Unir usuario a un evento
        
        Args:
            db: Sesión de base de datos
            event: Evento
            user: Usuario
        
        Returns:
            Tupla (éxito, mensaje)
        """
        # Verificar si el evento está activo
        if not event.is_active or event.is_finished:
            return False, "Este evento no está disponible"
        
        # Verificar si ya está participando
        existing = db.query(EventParticipant).filter(
            and_(
                EventParticipant.event_id == event.id,
                EventParticipant.user_id == user.id
            )
        ).first()
        
        if existing:
            return False, "Ya estás participando en este evento"
        
        # Verificar si el evento ya comenzó
        now = datetime.utcnow()
        was_present_at_start = now >= event.start_time
        
        # Crear participación
        participant = EventParticipant(
            event_id=event.id,
            user_id=user.id,
            was_present_at_start=was_present_at_start,
            was_present_at_end=False,
            activity_count=0,
            is_eligible=False,
            reward_received=False
        )
        db.add(participant)
        db.commit()
        
        bot_logger.info(f"Usuario {user.username} se unió al evento {event.name}")
        return True, f"¡Te uniste al evento {event.name}!"
    
    @staticmethod
    def record_activity(db: Session, event: Event, user: User) -> bool:
        """
        Registrar actividad de usuario durante evento
        
        Args:
            db: Sesión de base de datos
            event: Evento
            user: Usuario
        
        Returns:
            True si se registró la actividad
        """
        participant = db.query(EventParticipant).filter(
            and_(
                EventParticipant.event_id == event.id,
                EventParticipant.user_id == user.id
            )
        ).first()
        
        if not participant:
            return False
        
        participant.activity_count += 1
        db.commit()
        
        return True
    
    @staticmethod
    def check_participant_at_end(db: Session, event: Event, user: User) -> bool:
        """
        Marcar que el usuario estuvo presente al final del evento
        
        Args:
            db: Sesión de base de datos
            event: Evento
            user: Usuario
        
        Returns:
            True si se marcó correctamente
        """
        participant = db.query(EventParticipant).filter(
            and_(
                EventParticipant.event_id == event.id,
                EventParticipant.user_id == user.id
            )
        ).first()
        
        if not participant:
            return False
        
        participant.was_present_at_end = True
        
        # Verificar elegibilidad
        participant.is_eligible = (
            participant.was_present_at_start and
            participant.was_present_at_end and
            participant.activity_count >= event.min_activity
        )
        
        db.commit()
        return True
    
    @staticmethod
    def finish_event(db: Session, event: Event) -> tuple[int, list[User]]:
        """
        Finalizar evento y distribuir recompensas
        
        Args:
            db: Sesión de base de datos
            event: Evento
        
        Returns:
            Tupla (cantidad_elegibles, lista_de_ganadores)
        """
        # Marcar evento como finalizado
        event.is_finished = True
        event.updated_at = datetime.utcnow()
        
        # Obtener participantes elegibles
        eligible_participants = db.query(EventParticipant).filter(
            and_(
                EventParticipant.event_id == event.id,
                EventParticipant.is_eligible == True,
                EventParticipant.reward_received == False
            )
        ).all()
        
        eligible_count = len(eligible_participants)
        
        # Distribuir recompensas
        winners = []
        for participant in eligible_participants:
            user = db.query(User).filter(User.id == participant.user_id).first()
            if user:
                user.points += event.reward_points
                user.total_points_earned += event.reward_points
                user.updated_at = datetime.utcnow()
                
                participant.reward_received = True
                winners.append(user)
        
        db.commit()
        
        bot_logger.info(
            f"Evento finalizado: {event.name} - {eligible_count} participantes elegibles"
        )
        
        return eligible_count, winners
    
    @staticmethod
    def get_event_participants(db: Session, event: Event) -> list[EventParticipant]:
        """
        Obtener participantes de un evento
        
        Args:
            db: Sesión de base de datos
            event: Evento
        
        Returns:
            Lista de participantes
        """
        return db.query(EventParticipant).filter(
            EventParticipant.event_id == event.id
        ).all()
    
    @staticmethod
    def get_event_stats(db: Session, event: Event) -> dict:
        """
        Obtener estadísticas de un evento
        
        Args:
            db: Sesión de base de datos
            event: Evento
        
        Returns:
            Diccionario con estadísticas
        """
        from sqlalchemy import func
        
        total_participants = db.query(func.count(EventParticipant.id)).filter(
            EventParticipant.event_id == event.id
        ).scalar()
        
        eligible_participants = db.query(func.count(EventParticipant.id)).filter(
            and_(
                EventParticipant.event_id == event.id,
                EventParticipant.is_eligible == True
            )
        ).scalar()
        
        avg_activity = db.query(func.avg(EventParticipant.activity_count)).filter(
            EventParticipant.event_id == event.id
        ).scalar() or 0
        
        return {
            'total_participants': total_participants,
            'eligible_participants': eligible_participants,
            'avg_activity': round(avg_activity, 2),
            'is_active': event.is_active,
            'is_finished': event.is_finished
        }
