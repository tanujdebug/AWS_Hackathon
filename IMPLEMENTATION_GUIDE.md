# Implementation Guide - Drone Swarm Earthquake Rescue System

## Quick Start (30 minutes)

### 1. Environment Setup
```bash
# Clone repository
git clone <repository-url>
cd AWS_Hackathon

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies for dashboard
cd dashboard
npm install
cd ..
```

### 2. Run the System
```bash
# Terminal 1: Start the API server
python src/api/main.py

# Terminal 2: Start the drone simulator
python src/simulation/drone_simulator.py

# Terminal 3: Start the dashboard
cd dashboard
npm start
```

### 3. Access the System
- **Dashboard:** http://localhost:3000
- **API Documentation:** http://localhost:8000/docs
- **API Health Check:** http://localhost:8000/health

---

## Detailed Implementation Steps

### Phase 1: Foundation Setup (Day 1)

#### 1.1 AWS Account Setup
```bash
# Install AWS CLI
pip install awscli

# Configure AWS credentials
aws configure

# Create S3 bucket for data storage
aws s3 mb s3://drone-rescue-data-$(date +%s)

# Create DynamoDB table
aws dynamodb create-table \
    --table-name drone-telemetry \
    --attribute-definitions \
        AttributeName=drone_id,AttributeType=S \
        AttributeName=timestamp,AttributeType=S \
    --key-schema \
        AttributeName=drone_id,KeyType=HASH \
        AttributeName=timestamp,KeyType=RANGE \
    --billing-mode PAY_PER_REQUEST
```

#### 1.2 Local Development Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/
```

#### 1.3 Data Schema Implementation
```python
# Example telemetry data structure
telemetry_example = {
    "timestamp_utc": "2025-01-06T12:00:00Z",
    "drone_id": "drone-001",
    "position": {"lat": 34.0522, "lon": -118.2437, "alt_m": 15.0},
    "speed_m_s": 2.5,
    "heading_deg": 45.0,
    "battery_pct": 85.0,
    "status": "searching",
    "detected_person": {
        "person_id": "victim-001",
        "confidence": 0.85,
        "injury_level": "severe",
        "age_est": 35,
        "vitals": {"hr": 65, "resp": 12, "spo2": 88}
    },
    "nearest_responder_id": "responder-01",
    "dist_to_nearest_responder_m": 250.0,
    "neighbor_beacons": [
        {"drone_id": "drone-002", "distance_m": 45.2, "last_seen": "2025-01-06T12:00:00Z"}
    ],
    "message_seq": 1
}
```

### Phase 2: Core Components (Day 1-2)

#### 2.1 Drone Simulator
```python
# Run the drone simulator
python src/simulation/drone_simulator.py

# The simulator will:
# - Generate 20 drones with random positions
# - Simulate telemetry every minute
# - Create victim detection events
# - Save data to drone_telemetry.json
```

#### 2.2 ML Model Training
```python
# Train the survival likelihood model
python src/ml/survival_model.py

# This will:
# - Generate synthetic training data
# - Train XGBoost model
# - Save model to survival_model.pkl
# - Display performance metrics
```

#### 2.3 Route Optimization
```python
# Test the route optimizer
python src/routing/route_optimizer.py

# This will:
# - Create sample responders and victims
# - Optimize routes using OR-Tools
# - Display route solutions
```

### Phase 3: Integration (Day 2)

#### 3.1 API Server
```python
# Start the FastAPI server
python src/api/main.py

# The API provides endpoints for:
# - POST /telemetry - Receive drone data
# - GET /routes - Get optimized routes
# - GET /victims - Get victim information
# - GET /status - System status
# - GET /dashboard/data - All dashboard data
```

#### 3.2 Real-time Data Flow
```python
# Example: Send telemetry data to API
import requests
import json

telemetry_data = {
    "timestamp_utc": "2025-01-06T12:00:00Z",
    "drone_id": "drone-001",
    "position": {"lat": 34.0522, "lon": -118.2437},
    "speed_m_s": 2.5,
    "heading_deg": 45.0,
    "battery_pct": 85.0,
    "status": "searching",
    "detected_person": {
        "person_id": "victim-001",
        "confidence": 0.85,
        "injury_level": "severe",
        "age_est": 35,
        "vitals": {"hr": 65, "resp": 12, "spo2": 88}
    },
    "nearest_responder_id": "responder-01",
    "dist_to_nearest_responder_m": 250.0,
    "neighbor_beacons": [],
    "message_seq": 1
}

response = requests.post("http://localhost:8000/telemetry", json=telemetry_data)
print(response.json())
```

### Phase 4: Dashboard (Day 2-3)

#### 4.1 React Dashboard Setup
```bash
cd dashboard
npm install
npm start
```

#### 4.2 Dashboard Features
- **Real-time Map:** Shows drone positions, victims, and routes
- **System Status:** Active drones, victims, responders
- **Victim Priority:** Ranked list of victims by survival likelihood
- **Route Information:** Optimized routes for responders

### Phase 5: AWS Integration (Day 2-3)

#### 5.1 AWS IoT Core Setup
```python
# Configure IoT Core for drone connectivity
import boto3

iot_client = boto3.client('iot')

# Create IoT thing type
iot_client.create_thing_type(
    thingTypeName='Drone',
    thingTypeDescription='Earthquake rescue drone'
)

# Create IoT policy
policy_document = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": "iot:Connect",
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": "iot:Publish",
            "Resource": "arn:aws:iot:*:*:topic/drone/telemetry"
        }
    ]
}
```

#### 5.2 Kinesis Data Streams
```python
# Create Kinesis stream
kinesis_client = boto3.client('kinesis')

kinesis_client.create_stream(
    StreamName='drone-telemetry-stream',
    ShardCount=1
)
```

#### 5.3 SageMaker Model Deployment
```python
# Deploy model to SageMaker endpoint
import sagemaker
from sagemaker.sklearn import SKLearn

# Create SageMaker session
sagemaker_session = sagemaker.Session()

# Deploy model
sklearn_model = SKLearn(
    model_data='s3://your-bucket/survival-model.tar.gz',
    role='SageMakerExecutionRole',
    entry_point='inference.py',
    framework_version='0.23-1',
    py_version='py3'
)

predictor = sklearn_model.deploy(
    instance_type='ml.t2.medium',
    initial_instance_count=1
)
```

### Phase 6: Testing & Validation (Day 3)

#### 6.1 End-to-End Testing
```python
# Test complete system flow
def test_end_to_end():
    # 1. Start drone simulator
    # 2. Send telemetry to API
    # 3. Verify ML predictions
    # 4. Check route optimization
    # 5. Validate dashboard updates
    pass
```

#### 6.2 Performance Testing
```python
# Load testing with multiple drones
import concurrent.futures
import requests

def send_telemetry(drone_id):
    # Send telemetry for one drone
    pass

# Test with 100 drones
with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
    futures = [executor.submit(send_telemetry, f"drone-{i}") for i in range(100)]
    results = [future.result() for future in futures]
```

### Phase 7: Demo Preparation (Day 3)

#### 7.1 Demo Script
1. **Setup (2 minutes):**
   - Start all services
   - Verify system health
   - Load demo data

2. **Drone Simulation (3 minutes):**
   - Show 20+ drones on map
   - Demonstrate victim detection
   - Show real-time telemetry

3. **ML Integration (2 minutes):**
   - Show survival likelihood predictions
   - Explain model features
   - Demonstrate accuracy

4. **Route Optimization (3 minutes):**
   - Show dynamic route planning
   - Demonstrate multi-responder coordination
   - Show route updates

5. **Dashboard Features (2 minutes):**
   - Real-time updates
   - Priority victim list
   - System status metrics

#### 7.2 Demo Data Preparation
```python
# Create demo scenario
demo_scenario = {
    "earthquake_center": [34.0522, -118.2437],
    "num_drones": 20,
    "num_victims": 15,
    "num_responders": 5,
    "simulation_duration": 30  # minutes
}
```

---

## Troubleshooting

### Common Issues:

#### 1. API Connection Errors
```bash
# Check if API is running
curl http://localhost:8000/health

# Check API logs
python src/api/main.py
```

#### 2. Dashboard Not Loading
```bash
# Check if dashboard is running
cd dashboard
npm start

# Check browser console for errors
```

#### 3. ML Model Errors
```bash
# Retrain model
python src/ml/survival_model.py

# Check model file exists
ls -la survival_model.pkl
```

#### 4. Route Optimization Issues
```bash
# Check OR-Tools installation
python -c "import ortools"

# Test with sample data
python src/routing/route_optimizer.py
```

### Performance Optimization:

#### 1. API Performance
```python
# Add caching
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_prediction(features_hash):
    return model.predict(features)
```

#### 2. Database Optimization
```python
# Use connection pooling
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    'sqlite:///drone_data.db',
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20
)
```

#### 3. Frontend Optimization
```javascript
// Implement virtual scrolling for large datasets
import { FixedSizeList as List } from 'react-window';

const VirtualizedList = ({ items }) => (
  <List
    height={600}
    itemCount={items.length}
    itemSize={50}
  >
    {({ index, style }) => (
      <div style={style}>
        {items[index]}
      </div>
    )}
  </List>
);
```

---

## Deployment Options

### Option 1: Local Development
- All services run locally
- SQLite database
- No AWS dependencies
- Good for development and testing

### Option 2: AWS Services
- IoT Core for drone connectivity
- Kinesis for data streaming
- Lambda for processing
- DynamoDB for storage
- SageMaker for ML
- Amplify for hosting

### Option 3: Hybrid Approach
- Local development with AWS services
- Gradual migration to cloud
- Fallback to local services if needed

---

## Success Criteria

### Technical Requirements:
- [ ] 20+ drones simulated
- [ ] Real-time telemetry processing
- [ ] ML survival predictions
- [ ] Dynamic route optimization
- [ ] Live dashboard updates

### Performance Requirements:
- [ ] < 2 second API response time
- [ ] > 85% ML model accuracy
- [ ] Support 100+ concurrent drones
- [ ] Real-time dashboard updates

### Demo Requirements:
- [ ] 5-minute live demonstration
- [ ] All components working together
- [ ] Clear explanation of value proposition
- [ ] Professional presentation

---

## Next Steps

1. **Immediate (Day 1):**
   - Set up development environment
   - Implement core components
   - Test individual modules

2. **Short-term (Day 2):**
   - Integrate components
   - Implement real-time features
   - Test end-to-end flow

3. **Final (Day 3):**
   - Polish and optimization
   - Demo preparation
   - Presentation practice

4. **Future Enhancements:**
   - Advanced ML models
   - Multi-objective optimization
   - Mobile applications
   - Production deployment
