"""
API endpoints for event management
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from bot.database.connection import SessionLocal
from bot.database.models import Event, EventParticipant, User
from web.auth import get_current_user, AdminUser
from sqlalchemy import and_, or_

router = APIRouter(prefix="/events", tags=["Events"])


class EventBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    reward_points: int = Field(..., ge=0)
    min_activity: int = Field(default=10, ge=0)
    requires_presence_start: bool = True
    requires_presence_end: bool = True
    is_active: bool = True


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    reward_points: Optional[int] = None
    min_activity: Optional[int] = None
    requires_presence_start: Optional[bool] = None
    requires_presence_end: Optional[bool] = None
    is_active: Optional[bool] = None


class EventResponse(EventBase):
    id: int
    created_at: datetime
    participant_count: int = 0
    
    class Config:
        from_attributes = True


class ParticipantResponse(BaseModel):
    id: int
    user_id: int
    username: str
    joined_at: datetime
    was_present_start: bool
    was_present_end: bool
    activity_count: int
    reward_claimed: bool
    
    class Config:
        from_attributes = True


@router.get("/", response_model=List[EventResponse])
async def get_events(
    active_only: bool = Query(False),
    current_user: AdminUser = Depends(get_current_user)
):
    """Get all events"""
    db = SessionLocal()
    try:
        query = db.query(Event)
        
        if active_only:
            query = query.filter(Event.is_active == True)
        
        events = query.order_by(Event.start_time.desc()).all()
        
        # Add participant count
        result = []
        for event in events:
            event_dict = {
                "id": event.id,
                "name": event.name,
                "description": event.description,
                "start_time": event.start_time,
                "end_time": event.end_time,
                "reward_points": event.reward_points,
                "min_activity": event.min_activity,
                "requires_presence_start": event.requires_presence_start,
                "requires_presence_end": event.requires_presence_end,
                "is_active": event.is_active,
                "created_at": event.created_at,
                "participant_count": len(event.participants)
            }
            result.append(event_dict)
        
        return result
    finally:
        db.close()


@router.post("/", response_model=EventResponse)
async def create_event(
    event: EventCreate,
    current_user: AdminUser = Depends(get_current_user)
):
    """Create a new event"""
    db = SessionLocal()
    try:
        # Validate dates
        if event.end_time <= event.start_time:
            raise HTTPException(status_code=400, detail="End time must be after start time")
        
        db_event = Event(
            name=event.name,
            description=event.description,
            start_time=event.start_time,
            end_time=event.end_time,
            reward_points=event.reward_points,
            min_activity=event.min_activity,
            requires_presence_start=event.requires_presence_start,
            requires_presence_end=event.requires_presence_end,
            is_active=event.is_active
        )
        
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        
        return {
            **db_event.__dict__,
            "participant_count": 0
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        db.close()


@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: int,
    current_user: AdminUser = Depends(get_current_user)
):
    """Get event by ID"""
    db = SessionLocal()
    try:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        return {
            **event.__dict__,
            "participant_count": len(event.participants)
        }
    finally:
        db.close()


@router.put("/{event_id}", response_model=EventResponse)
async def update_event(
    event_id: int,
    event_update: EventUpdate,
    current_user: AdminUser = Depends(get_current_user)
):
    """Update an event"""
    db = SessionLocal()
    try:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Update fields
        if event_update.name is not None:
            event.name = event_update.name
        if event_update.description is not None:
            event.description = event_update.description
        if event_update.start_time is not None:
            event.start_time = event_update.start_time
        if event_update.end_time is not None:
            event.end_time = event_update.end_time
        if event_update.reward_points is not None:
            event.reward_points = event_update.reward_points
        if event_update.min_activity is not None:
            event.min_activity = event_update.min_activity
        if event_update.requires_presence_start is not None:
            event.requires_presence_start = event_update.requires_presence_start
        if event_update.requires_presence_end is not None:
            event.requires_presence_end = event_update.requires_presence_end
        if event_update.is_active is not None:
            event.is_active = event_update.is_active
        
        # Validate dates
        if event.end_time <= event.start_time:
            raise HTTPException(status_code=400, detail="End time must be after start time")
        
        db.commit()
        db.refresh(event)
        
        return {
            **event.__dict__,
            "participant_count": len(event.participants)
        }
    finally:
        db.close()


@router.delete("/{event_id}")
async def delete_event(
    event_id: int,
    current_user: AdminUser = Depends(get_current_user)
):
    """Delete an event"""
    db = SessionLocal()
    try:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        db.delete(event)
        db.commit()
        
        return {"message": "Event deleted successfully"}
    finally:
        db.close()


@router.get("/{event_id}/participants", response_model=List[ParticipantResponse])
async def get_event_participants(
    event_id: int,
    current_user: AdminUser = Depends(get_current_user)
):
    """Get participants for an event"""
    db = SessionLocal()
    try:
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        participants = db.query(EventParticipant).filter(
            EventParticipant.event_id == event_id
        ).all()
        
        result = []
        for p in participants:
            result.append({
                "id": p.id,
                "user_id": p.user_id,
                "username": p.user.username,
                "joined_at": p.joined_at,
                "was_present_start": p.was_present_start,
                "was_present_end": p.was_present_end,
                "activity_count": p.activity_count,
                "reward_claimed": p.reward_claimed
            })
        
        return result
    finally:
        db.close()


@router.post("/{event_id}/distribute-rewards")
async def distribute_rewards(
    event_id: int,
    current_user: AdminUser = Depends(get_current_user)
):
    """Manually distribute rewards for an event"""
    db = SessionLocal()
    try:
        from bot.services.event_service import EventService
        
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        # Distribute rewards
        rewarded_count = EventService.distribute_event_rewards(db, event)
        
        return {
            "message": f"Rewards distributed to {rewarded_count} participants",
            "rewarded_count": rewarded_count
        }
    finally:
        db.close()
