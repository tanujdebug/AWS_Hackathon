#!/usr/bin/env python3
"""
Enhanced Real-time Drone Swarm Simulation
Drones move visibly on the map with realistic flight patterns
"""

import asyncio
import json
import random
import time
import requests
from datetime import datetime, timezone
from typing import Dict, List
import uuid
import math

class EnhancedDroneSimulator:
    def __init__(self):
        self.api_url = "http://localhost:8000"
        self.drones = []
        self.victims = []
        self.responders = []
        self.earthquake_center = (34.0522, -118.2437)  # Los Angeles
        self.search_radius = 0.01  # ~1km radius
        self.simulation_running = False
        
    def initialize_simulation(self):
        """Initialize the simulation with realistic data"""
        print("🚁 Initializing Enhanced Drone Swarm Simulation...")
        
        # Create 20 drones in a grid pattern around earthquake center
        grid_size = 5
        for i in range(20):
            row = i // grid_size
            col = i % grid_size
            
            # Create grid pattern around earthquake center
            lat_offset = (row - 2) * 0.002  # ~200m spacing
            lon_offset = (col - 2) * 0.002
            
            drone = {
                'id': f'drone-{i+1:03d}',
                'lat': self.earthquake_center[0] + lat_offset,
                'lon': self.earthquake_center[1] + lon_offset,
                'alt': random.uniform(15, 45),
                'battery': random.uniform(70, 100),
                'status': 'searching',
                'speed': random.uniform(2, 5),
                'heading': random.uniform(0, 360),
                'target_lat': None,
                'target_lon': None,
                'search_pattern': 'spiral',  # spiral, grid, random
                'search_radius': 0.001,
                'last_victim_check': time.time()
            }
            self.drones.append(drone)
        
        # Create 6 responders around the perimeter
        for i in range(6):
            angle = (i * 60) * math.pi / 180  # 60 degrees apart
            distance = 0.008  # ~800m from center
            
            responder = {
                'id': f'responder-{i+1:02d}',
                'lat': self.earthquake_center[0] + distance * math.cos(angle),
                'lon': self.earthquake_center[1] + distance * math.sin(angle),
                'capacity': random.randint(4, 8),
                'status': 'available'
            }
            self.responders.append(responder)
        
        # Send responders to API
        for responder in self.responders:
            self.send_responder_data(responder)
        
        print(f"✅ Initialized: {len(self.drones)} drones, {len(self.responders)} responders")
    
    def update_drone_movement(self, drone):
        """Update drone position with realistic movement patterns"""
        if drone['status'] == 'idle':
            return
        
        # Different movement patterns
        if drone['search_pattern'] == 'spiral':
            self.spiral_search(drone)
        elif drone['search_pattern'] == 'grid':
            self.grid_search(drone)
        else:
            self.random_search(drone)
        
        # Keep drones within search area
        distance_from_center = math.sqrt(
            (drone['lat'] - self.earthquake_center[0])**2 + 
            (drone['lon'] - self.earthquake_center[1])**2
        )
        
        if distance_from_center > self.search_radius:
            # Move back towards center
            angle_to_center = math.atan2(
                self.earthquake_center[1] - drone['lon'],
                self.earthquake_center[0] - drone['lat']
            )
            drone['lat'] += 0.0001 * math.cos(angle_to_center)
            drone['lon'] += 0.0001 * math.sin(angle_to_center)
    
    def spiral_search(self, drone):
        """Spiral search pattern"""
        # Update heading for spiral
        drone['heading'] = (drone['heading'] + 2) % 360
        
        # Move in spiral pattern
        angle_rad = math.radians(drone['heading'])
        move_distance = 0.0001  # Small movement
        
        drone['lat'] += move_distance * math.cos(angle_rad)
        drone['lon'] += move_distance * math.sin(angle_rad)
    
    def grid_search(self, drone):
        """Grid search pattern"""
        # Move in straight lines, turning at boundaries
        if random.random() < 0.1:  # 10% chance to change direction
            drone['heading'] = random.choice([0, 90, 180, 270])
        
        angle_rad = math.radians(drone['heading'])
        move_distance = 0.0002
        
        drone['lat'] += move_distance * math.cos(angle_rad)
        drone['lon'] += move_distance * math.sin(angle_rad)
    
    def random_search(self, drone):
        """Random search pattern"""
        # Random movement with slight bias towards center
        center_lat, center_lon = self.earthquake_center
        
        # Random movement
        drone['lat'] += random.uniform(-0.0002, 0.0002)
        drone['lon'] += random.uniform(-0.0002, 0.0002)
        
        # Slight bias towards center
        if random.random() < 0.3:
            drone['lat'] += 0.00005 * (center_lat - drone['lat'])
            drone['lon'] += 0.00005 * (center_lon - drone['lon'])
    
    def check_for_victims(self, drone):
        """Check if drone should detect a victim"""
        current_time = time.time()
        
        # Only check every 30 seconds per drone
        if current_time - drone['last_victim_check'] < 30:
            return None
        
        drone['last_victim_check'] = current_time
        
        # 12% chance per check to find a victim (increased detection)
        if random.random() < 0.12 and len(self.victims) < 25:
            victim_id = f'victim-{uuid.uuid4().hex[:8]}'
            # Prioritize severe patients - higher chance of severe/unconscious
            injury_levels = ['none', 'minor', 'severe', 'unconscious']
            injury_level = random.choices(injury_levels, weights=[0.05, 0.25, 0.45, 0.25])[0]
            
            # Create victim near drone location
            victim = {
                'id': victim_id,
                'lat': drone['lat'] + random.uniform(-0.0005, 0.0005),
                'lon': drone['lon'] + random.uniform(-0.0005, 0.0005),
                'injury_level': injury_level,
                'detected_at': datetime.now(),
                'detected_by': drone['id']
            }
            self.victims.append(victim)
            
            # Drone changes to tracking mode
            drone['status'] = 'tracking'
            drone['target_lat'] = victim['lat']
            drone['target_lon'] = victim['lon']
            
            return {
                'person_id': victim_id,
                'confidence': random.uniform(0.75, 0.95),
                'injury_level': injury_level,
                'age_est': random.randint(5, 80),
                'vitals': {
                    'hr': random.randint(40, 120),
                    'resp': random.randint(8, 25),
                    'spo2': random.randint(70, 100)
                }
            }
        
        return None
    
    def update_drone_status(self, drone):
        """Update drone status (no battery concerns)"""
        # Keep battery high for continuous operation
        drone['battery'] = random.uniform(85, 100)
        
        # Update status based on activity only
        if drone['status'] == 'tracking' and random.random() < 0.15:
            drone['status'] = 'searching'  # Resume search after tracking
    
    def send_telemetry(self, drone):
        """Send drone telemetry to API"""
        try:
            # Check for victim detection
            detected_person = self.check_for_victims(drone)
            
            # Create telemetry payload
            telemetry = {
                'timestamp_utc': datetime.now(timezone.utc).isoformat(),
                'drone_id': drone['id'],
                'position': {
                    'lat': drone['lat'],
                    'lon': drone['lon'],
                    'alt_m': drone['alt']
                },
                'speed_m_s': drone['speed'],
                'heading_deg': drone['heading'],
                'battery_pct': drone['battery'],
                'status': drone['status'],
                'detected_person': detected_person,
                'nearest_responder_id': random.choice(self.responders)['id'],
                'dist_to_nearest_responder_m': random.uniform(200, 800),
                'neighbor_beacons': self.get_neighbor_beacons(drone),
                'message_seq': random.randint(1, 1000)
            }
            
            # Send to API
            response = requests.post(f"{self.api_url}/telemetry", json=telemetry, timeout=5)
            if response.status_code == 200:
                status_emoji = {
                    'searching': '🔍',
                    'tracking': '🎯',
                    'returning': '🔋',
                    'idle': '⏸️'
                }
                emoji = status_emoji.get(drone['status'], '🚁')
                print(f"{emoji} {drone['id']}: {drone['status']}, Battery: {drone['battery']:.0f}%", end="")
                if detected_person:
                    print(f" 🚨 VICTIM: {detected_person['injury_level']}")
                else:
                    print()
            else:
                print(f"❌ Failed to send telemetry for {drone['id']}")
                
        except Exception as e:
            print(f"❌ Error sending telemetry: {e}")
    
    def get_neighbor_beacons(self, drone):
        """Get nearby drone beacons"""
        beacons = []
        for other_drone in self.drones:
            if other_drone['id'] != drone['id']:
                distance = math.sqrt(
                    (drone['lat'] - other_drone['lat'])**2 + 
                    (drone['lon'] - other_drone['lon'])**2
                ) * 111000  # Convert to meters
                
                if distance < 200:  # Within 200m
                    beacons.append({
                        'drone_id': other_drone['id'],
                        'distance_m': distance,
                        'last_seen': datetime.now(timezone.utc).isoformat()
                    })
        return beacons
    
    def send_responder_data(self, responder):
        """Send responder data to API"""
        try:
            payload = {
                'responder_id': responder['id'],
                'lat': responder['lat'],
                'lon': responder['lon'],
                'capacity': responder['capacity'],
                'status': responder['status']
            }
            response = requests.post(f"{self.api_url}/responders", json=payload, timeout=5)
            if response.status_code == 200:
                print(f"🚑 Added responder {responder['id']}")
        except Exception as e:
            print(f"❌ Error adding responder: {e}")
    
    def get_system_status(self):
        """Get current system status"""
        try:
            response = requests.get(f"{self.api_url}/status", timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"❌ Error getting status: {e}")
        return None
    
    def display_status(self):
        """Display current simulation status"""
        status = self.get_system_status()
        if status:
            print(f"\n📊 LIVE SIMULATION STATUS:")
            print(f"🚁 Active Drones: {status.get('active_drones', 0)}")
            print(f"🚨 Total Victims: {status.get('total_victims', 0)}")
            print(f"🚑 Available Responders: {status.get('available_responders', 0)}")
            print(f"📈 Avg Survival Rate: {status.get('average_survival_likelihood', 0)*100:.1f}%")
            print(f"⚖️ System Load: {status.get('system_load', 0):.1f}")
            print(f"🕐 Time: {datetime.now().strftime('%H:%M:%S')}")
            print("-" * 50)
    
    async def run_simulation(self, duration_minutes=30):
        """Run the enhanced real-time simulation"""
        print("🚀 Starting Enhanced Drone Swarm Simulation...")
        print(f"⏱️ Duration: {duration_minutes} minutes")
        print(f"🌐 Dashboard: http://localhost:3000/hackathon_dashboard.html")
        print(f"📚 API Docs: http://localhost:8000/docs")
        print("=" * 60)
        
        self.simulation_running = True
        start_time = time.time()
        
        try:
            while self.simulation_running and (time.time() - start_time) < duration_minutes * 60:
                # Update all drones
                for drone in self.drones:
                    # Update movement
                    self.update_drone_movement(drone)
                    
                    # Update status and battery
                    self.update_drone_status(drone)
                    
                    # Send telemetry
                    self.send_telemetry(drone)
                
                # Display status every 20 seconds
                if int(time.time() - start_time) % 20 == 0:
                    self.display_status()
                
                # Wait 8 seconds before next update (faster updates for better visualization)
                await asyncio.sleep(8)
                
        except KeyboardInterrupt:
            print("\n🛑 Simulation stopped by user")
        finally:
            self.simulation_running = False
            print("✅ Simulation completed")

def main():
    """Main function to run the enhanced simulation"""
    simulator = EnhancedDroneSimulator()
    
    # Initialize the simulation
    simulator.initialize_simulation()
    
    # Wait a moment for initialization
    time.sleep(2)
    
    # Run the simulation
    asyncio.run(simulator.run_simulation(duration_minutes=30))

if __name__ == "__main__":
    main()
