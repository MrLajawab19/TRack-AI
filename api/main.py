"""
FastAPI main application for AI-Powered Train Traffic Control System
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from typing import List, Dict, Optional
from datetime import datetime
import uvicorn

from models.train import Train, TrainMovement, TrainConflict, TrainType, TrainPriority
from models.infrastructure import RailwayNetwork, TrackSection, create_sample_network
from optimization.scheduler import TrainScheduler, RealTimeOptimizer
from api.irctc_service import irctc_service

# Initialize FastAPI app
app = FastAPI(
    title="AI-Powered Train Traffic Control System",
    description="Intelligent decision-support system for railway traffic optimization",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables (in production, use proper database and state management)
railway_network = create_sample_network()
scheduler = TrainScheduler(railway_network)
real_time_optimizer = RealTimeOptimizer(scheduler)
active_trains: List[Train] = []
current_schedule: Optional[Dict] = None

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main dashboard"""
    with open("index.html", "r") as f:
        return HTMLResponse(content=f.read())


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


# Train Management Endpoints

@app.post("/api/trains", response_model=Dict)
async def create_train(train: Train):
    """Create a new train in the system"""
    try:
        # Check if train already exists
        existing_train = next((t for t in active_trains if t.train_id == train.train_id), None)
        if existing_train:
            raise HTTPException(status_code=400, detail="Train already exists")
        
        # Validate route
        if not train.route_sections:
            route = railway_network.get_route_sections(train.origin_station, train.destination_station)
            train.route_sections = route
        
        active_trains.append(train)
        
        return {
            "status": "success",
            "message": f"Train {train.train_id} created successfully",
            "train_id": train.train_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/trains", response_model=List[Train])
async def get_trains():
    """Get all active trains"""
    return active_trains


@app.get("/api/trains/{train_id}", response_model=Train)
async def get_train(train_id: str):
    """Get specific train by ID"""
    train = next((t for t in active_trains if t.train_id == train_id), None)
    if not train:
        raise HTTPException(status_code=404, detail="Train not found")
    return train


@app.put("/api/trains/{train_id}", response_model=Dict)
async def update_train(train_id: str, train_update: Train):
    """Update train information"""
    try:
        train_index = next((i for i, t in enumerate(active_trains) if t.train_id == train_id), None)
        if train_index is None:
            raise HTTPException(status_code=404, detail="Train not found")
        
        active_trains[train_index] = train_update
        
        return {
            "status": "success",
            "message": f"Train {train_id} updated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/trains/{train_id}", response_model=Dict)
async def delete_train(train_id: str):
    """Remove train from system"""
    try:
        train_index = next((i for i, t in enumerate(active_trains) if t.train_id == train_id), None)
        if train_index is None:
            raise HTTPException(status_code=404, detail="Train not found")
        
        removed_train = active_trains.pop(train_index)
        
        return {
            "status": "success",
            "message": f"Train {train_id} removed successfully",
            "removed_train": removed_train.train_number
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# IRCTC API Integration Endpoints

@app.get("/api/train/{train_no}", response_model=Dict)
async def get_train_schedule_irctc(train_no: str):
    """
    Get real-time train schedule from IRCTC API
    
    Args:
        train_no: Train number (e.g., "12936")
        
    Returns:
        Train schedule information including stations, timings, and current status
    """
    try:
        schedule_data = await irctc_service.get_train_schedule(train_no)
        return schedule_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching train schedule: {str(e)}")


@app.post("/api/trains/bulk-schedule", response_model=Dict)
async def get_multiple_train_schedules(train_numbers: List[str]):
    """
    Get schedules for multiple trains concurrently
    
    Args:
        train_numbers: List of train numbers
        
    Returns:
        Dictionary mapping train numbers to their schedule data
    """
    try:
        if len(train_numbers) > 10:  # Limit to prevent abuse
            raise HTTPException(status_code=400, detail="Maximum 10 trains allowed per request")
        
        schedules = await irctc_service.get_multiple_trains(train_numbers)
        return {
            "success": True,
            "count": len(schedules),
            "schedules": schedules,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching train schedules: {str(e)}")


@app.delete("/api/train-cache", response_model=Dict)
async def clear_train_cache():
    """Clear the train data cache"""
    try:
        irctc_service.clear_cache()
        return {
            "status": "success",
            "message": "Train data cache cleared successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/train-cache/stats", response_model=Dict)
async def get_cache_stats():
    """Get cache statistics"""
    try:
        stats = irctc_service.get_cache_stats()
        return {
            "status": "success",
            "cache_stats": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Scheduling and Optimization Endpoints

@app.post("/api/optimize", response_model=Dict)
async def optimize_schedule(time_horizon: int = 24):
    """Optimize train schedule"""
    try:
        global current_schedule
        
        if not active_trains:
            raise HTTPException(status_code=400, detail="No trains to optimize")
        
        # Run optimization
        current_schedule = scheduler.optimize_schedule(active_trains, time_horizon)
        
        return {
            "status": "success",
            "message": "Schedule optimized successfully",
            "schedule": current_schedule
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/schedule", response_model=Dict)
async def get_current_schedule():
    """Get current optimized schedule"""
    if not current_schedule:
        return {
            "status": "no_schedule",
            "message": "No schedule available. Run optimization first."
        }
    
    return {
        "status": "success",
        "schedule": current_schedule,
        "last_updated": datetime.now().isoformat()
    }


@app.post("/api/conflicts/detect", response_model=List[TrainConflict])
async def detect_conflicts():
    """Detect conflicts between trains"""
    try:
        conflicts = scheduler.detect_conflicts(active_trains)
        return conflicts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/conflicts/resolve", response_model=List[Dict])
async def resolve_conflicts():
    """Get conflict resolution recommendations"""
    try:
        conflicts = scheduler.detect_conflicts(active_trains)
        resolutions = scheduler.resolve_conflicts(conflicts, active_trains)
        return resolutions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Real-time Updates

@app.post("/api/realtime/update", response_model=Dict)
async def update_realtime(disruptions: List[Dict] = None):
    """Update schedule with real-time information"""
    try:
        global current_schedule
        
        result = real_time_optimizer.update_schedule(active_trains, disruptions)
        current_schedule = result['schedule']
        
        return {
            "status": "success",
            "message": "Real-time update completed",
            "result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Infrastructure Endpoints

@app.get("/api/network", response_model=Dict)
async def get_network_info():
    """Get railway network information"""
    return {
        "network_id": railway_network.network_id,
        "network_name": railway_network.network_name,
        "sections_count": len(railway_network.sections),
        "stations_count": len(railway_network.stations),
        "signals_count": len(railway_network.signals)
    }


@app.get("/api/sections", response_model=List[Dict])
async def get_sections():
    """Get all track sections"""
    sections_list = []
    for section_id, section in railway_network.sections.items():
        sections_list.append({
            "section_id": section.section_id,
            "section_name": section.section_name,
            "section_type": section.section_type.value,
            "length_km": section.length_km,
            "current_status": section.current_status.value,
            "occupying_trains": section.occupying_trains,
            "max_trains": section.max_trains
        })
    return sections_list


@app.get("/api/sections/{section_id}/status", response_model=Dict)
async def get_section_status(section_id: str):
    """Get specific section status"""
    if section_id not in railway_network.sections:
        raise HTTPException(status_code=404, detail="Section not found")
    
    section = railway_network.sections[section_id]
    return {
        "section_id": section.section_id,
        "current_status": section.current_status.value,
        "occupying_trains": section.occupying_trains,
        "reserved_for": section.reserved_for,
        "capacity_available": railway_network.check_section_capacity(section_id)
    }


# Analytics and Metrics

@app.get("/api/metrics", response_model=Dict)
async def get_system_metrics():
    """Get system performance metrics"""
    try:
        total_trains = len(active_trains)
        running_trains = len([t for t in active_trains if t.current_status.value == "running"])
        delayed_trains = len([t for t in active_trains if t.current_status.value == "delayed"])
        
        available_sections = len(railway_network.get_available_sections())
        total_sections = len(railway_network.sections)
        
        metrics = {
            "trains": {
                "total": total_trains,
                "running": running_trains,
                "delayed": delayed_trains,
                "on_time_percentage": ((total_trains - delayed_trains) / max(total_trains, 1)) * 100
            },
            "infrastructure": {
                "total_sections": total_sections,
                "available_sections": available_sections,
                "utilization_percentage": ((total_sections - available_sections) / max(total_sections, 1)) * 100
            },
            "schedule": {
                "last_optimization": current_schedule.get('metrics', {}) if current_schedule else {},
                "has_active_schedule": current_schedule is not None
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Simulation Endpoints

@app.post("/api/simulate", response_model=Dict)
async def run_simulation(scenario: Dict):
    """Run what-if simulation"""
    try:
        # This is a simplified simulation for MVP
        # In production, this would be more sophisticated
        
        simulation_trains = active_trains.copy()
        
        # Apply scenario modifications
        if "train_delays" in scenario:
            for delay_info in scenario["train_delays"]:
                train_id = delay_info.get("train_id")
                delay_minutes = delay_info.get("delay_minutes", 0)
                
                for train in simulation_trains:
                    if train.train_id == train_id:
                        train.scheduled_departure += timedelta(minutes=delay_minutes)
                        break
        
        # Run optimization on modified scenario
        simulation_result = scheduler.optimize_schedule(simulation_trains)
        
        return {
            "status": "success",
            "message": "Simulation completed",
            "scenario": scenario,
            "result": simulation_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Sample data creation for testing
@app.post("/api/sample-data", response_model=Dict)
async def create_sample_data():
    """Create sample trains for testing"""
    try:
        global active_trains
        
        # Clear existing trains
        active_trains = []
        
        # Create sample trains
        sample_trains = [
            Train(
                train_id="T001",
                train_number="12345",
                train_name="Express 1",
                train_type=TrainType.EXPRESS,
                priority=TrainPriority.HIGH,
                origin_station="SEC_001",
                destination_station="SEC_004",
                scheduled_departure=datetime.now(),
                scheduled_arrival=datetime.now() + timedelta(hours=2),
                route_sections=["SEC_001", "SEC_003", "SEC_004"]
            ),
            Train(
                train_id="T002",
                train_number="67890",
                train_name="Local 1",
                train_type=TrainType.LOCAL,
                priority=TrainPriority.MEDIUM,
                origin_station="SEC_002",
                destination_station="SEC_005",
                scheduled_departure=datetime.now() + timedelta(minutes=30),
                scheduled_arrival=datetime.now() + timedelta(hours=2, minutes=30),
                route_sections=["SEC_002", "SEC_003", "SEC_005"]
            ),
            Train(
                train_id="T003",
                train_number="11111",
                train_name="Freight 1",
                train_type=TrainType.FREIGHT,
                priority=TrainPriority.LOW,
                origin_station="SEC_001",
                destination_station="SEC_002",
                scheduled_departure=datetime.now() + timedelta(hours=1),
                scheduled_arrival=datetime.now() + timedelta(hours=4),
                route_sections=["SEC_001", "SEC_003", "SEC_002"]
            )
        ]
        
        active_trains.extend(sample_trains)
        
        return {
            "status": "success",
            "message": f"Created {len(sample_trains)} sample trains",
            "trains": [t.train_id for t in sample_trains]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
