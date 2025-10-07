"""
FastAPI Backend for Drone Swarm Earthquake Rescue System
Provides REST API endpoints for telemetry, ML inference, and routing
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import json
import asyncio
from datetime import datetime, timezone
import uvicorn

# Import our modules
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.survival_model import SurvivalLikelihoodModel
from routing.route_optimizer import RouteOptimizer, Victim, Responder
from simulation.drone_simulator import DroneTelemetry

# Initialize FastAPI app
app = FastAPI(
    title="Drone Swarm Earthquake Rescue API",
    description="Real-time API for earthquake rescue coordination",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
survival_model = SurvivalLikelihoodModel()
route_optimizer = RouteOptimizer()
telemetry_data = []
victims_data = {}
responders_data = {}

# Pydantic models for API
class TelemetryRequest(BaseModel):
    timestamp_utc: str
    drone_id: str
    position: Dict[str, float]
    speed_m_s: float
    heading_deg: float
    battery_pct: float
    status: str
    detected_person: Optional[Dict] = None
    nearest_responder_id: Optional[str] = None
    dist_to_nearest_responder_m: float
    neighbor_beacons: List[Dict] = []
    message_seq: int

class VictimRequest(BaseModel):
    person_id: str
    lat: float
    lon: float
    injury_level: str
    age_est: int
    vitals: Dict[str, int]
    detection_confidence: float
    time_detected: str

class ResponderRequest(BaseModel):
    responder_id: str
    lat: float
    lon: float
    capacity: int
    status: str

class RouteResponse(BaseModel):
    responder_id: str
    route: List[str]
    total_distance: float
    estimated_time: float
    victims_served: List[str]

class SystemStatusResponse(BaseModel):
    total_victims: int
    available_responders: int
    average_survival_likelihood: float
    system_load: float
    active_drones: int

# Initialize ML model
@app.on_event("startup")
async def startup_event():
    """Initialize the ML model on startup"""
    try:
        # Try to load existing model
        survival_model.load_model('survival_model.pkl')
        print("Loaded existing survival model")
    except:
        # Create a simple model for demo
        print("Creating simple survival model...")
        from sklearn.ensemble import RandomForestClassifier
        import numpy as np
        
        # Create simple training data
        np.random.seed(42)
        X = np.random.rand(100, 5)  # 5 features
        y = np.random.randint(0, 2, 100)  # Binary classification
        
        # Train simple model
        survival_model.model = RandomForestClassifier(n_estimators=10, random_state=42)
        survival_model.model.fit(X, y)
        survival_model.is_trained = True
        survival_model.feature_columns = ['feature_1', 'feature_2', 'feature_3', 'feature_4', 'feature_5']
        print("Simple survival model created")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Drone Swarm Earthquake Rescue API",
        "status": "operational",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model_loaded": survival_model.is_trained
    }

@app.post("/telemetry")
async def receive_telemetry(telemetry: TelemetryRequest):
    """Receive drone telemetry data"""
    try:
        # Store telemetry data
        telemetry_dict = telemetry.dict()
        telemetry_dict['received_at'] = datetime.now(timezone.utc).isoformat()
        telemetry_data.append(telemetry_dict)
        
        # Process detected person if any
        if telemetry.detected_person:
            await process_detected_person(telemetry.detected_person, telemetry.position)
        
        return {
            "status": "success",
            "message": "Telemetry received",
            "drone_id": telemetry.drone_id,
            "timestamp": telemetry.timestamp_utc
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing telemetry: {str(e)}")

async def process_detected_person(person_data: Dict, drone_position: Dict):
    """Process detected person and calculate survival likelihood"""
    try:
        # Calculate survival likelihood using simple model
        # Create simple features for demo
        import numpy as np
        np.random.seed(hash(person_data['person_id']) % 1000)
        features = np.random.rand(1, 5)  # 5 random features
        
        if survival_model.is_trained:
            survival_likelihood = survival_model.model.predict_proba(features)[0][1]
        else:
            # Fallback to simple calculation
            injury_level = person_data.get('injury_level', 'minor')
            injury_scores = {'none': 0.9, 'minor': 0.7, 'severe': 0.4, 'unconscious': 0.2}
            survival_likelihood = injury_scores.get(injury_level, 0.5)
        
        # Create victim object
        victim = Victim(
            id=person_data['person_id'],
            lat=drone_position['lat'],
            lon=drone_position['lon'],
            survival_likelihood=survival_likelihood,
            injury_level=person_data['injury_level'],
            time_detected=datetime.now(),
            priority_score=0
        )
        
        # Add to route optimizer
        route_optimizer.add_victim(victim)
        victims_data[victim.id] = victim
        
        print(f"Processed victim {victim.id} with survival likelihood {survival_likelihood:.3f}")
        
    except Exception as e:
        print(f"Error processing detected person: {str(e)}")

@app.post("/responders")
async def add_responder(responder: ResponderRequest):
    """Add or update responder information"""
    try:
        responder_obj = Responder(
            id=responder.responder_id,
            lat=responder.lat,
            lon=responder.lon,
            capacity=responder.capacity,
            status=responder.status,
            current_route=[]
        )
        
        route_optimizer.add_responder(responder_obj)
        responders_data[responder.responder_id] = responder_obj
        
        return {
            "status": "success",
            "message": "Responder added/updated",
            "responder_id": responder.responder_id
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding responder: {str(e)}")

@app.get("/routes")
async def get_optimized_routes():
    """Get optimized routes for all responders"""
    try:
        solutions = route_optimizer.optimize_routes()
        
        routes = []
        for solution in solutions:
            routes.append(RouteResponse(
                responder_id=solution.responder_id,
                route=solution.route,
                total_distance=solution.total_distance,
                estimated_time=solution.estimated_time,
                victims_served=solution.victims_served
            ))
        
        return {
            "status": "success",
            "routes": routes,
            "total_routes": len(routes)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error optimizing routes: {str(e)}")

@app.get("/victims")
async def get_victims():
    """Get all detected victims with priority scores"""
    try:
        victims_list = []
        for victim in victims_data.values():
            victims_list.append({
                "id": victim.id,
                "lat": victim.lat,
                "lon": victim.lon,
                "survival_likelihood": victim.survival_likelihood,
                "injury_level": victim.injury_level,
                "time_detected": victim.time_detected.isoformat(),
                "priority_score": victim.priority_score
            })
        
        # Sort by priority score
        victims_list.sort(key=lambda x: x['priority_score'], reverse=True)
        
        return {
            "status": "success",
            "victims": victims_list,
            "total_victims": len(victims_list)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting victims: {str(e)}")

@app.get("/status")
async def get_system_status():
    """Get overall system status"""
    try:
        status = route_optimizer.get_system_status()
        
        # Add additional metrics
        active_drones = len(set(t['drone_id'] for t in telemetry_data[-100:]))  # Last 100 records
        
        return SystemStatusResponse(
            total_victims=status['total_victims'],
            available_responders=status['available_responders'],
            average_survival_likelihood=status['average_survival_likelihood'],
            system_load=status['system_load'],
            active_drones=active_drones
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting system status: {str(e)}")

@app.get("/telemetry/latest")
async def get_latest_telemetry(limit: int = 100):
    """Get latest telemetry data"""
    try:
        latest_data = telemetry_data[-limit:] if telemetry_data else []
        
        return {
            "status": "success",
            "telemetry": latest_data,
            "count": len(latest_data)
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting telemetry: {str(e)}")

@app.post("/routes/update")
async def update_routes():
    """Trigger route update (useful for dynamic replanning)"""
    try:
        solutions = route_optimizer.optimize_routes()
        
        routes = []
        for solution in solutions:
            routes.append({
                "responder_id": solution.responder_id,
                "route": solution.route,
                "total_distance": solution.total_distance,
                "estimated_time": solution.estimated_time,
                "victims_served": solution.victims_served
            })
        
        return {
            "status": "success",
            "message": "Routes updated",
            "routes": routes
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating routes: {str(e)}")

@app.get("/dashboard/data")
async def get_dashboard_data():
    """Get all data needed for dashboard"""
    try:
        # Get system status
        status = route_optimizer.get_system_status()
        
        # Get latest telemetry
        latest_telemetry = telemetry_data[-50:] if telemetry_data else []
        
        # Get victims
        victims_list = []
        for victim in victims_data.values():
            victims_list.append({
                "id": victim.id,
                "lat": victim.lat,
                "lon": victim.lon,
                "survival_likelihood": victim.survival_likelihood,
                "injury_level": victim.injury_level,
                "time_detected": victim.time_detected.isoformat(),
                "priority_score": victim.priority_score
            })
        
        # Get routes
        solutions = route_optimizer.optimize_routes()
        routes = []
        for solution in solutions:
            routes.append({
                "responder_id": solution.responder_id,
                "route": solution.route,
                "total_distance": solution.total_distance,
                "estimated_time": solution.estimated_time,
                "victims_served": solution.victims_served
            })
        
        return {
            "status": "success",
            "system_status": status,
            "telemetry": latest_telemetry,
            "victims": victims_list,
            "routes": routes,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting dashboard data: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
