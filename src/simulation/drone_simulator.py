"""
Drone Swarm Earthquake Rescue System - Drone Simulator
Simulates drone telemetry data for earthquake disaster response
"""

import json
import time
import random
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
import uuid

@dataclass
class DronePosition:
    lat: float
    lon: float
    alt_m: float

@dataclass
class DetectedPerson:
    person_id: str
    confidence: float
    injury_level: str
    age_est: int
    vitals: Dict[str, int]

@dataclass
class NeighborBeacon:
    drone_id: str
    distance_m: float
    last_seen: str

@dataclass
class DroneTelemetry:
    timestamp_utc: str
    drone_id: str
    position: DronePosition
    speed_m_s: float
    heading_deg: float
    battery_pct: float
    status: str
    detected_person: Optional[DetectedPerson]
    nearest_responder_id: Optional[str]
    dist_to_nearest_responder_m: float
    neighbor_beacons: List[NeighborBeacon]
    message_seq: int

class DroneSimulator:
    def __init__(self, num_drones: int = 20, earthquake_center: tuple = (34.0522, -118.2437)):
        self.num_drones = num_drones
        self.earthquake_center = earthquake_center
        self.drones = self._initialize_drones()
        self.responders = self._initialize_responders()
        self.victims = []
        self.message_seq = 0
        
    def _initialize_drones(self) -> List[Dict]:
        """Initialize drone fleet with random positions around earthquake zone"""
        drones = []
        for i in range(self.num_drones):
            # Random position within 2km of earthquake center
            lat_offset = random.uniform(-0.02, 0.02)  # ~2km radius
            lon_offset = random.uniform(-0.02, 0.02)
            
            drone = {
                'id': f'drone-{i:03d}',
                'position': DronePosition(
                    lat=self.earthquake_center[0] + lat_offset,
                    lon=self.earthquake_center[1] + lon_offset,
                    alt_m=random.uniform(5, 50)
                ),
                'battery': random.uniform(60, 100),
                'status': random.choice(['searching', 'tracking', 'returning']),
                'speed': random.uniform(0.5, 3.0),
                'heading': random.uniform(0, 360)
            }
            drones.append(drone)
        return drones
    
    def _initialize_responders(self) -> List[Dict]:
        """Initialize emergency responders"""
        responders = []
        for i in range(5):  # 5 responder teams
            responder = {
                'id': f'responder-{i:02d}',
                'position': DronePosition(
                    lat=self.earthquake_center[0] + random.uniform(-0.01, 0.01),
                    lon=self.earthquake_center[1] + random.uniform(-0.01, 0.01),
                    alt_m=0
                ),
                'status': 'available'
            }
            responders.append(responder)
        return responders
    
    def _calculate_distance(self, pos1: DronePosition, pos2: DronePosition) -> float:
        """Calculate distance between two positions in meters"""
        from math import radians, cos, sin, asin, sqrt
        
        def haversine(lon1, lat1, lon2, lat2):
            lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
            dlon = lon2 - lon1
            dlat = lat2 - lat1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            r = 6371000  # Earth radius in meters
            return c * r
        
        return haversine(pos1.lon, pos1.lat, pos2.lon, pos2.lat)
    
    def _find_nearest_responder(self, drone_pos: DronePosition) -> tuple:
        """Find nearest responder to drone"""
        min_distance = float('inf')
        nearest_responder = None
        
        for responder in self.responders:
            distance = self._calculate_distance(drone_pos, responder['position'])
            if distance < min_distance:
                min_distance = distance
                nearest_responder = responder['id']
        
        return nearest_responder, min_distance
    
    def _simulate_person_detection(self, drone: Dict) -> Optional[DetectedPerson]:
        """Simulate person detection with realistic probabilities"""
        # 5% chance per minute of detecting a person
        if random.random() < 0.05:
            # Create new victim or use existing
            if not self.victims or random.random() < 0.3:
                victim_id = f'victim-{uuid.uuid4().hex[:8]}'
                victim = {
                    'id': victim_id,
                    'position': DronePosition(
                        lat=drone['position'].lat + random.uniform(-0.001, 0.001),
                        lon=drone['position'].lon + random.uniform(-0.001, 0.001),
                        alt_m=0
                    ),
                    'injury_level': random.choice(['none', 'minor', 'severe', 'unconscious']),
                    'age': random.randint(5, 80)
                }
                self.victims.append(victim)
            else:
                victim = random.choice(self.victims)
                victim_id = victim['id']
            
            # Generate vitals based on injury level
            injury_level = victim['injury_level']
            if injury_level == 'unconscious':
                hr, resp, spo2 = random.randint(30, 50), random.randint(5, 10), random.randint(60, 80)
            elif injury_level == 'severe':
                hr, resp, spo2 = random.randint(50, 80), random.randint(10, 20), random.randint(80, 90)
            elif injury_level == 'minor':
                hr, resp, spo2 = random.randint(70, 100), random.randint(12, 20), random.randint(90, 98)
            else:
                hr, resp, spo2 = random.randint(60, 100), random.randint(12, 25), random.randint(95, 100)
            
            return DetectedPerson(
                person_id=victim_id,
                confidence=random.uniform(0.7, 0.95),
                injury_level=injury_level,
                age_est=victim['age'],
                vitals={'hr': hr, 'resp': resp, 'spo2': spo2}
            )
        return None
    
    def _get_neighbor_beacons(self, drone: Dict) -> List[NeighborBeacon]:
        """Get nearby drone beacons for coordination"""
        beacons = []
        for other_drone in self.drones:
            if other_drone['id'] != drone['id']:
                distance = self._calculate_distance(drone['position'], other_drone['position'])
                if distance < 100:  # Within 100m
                    beacon = NeighborBeacon(
                        drone_id=other_drone['id'],
                        distance_m=distance,
                        last_seen=datetime.now(timezone.utc).isoformat()
                    )
                    beacons.append(beacon)
        return beacons
    
    def _update_drone_state(self, drone: Dict):
        """Update drone state for next iteration"""
        # Simulate movement
        drone['position'].lat += random.uniform(-0.0001, 0.0001)
        drone['position'].lon += random.uniform(-0.0001, 0.0001)
        drone['position'].alt_m += random.uniform(-2, 2)
        drone['position'].alt_m = max(5, min(50, drone['position'].alt_m))
        
        # Update battery (drain 0.5-2% per minute)
        drone['battery'] -= random.uniform(0.5, 2.0)
        drone['battery'] = max(0, drone['battery'])
        
        # Update status based on battery
        if drone['battery'] < 20:
            drone['status'] = 'returning'
        elif drone['battery'] < 10:
            drone['status'] = 'idle'
        elif drone['status'] == 'returning' and drone['battery'] > 80:
            drone['status'] = 'searching'
        
        # Update speed and heading
        drone['speed'] = random.uniform(0.5, 3.0)
        drone['heading'] = (drone['heading'] + random.uniform(-30, 30)) % 360
    
    def generate_telemetry(self) -> List[DroneTelemetry]:
        """Generate telemetry for all drones"""
        telemetry_list = []
        
        for drone in self.drones:
            # Update drone state
            self._update_drone_state(drone)
            
            # Simulate person detection
            detected_person = self._simulate_person_detection(drone)
            
            # Find nearest responder
            nearest_responder, distance = self._find_nearest_responder(drone['position'])
            
            # Get neighbor beacons
            neighbor_beacons = self._get_neighbor_beacons(drone)
            
            # Create telemetry
            telemetry = DroneTelemetry(
                timestamp_utc=datetime.now(timezone.utc).isoformat(),
                drone_id=drone['id'],
                position=drone['position'],
                speed_m_s=drone['speed'],
                heading_deg=drone['heading'],
                battery_pct=drone['battery'],
                status=drone['status'],
                detected_person=detected_person,
                nearest_responder_id=nearest_responder,
                dist_to_nearest_responder_m=distance,
                neighbor_beacons=neighbor_beacons,
                message_seq=self.message_seq
            )
            
            telemetry_list.append(telemetry)
            self.message_seq += 1
        
        return telemetry_list
    
    async def run_simulation(self, duration_minutes: int = 60, output_file: str = None):
        """Run continuous simulation"""
        print(f"Starting drone simulation with {self.num_drones} drones...")
        print(f"Simulation will run for {duration_minutes} minutes")
        
        all_telemetry = []
        start_time = time.time()
        
        try:
            while time.time() - start_time < duration_minutes * 60:
                # Generate telemetry for all drones
                telemetry_batch = self.generate_telemetry()
                all_telemetry.extend(telemetry_batch)
                
                # Print status
                active_drones = len([d for d in self.drones if d['battery'] > 10])
                detected_victims = len(self.victims)
                print(f"Time: {datetime.now().strftime('%H:%M:%S')} | "
                      f"Active drones: {active_drones}/{self.num_drones} | "
                      f"Victims detected: {detected_victims}")
                
                # Save to file if specified
                if output_file:
                    with open(output_file, 'w') as f:
                        json.dump([asdict(t) for t in all_telemetry], f, indent=2)
                
                # Wait 1 minute (60 seconds)
                await asyncio.sleep(60)
                
        except KeyboardInterrupt:
            print("\nSimulation stopped by user")
        
        print(f"Simulation complete. Generated {len(all_telemetry)} telemetry records.")
        return all_telemetry

def main():
    """Main function to run the simulator"""
    simulator = DroneSimulator(num_drones=20)
    
    # Run simulation for 10 minutes and save to file
    asyncio.run(simulator.run_simulation(
        duration_minutes=10,
        output_file='drone_telemetry.json'
    ))

if __name__ == "__main__":
    main()
