# AI-Powered Precise Train Traffic Control System

## SIH 2025 Problem Statement 25022

### Project Overview
An intelligent decision-support system that assists section controllers in making optimized, real-time decisions for train precedence and crossings to maximize section throughput and minimize overall train travel time.

### MVP Goals (Internal Hackathon - Sept 24, 2025)
- ✅ 25% Backend functionality working
- Core optimization algorithms
- Basic conflict detection and resolution
- Simple simulation engine
- REST API framework
- Basic web interface

### Technology Stack
- **Backend**: Python with FastAPI
- **Frontend**: HTML/CSS/JavaScript (React components)
- **Database**: SQLite (MVP), PostgreSQL (Production)
- **Optimization**: Google OR-Tools
- **AI/ML**: scikit-learn, numpy, pandas

### System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Interface │    │   REST API      │    │  Optimization   │
│   (Controller   │◄──►│   (FastAPI)     │◄──►│   Engine        │
│    Dashboard)   │    │                 │    │  (OR-Tools)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Database      │
                       │   (SQLite)      │
                       │                 │
                       └─────────────────┘
```

### Core Components

1. **Data Models**
   - Train entities (express, local, freight, maintenance)
   - Track sections and infrastructure
   - Schedule and timing constraints
   - Priority and safety rules

2. **Optimization Engine**
   - Constraint programming for scheduling
   - Conflict detection algorithms
   - Real-time re-optimization
   - Performance metrics calculation

3. **Simulation Engine**
   - What-if scenario analysis
   - Throughput calculations
   - Delay impact assessment

4. **API Layer**
   - Train management endpoints
   - Schedule optimization endpoints
   - Simulation and analytics endpoints

### Installation & Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py

# Access the web interface
http://localhost:8000
```

### Development Progress

- [ ] Core data models
- [ ] Basic optimization algorithm
- [ ] Conflict detection logic
- [ ] REST API framework
- [ ] Web interface
- [ ] Simulation engine
- [ ] Performance metrics

### Key Features for MVP

1. **Train Schedule Optimization**
   - Priority-based scheduling
   - Conflict-free timetable generation
   - Real-time adjustments

2. **Decision Support Interface**
   - Controller dashboard
   - Recommendation system
   - Override capabilities

3. **Performance Analytics**
   - Throughput metrics
   - Delay analysis
   - Utilization reports

### Future Enhancements

- Integration with existing railway systems
- Advanced AI/ML algorithms
- Real-time data streaming
- Mobile interface
- Advanced analytics and reporting
