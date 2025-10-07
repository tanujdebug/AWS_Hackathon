# Drone Swarm Earthquake Rescue System

## Project Overview
An autonomous drone swarm system for earthquake disaster response that prioritizes survivors, optimizes rescue routes, and coordinates search patterns in real-time.

## System Architecture

### Core Components
1. **Drone Telemetry System** - Real-time data collection from drone swarm
2. **Survival Likelihood ML Model** - AI-powered victim prioritization
3. **Dynamic Routing Engine** - Optimal rescue path planning
4. **Coordination Layer** - Drone swarm communication and search optimization
5. **Real-time Dashboard** - Emergency responder interface

### AWS Services Used
- **AWS IoT Core** - Secure drone connectivity
- **Amazon Kinesis** - Real-time data streaming
- **AWS Lambda** - Serverless data processing
- **Amazon DynamoDB** - Real-time state storage
- **Amazon S3** - Data lake for historical telemetry
- **Amazon SageMaker** - ML model training and inference
- **AWS Fargate** - Routing optimization service
- **Amazon Location Service** - Geospatial operations
- **AWS Amplify** - Dashboard hosting

## Team Structure (5 Members)

### Role 1: Team Lead & Integration Engineer
**Responsibilities:**
- Overall architecture and project coordination
- AWS account setup and service configuration
- Component integration and end-to-end testing
- Final presentation and demo preparation

**Key Deliverables:**
- AWS infrastructure setup
- Integration testing framework
- System architecture documentation
- Demo presentation

### Role 2: Drone Simulation & Data Engineer
**Responsibilities:**
- Mock drone telemetry generator
- Data schema design and validation
- AWS IoT Core integration
- Data pipeline monitoring

**Key Deliverables:**
- Drone simulator with 20+ drones
- Telemetry data schema
- IoT Core device provisioning
- Real-time data streaming

### Role 3: ML Engineer & Data Scientist
**Responsibilities:**
- Survival likelihood model development
- Feature engineering and model training
- SageMaker endpoint deployment
- Model performance monitoring

**Key Deliverables:**
- Trained survival prediction model
- Feature engineering pipeline
- Real-time inference endpoint
- Model evaluation metrics

### Role 4: Routing & Optimization Engineer
**Responsibilities:**
- Dynamic routing algorithm implementation
- OR-Tools integration for VRP optimization
- Real-time route updates
- Multi-responder coordination

**Key Deliverables:**
- Route optimization service
- Dynamic replanning logic
- API endpoints for route queries
- Performance optimization

### Role 5: Frontend & UI Engineer
**Responsibilities:**
- Real-time dashboard development
- Mobile responder app
- Map visualization with Leaflet
- User experience optimization

**Key Deliverables:**
- React dashboard with live updates
- Mobile PWA for responders
- Interactive map with drone positions
- Priority victim visualization

## Data Schema

### Drone Telemetry (per minute per drone)
```json
{
  "timestamp_utc": "2025-01-06T12:00:00Z",
  "drone_id": "drone-017",
  "position": {
    "lat": 34.0491,
    "lon": -118.2498,
    "alt_m": 12.0
  },
  "status": "searching",
  "battery_pct": 62.5,
  "detected_person": {
    "person_id": "victim-123",
    "confidence": 0.85,
    "injury_level": "severe",
    "vitals": {"hr": 45, "resp": 8, "spo2": 78}
  },
  "nearest_responder": {
    "responder_id": "responder-05",
    "distance_m": 45.3
  },
  "neighbor_beacons": [
    {"drone_id": "drone-018", "distance_m": 15.2, "last_seen": "2025-01-06T12:00:00Z"}
  ]
}
```

## Implementation Timeline

### Day 1: Foundation & Parallel Development
- **Morning:** Team setup, AWS accounts, project structure
- **Afternoon:** Each role begins independent development
- **Evening:** Integration checkpoint and data flow validation

### Day 2: Integration & Real-time Features
- **Morning:** Connect components via APIs
- **Afternoon:** Implement real-time updates and coordination
- **Evening:** End-to-end testing and bug fixes

### Day 3: Polish & Production Readiness
- **Morning:** Performance optimization and monitoring
- **Afternoon:** UI polish and demo preparation
- **Evening:** Final testing and presentation prep

## Technical Complexity Levels

### MVP Features (Must Have)
- 10-20 simulated drones with telemetry
- Basic survival likelihood scoring
- Simple routing for single responder
- Real-time dashboard with map

### Advanced Features (Should Have)
- Multi-responder coordination
- Dynamic route replanning
- Drone swarm coordination
- Mobile responder app

### Stretch Features (Nice to Have)
- Sensor fusion (thermal, audio, visual)
- Battery-aware routing
- Human-in-the-loop verification
- Advanced ML ensemble models

## Success Metrics
- **Response Time:** < 2 minutes from detection to route update
- **Accuracy:** > 85% survival likelihood prediction
- **Scalability:** Support 100+ drones simultaneously
- **Reliability:** 99.9% uptime during critical operations

## Getting Started
1. Clone this repository
2. Set up AWS accounts and configure credentials
3. Install dependencies: `pip install -r requirements.txt`
4. Run the drone simulator: `python src/simulation/drone_simulator.py`
5. Start the dashboard: `npm start` in the `dashboard/` directory

## Project Structure
```
├── src/
│   ├── simulation/          # Drone simulation and mock data
│   ├── ml/                  # ML models and training
│   ├── routing/             # Route optimization algorithms
│   ├── api/                 # Backend API services
│   └── utils/               # Shared utilities
├── dashboard/               # React dashboard
├── mobile/                  # Mobile responder app
├── docs/                    # Documentation
└── tests/                   # Test suites
```