#!/usr/bin/env python3
"""
Simple API server for Drone Swarm Earthquake Rescue System
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import json
import random
from datetime import datetime, timezone

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

# Global data storage
telemetry_data = []
victims_data = {}
responders_data = {}

# Pydantic models
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
        "model_loaded": True
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
        # Simple survival likelihood calculation
        injury_level = person_data.get('injury_level', 'minor')
        injury_scores = {'none': 0.9, 'minor': 0.7, 'severe': 0.4, 'unconscious': 0.2}
        survival_likelihood = injury_scores.get(injury_level, 0.5)
        
        # Add some randomness
        survival_likelihood += random.uniform(-0.1, 0.1)
        survival_likelihood = max(0.0, min(1.0, survival_likelihood))
        
        # Create victim object
        victim = {
            'id': person_data['person_id'],
            'lat': drone_position['lat'],
            'lon': drone_position['lon'],
            'survival_likelihood': survival_likelihood,
            'injury_level': person_data['injury_level'],
            'time_detected': datetime.now(),
            'priority_score': survival_likelihood * 100
        }
        
        # Add to victims data
        victims_data[victim['id']] = victim
        
        print(f"Processed victim {victim['id']} with survival likelihood {survival_likelihood:.3f}")
        
    except Exception as e:
        print(f"Error processing detected person: {str(e)}")

@app.post("/responders")
async def add_responder(responder: ResponderRequest):
    """Add or update responder information"""
    try:
        responder_obj = {
            'id': responder.responder_id,
            'lat': responder.lat,
            'lon': responder.lon,
            'capacity': responder.capacity,
            'status': responder.status,
            'current_route': []
        }
        
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
        routes = []
        
        # Simple route generation for demo
        for responder_id, responder in responders_data.items():
            if responder['status'] == 'available':
                # Get top victims
                sorted_victims = sorted(victims_data.values(), 
                                      key=lambda v: v['priority_score'], 
                                      reverse=True)
                
                # Create simple route
                route_victims = sorted_victims[:3]  # Top 3 victims
                route = [v['id'] for v in route_victims]
                
                routes.append({
                    "responder_id": responder_id,
                    "route": route,
                    "total_distance": random.uniform(1000, 5000),
                    "estimated_time": random.uniform(1.0, 3.0),
                    "victims_served": route
                })
        
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
                "id": victim['id'],
                "lat": victim['lat'],
                "lon": victim['lon'],
                "survival_likelihood": victim['survival_likelihood'],
                "injury_level": victim['injury_level'],
                "time_detected": victim['time_detected'].isoformat(),
                "priority_score": victim['priority_score']
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
        total_victims = len(victims_data)
        available_responders = len([r for r in responders_data.values() if r['status'] == 'available'])
        
        # Calculate average survival likelihood
        if victims_data:
            avg_survival = sum(v['survival_likelihood'] for v in victims_data.values()) / len(victims_data)
        else:
            avg_survival = 0
        
        # Count active drones
        active_drones = len(set(t['drone_id'] for t in telemetry_data[-100:])) if telemetry_data else 0
        
        return {
            "total_victims": total_victims,
            "available_responders": available_responders,
            "average_survival_likelihood": avg_survival,
            "system_load": total_victims / max(available_responders, 1),
            "active_drones": active_drones
        }
    
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

@app.get("/dashboard/data")
async def get_dashboard_data():
    """Get all data needed for dashboard"""
    try:
        # Get system status
        status = await get_system_status()
        
        # Get latest telemetry
        latest_telemetry = telemetry_data[-50:] if telemetry_data else []
        
        # Get victims
        victims_list = []
        for victim in victims_data.values():
            victims_list.append({
                "id": victim['id'],
                "lat": victim['lat'],
                "lon": victim['lon'],
                "survival_likelihood": victim['survival_likelihood'],
                "injury_level": victim['injury_level'],
                "time_detected": victim['time_detected'].isoformat(),
                "priority_score": victim['priority_score']
            })
        
        # Get routes
        routes_response = await get_optimized_routes()
        routes = routes_response.get('routes', [])
        
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
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
