"""
Infrastructure data models for track sections, stations, and railway network
"""

from enum import Enum
from typing import List, Dict, Optional, Set
from pydantic import BaseModel, Field
from datetime import datetime


class SectionType(str, Enum):
    """Types of track sections"""
    SINGLE_LINE = "single_line"
    DOUBLE_LINE = "double_line"
    MULTIPLE_LINE = "multiple_line"
    JUNCTION = "junction"
    YARD = "yard"
    PLATFORM = "platform"


class SignalType(str, Enum):
    """Types of signaling systems"""
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    SEMI_AUTOMATIC = "semi_automatic"
    CENTRALIZED = "centralized"


class SectionStatus(str, Enum):
    """Current status of a track section"""
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    BLOCKED = "blocked"
    MAINTENANCE = "maintenance"
    RESERVED = "reserved"


class TrackSection(BaseModel):
    """Represents a track section in the railway network"""
    
    section_id: str = Field(..., description="Unique section identifier")
    section_name: str = Field(..., description="Human-readable section name")
    section_type: SectionType = Field(..., description="Type of track section")
    
    # Physical characteristics
    length_km: float = Field(..., description="Section length in kilometers")
    max_speed_limit: int = Field(default=100, description="Maximum speed limit in km/h")
    gradient: float = Field(default=0.0, description="Track gradient in percentage")
    curvature: float = Field(default=0.0, description="Track curvature factor")
    
    # Capacity and constraints
    max_trains: int = Field(default=1, description="Maximum trains that can occupy simultaneously")
    platform_count: int = Field(default=0, description="Number of platforms (if applicable)")
    electrified: bool = Field(default=True, description="Whether section is electrified")
    
    # Connectivity
    connected_sections: List[str] = Field(default_factory=list, description="Adjacent section IDs")
    entry_signals: List[str] = Field(default_factory=list, description="Entry signal IDs")
    exit_signals: List[str] = Field(default_factory=list, description="Exit signal IDs")
    
    # Current status
    current_status: SectionStatus = Field(default=SectionStatus.AVAILABLE)
    occupying_trains: List[str] = Field(default_factory=list, description="Currently occupying train IDs")
    reserved_for: Optional[str] = Field(None, description="Train ID for which section is reserved")
    
    # Operational parameters
    signal_type: SignalType = Field(default=SignalType.AUTOMATIC)
    maintenance_windows: List[Dict] = Field(default_factory=list, description="Scheduled maintenance periods")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Station(BaseModel):
    """Represents a railway station"""
    
    station_id: str = Field(..., description="Unique station identifier")
    station_name: str = Field(..., description="Station name")
    station_code: str = Field(..., description="Official station code")
    
    # Location and characteristics
    latitude: Optional[float] = Field(None, description="Station latitude")
    longitude: Optional[float] = Field(None, description="Station longitude")
    elevation: Optional[float] = Field(None, description="Station elevation in meters")
    
    # Infrastructure
    platform_sections: List[str] = Field(default_factory=list, description="Platform section IDs")
    yard_sections: List[str] = Field(default_factory=list, description="Yard section IDs")
    junction_sections: List[str] = Field(default_factory=list, description="Junction section IDs")
    
    # Operational capabilities
    passenger_station: bool = Field(default=True, description="Handles passenger trains")
    freight_station: bool = Field(default=False, description="Handles freight trains")
    maintenance_facility: bool = Field(default=False, description="Has maintenance facilities")
    
    # Current operations
    scheduled_arrivals: List[str] = Field(default_factory=list, description="Scheduled arriving train IDs")
    scheduled_departures: List[str] = Field(default_factory=list, description="Scheduled departing train IDs")


class Signal(BaseModel):
    """Represents a railway signal"""
    
    signal_id: str = Field(..., description="Unique signal identifier")
    signal_name: str = Field(..., description="Signal name/number")
    signal_type: SignalType = Field(..., description="Type of signal")
    
    # Location
    section_id: str = Field(..., description="Section where signal is located")
    kilometer_post: float = Field(..., description="Kilometer post location")
    
    # Signal aspects and states
    current_aspect: str = Field(default="red", description="Current signal aspect")
    controlled_sections: List[str] = Field(default_factory=list, description="Sections controlled by this signal")
    
    # Operational parameters
    automatic_operation: bool = Field(default=True, description="Whether signal operates automatically")
    override_capability: bool = Field(default=True, description="Can be manually overridden")


class RailwayNetwork(BaseModel):
    """Represents the complete railway network"""
    
    network_id: str = Field(..., description="Network identifier")
    network_name: str = Field(..., description="Network name")
    
    # Network components
    sections: Dict[str, TrackSection] = Field(default_factory=dict, description="All track sections")
    stations: Dict[str, Station] = Field(default_factory=dict, description="All stations")
    signals: Dict[str, Signal] = Field(default_factory=dict, description="All signals")
    
    # Network topology
    adjacency_matrix: Dict[str, List[str]] = Field(default_factory=dict, description="Section connectivity")
    distance_matrix: Dict[str, Dict[str, float]] = Field(default_factory=dict, description="Distances between sections")
    
    def add_section(self, section: TrackSection) -> None:
        """Add a track section to the network"""
        self.sections[section.section_id] = section
        if section.section_id not in self.adjacency_matrix:
            self.adjacency_matrix[section.section_id] = section.connected_sections
    
    def add_station(self, station: Station) -> None:
        """Add a station to the network"""
        self.stations[station.station_id] = station
    
    def add_signal(self, signal: Signal) -> None:
        """Add a signal to the network"""
        self.signals[signal.signal_id] = signal
    
    def get_route_sections(self, origin: str, destination: str) -> List[str]:
        """Get the sequence of sections for a route (simplified pathfinding)"""
        # This is a simplified implementation - in production, use proper pathfinding algorithms
        if origin == destination:
            return [origin]
        
        # For MVP, return direct connection if exists
        if origin in self.adjacency_matrix and destination in self.adjacency_matrix[origin]:
            return [origin, destination]
        
        # Otherwise, return empty list (to be enhanced with proper routing)
        return []
    
    def calculate_route_distance(self, sections: List[str]) -> float:
        """Calculate total distance for a route"""
        total_distance = 0.0
        for i in range(len(sections) - 1):
            current_section = sections[i]
            next_section = sections[i + 1]
            
            if (current_section in self.distance_matrix and 
                next_section in self.distance_matrix[current_section]):
                total_distance += self.distance_matrix[current_section][next_section]
            elif current_section in self.sections:
                # Fallback to section length
                total_distance += self.sections[current_section].length_km
        
        return total_distance
    
    def get_available_sections(self) -> List[str]:
        """Get list of currently available sections"""
        return [
            section_id for section_id, section in self.sections.items()
            if section.current_status == SectionStatus.AVAILABLE
        ]
    
    def check_section_capacity(self, section_id: str) -> bool:
        """Check if section has available capacity"""
        if section_id not in self.sections:
            return False
        
        section = self.sections[section_id]
        return len(section.occupying_trains) < section.max_trains
    
    def reserve_section(self, section_id: str, train_id: str) -> bool:
        """Reserve a section for a specific train"""
        if section_id not in self.sections:
            return False
        
        section = self.sections[section_id]
        if section.current_status == SectionStatus.AVAILABLE and section.reserved_for is None:
            section.reserved_for = train_id
            section.current_status = SectionStatus.RESERVED
            return True
        
        return False
    
    def occupy_section(self, section_id: str, train_id: str) -> bool:
        """Mark section as occupied by a train"""
        if section_id not in self.sections:
            return False
        
        section = self.sections[section_id]
        if (section.current_status in [SectionStatus.AVAILABLE, SectionStatus.RESERVED] and
            len(section.occupying_trains) < section.max_trains):
            
            section.occupying_trains.append(train_id)
            section.current_status = SectionStatus.OCCUPIED
            section.reserved_for = None
            return True
        
        return False
    
    def release_section(self, section_id: str, train_id: str) -> bool:
        """Release section from train occupation"""
        if section_id not in self.sections:
            return False
        
        section = self.sections[section_id]
        if train_id in section.occupying_trains:
            section.occupying_trains.remove(train_id)
            
            if not section.occupying_trains:
                section.current_status = SectionStatus.AVAILABLE
            
            return True
        
        return False


# Utility functions for network operations
def create_sample_network() -> RailwayNetwork:
    """Create a sample railway network for testing"""
    network = RailwayNetwork(
        network_id="sample_001",
        network_name="Sample Railway Network"
    )
    
    # Create sample sections
    sections_data = [
        {"id": "SEC_001", "name": "Main Line Section 1", "type": SectionType.DOUBLE_LINE, "length": 15.5},
        {"id": "SEC_002", "name": "Main Line Section 2", "type": SectionType.DOUBLE_LINE, "length": 12.3},
        {"id": "SEC_003", "name": "Junction A", "type": SectionType.JUNCTION, "length": 2.1},
        {"id": "SEC_004", "name": "Platform 1", "type": SectionType.PLATFORM, "length": 0.4},
        {"id": "SEC_005", "name": "Platform 2", "type": SectionType.PLATFORM, "length": 0.4},
    ]
    
    for section_data in sections_data:
        section = TrackSection(
            section_id=section_data["id"],
            section_name=section_data["name"],
            section_type=section_data["type"],
            length_km=section_data["length"]
        )
        network.add_section(section)
    
    # Set up connectivity
    network.adjacency_matrix = {
        "SEC_001": ["SEC_003"],
        "SEC_002": ["SEC_003"],
        "SEC_003": ["SEC_001", "SEC_002", "SEC_004", "SEC_005"],
        "SEC_004": ["SEC_003"],
        "SEC_005": ["SEC_003"]
    }
    
    # Set up distance matrix
    network.distance_matrix = {
        "SEC_001": {"SEC_003": 15.5},
        "SEC_002": {"SEC_003": 12.3},
        "SEC_003": {"SEC_001": 15.5, "SEC_002": 12.3, "SEC_004": 2.1, "SEC_005": 2.1},
        "SEC_004": {"SEC_003": 0.4},
        "SEC_005": {"SEC_003": 0.4}
    }
    
    return network
