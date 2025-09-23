"""
Train data models for the AI-Powered Train Traffic Control System
"""

from enum import Enum
from datetime import datetime, timedelta
from typing import Optional, List
from pydantic import BaseModel, Field


class TrainType(str, Enum):
    """Types of trains in the railway system"""
    EXPRESS = "express"
    LOCAL = "local"
    FREIGHT = "freight"
    MAINTENANCE = "maintenance"
    SPECIAL = "special"


class TrainPriority(int, Enum):
    """Priority levels for trains (higher number = higher priority)"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4
    EMERGENCY = 5


class TrainStatus(str, Enum):
    """Current status of a train"""
    SCHEDULED = "scheduled"
    RUNNING = "running"
    DELAYED = "delayed"
    HALTED = "halted"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Train(BaseModel):
    """Core train entity model"""
    
    train_id: str = Field(..., description="Unique train identifier")
    train_number: str = Field(..., description="Official train number")
    train_name: str = Field(..., description="Train name")
    train_type: TrainType = Field(..., description="Type of train")
    priority: TrainPriority = Field(default=TrainPriority.MEDIUM, description="Train priority level")
    
    # Schedule information
    origin_station: str = Field(..., description="Starting station")
    destination_station: str = Field(..., description="Final destination")
    scheduled_departure: datetime = Field(..., description="Scheduled departure time")
    scheduled_arrival: datetime = Field(..., description="Scheduled arrival time")
    
    # Current status
    current_status: TrainStatus = Field(default=TrainStatus.SCHEDULED)
    current_location: Optional[str] = Field(None, description="Current section/station")
    actual_departure: Optional[datetime] = Field(None, description="Actual departure time")
    estimated_arrival: Optional[datetime] = Field(None, description="Estimated arrival time")
    
    # Operational parameters
    max_speed: int = Field(default=100, description="Maximum speed in km/h")
    length: int = Field(default=200, description="Train length in meters")
    weight: int = Field(default=1000, description="Train weight in tons")
    
    # Route information
    route_sections: List[str] = Field(default_factory=list, description="List of track sections in route")
    platform_requirements: Optional[str] = Field(None, description="Special platform requirements")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TrainMovement(BaseModel):
    """Represents a train movement between sections"""
    
    movement_id: str = Field(..., description="Unique movement identifier")
    train_id: str = Field(..., description="Associated train ID")
    from_section: str = Field(..., description="Source section")
    to_section: str = Field(..., description="Destination section")
    
    scheduled_start: datetime = Field(..., description="Scheduled start time")
    scheduled_end: datetime = Field(..., description="Scheduled end time")
    actual_start: Optional[datetime] = Field(None, description="Actual start time")
    actual_end: Optional[datetime] = Field(None, description="Actual end time")
    
    estimated_duration: timedelta = Field(..., description="Estimated travel time")
    priority_score: float = Field(default=0.0, description="Calculated priority score")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            timedelta: lambda v: v.total_seconds()
        }


class TrainConflict(BaseModel):
    """Represents a potential conflict between trains"""
    
    conflict_id: str = Field(..., description="Unique conflict identifier")
    train_ids: List[str] = Field(..., description="Conflicting train IDs")
    section_id: str = Field(..., description="Conflicted section")
    conflict_type: str = Field(..., description="Type of conflict")
    
    conflict_start: datetime = Field(..., description="When conflict begins")
    conflict_end: datetime = Field(..., description="When conflict ends")
    severity: int = Field(default=1, description="Conflict severity (1-5)")
    
    resolution_strategy: Optional[str] = Field(None, description="Proposed resolution")
    resolved: bool = Field(default=False, description="Whether conflict is resolved")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Utility functions for train operations
def calculate_priority_score(train: Train) -> float:
    """Calculate dynamic priority score based on train attributes"""
    base_score = float(train.priority.value)
    
    # Adjust for train type
    type_multipliers = {
        TrainType.EMERGENCY: 2.0,
        TrainType.EXPRESS: 1.5,
        TrainType.LOCAL: 1.0,
        TrainType.FREIGHT: 0.8,
        TrainType.MAINTENANCE: 0.5
    }
    
    type_multiplier = type_multipliers.get(train.train_type, 1.0)
    
    # Adjust for delays (if any)
    delay_penalty = 0.0
    if train.actual_departure and train.scheduled_departure:
        delay = train.actual_departure - train.scheduled_departure
        if delay.total_seconds() > 0:
            delay_penalty = min(delay.total_seconds() / 3600, 2.0)  # Max 2 hour penalty
    
    return base_score * type_multiplier + delay_penalty


def estimate_travel_time(train: Train, from_section: str, to_section: str, distance_km: float) -> timedelta:
    """Estimate travel time between sections"""
    # Simple calculation based on average speed (can be enhanced with more sophisticated models)
    average_speed = train.max_speed * 0.8  # Assume 80% of max speed
    travel_hours = distance_km / average_speed
    
    # Add buffer time based on train type
    buffer_minutes = {
        TrainType.EXPRESS: 2,
        TrainType.LOCAL: 5,
        TrainType.FREIGHT: 10,
        TrainType.MAINTENANCE: 15,
        TrainType.SPECIAL: 5
    }.get(train.train_type, 5)
    
    total_minutes = (travel_hours * 60) + buffer_minutes
    return timedelta(minutes=total_minutes)
