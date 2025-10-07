#!/usr/bin/env python3
"""
Real-time Drone Swarm Earthquake Rescue Simulation
Perfect for hackathon demonstrations
"""

import asyncio
import json
import random
import time
import requests
from datetime import datetime, timezone
from typing import Dict, List
import uuid

class RealTimeSimulator:
    def __init__(self):
        self.api_url = "http://localhost:8000"
        self.drones = []
        self.victims = []
        self.responders = []
        self.earthquake_center = (34.0522, -118.2437)  # Los Angeles
        self.simulation_running = False
        
    def initialize_simulation(self):
        """Initialize the simulation with realistic data"""
        print("🚁 Initializing Drone Swarm Earthquake Rescue Simulation...")
        
        # Create 15 drones
        for i in range(15):
            drone = {
                'id': f'drone-{i+1:03d}',
                'lat': self.earthquake_center[0] + random.uniform(-0.01, 0.01),
                'lon': self.earthquake_center[1] + random.uniform(-0.01, 0.01),
                'alt': random.uniform(10, 50),
                'battery': random.uniform(60, 100),
                'status': 'searching',
                'speed': random.uniform(1, 4),
                'heading': random.uniform(0, 360)
            }
            self.drones.append(drone)
        
        # Create 5 responders
        for i in range(5):
            responder = {
                'id': f'responder-{i+1:02d}',
                'lat': self.earthquake_center[0] + random.uniform(-0.005, 0.005),
                'lon': self.earthquake_center[1] + random.uniform(-0.005, 0.005),
                'capacity': random.randint(3, 8),
                'status': 'available'
            }
            self.responders.append(responder)
        
        # Send responders to API
        for responder in self.responders:
            self.send_responder_data(responder)
        
        print(f"✅ Initialized: {len(self.drones)} drones, {len(self.responders)} responders")
    
    def send_telemetry(self, drone):
        """Send drone telemetry to API"""
        try:
            # Simulate victim detection (5% chance per drone)
            detected_person = None
            if random.random() < 0.05 and len(self.victims) < 20:
                victim_id = f'victim-{uuid.uuid4().hex[:8]}'
                injury_levels = ['none', 'minor', 'severe', 'unconscious']
                injury_level = random.choices(injury_levels, weights=[0.1, 0.3, 0.4, 0.2])[0]
                
                detected_person = {
                    'person_id': victim_id,
                    'confidence': random.uniform(0.7, 0.95),
                    'injury_level': injury_level,
                    'age_est': random.randint(5, 80),
                    'vitals': {
                        'hr': random.randint(40, 120),
                        'resp': random.randint(8, 25),
                        'spo2': random.randint(70, 100)
                    }
                }
                
                # Add victim to our list
                victim = {
                    'id': victim_id,
                    'lat': drone['lat'] + random.uniform(-0.001, 0.001),
                    'lon': drone['lon'] + random.uniform(-0.001, 0.001),
                    'injury_level': injury_level,
                    'detected_at': datetime.now()
                }
                self.victims.append(victim)
            
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
                'dist_to_nearest_responder_m': random.uniform(100, 500),
                'neighbor_beacons': [],
                'message_seq': random.randint(1, 1000)
            }
            
            # Send to API
            response = requests.post(f"{self.api_url}/telemetry", json=telemetry, timeout=5)
            if response.status_code == 200:
                print(f"📡 {drone['id']}: {drone['status']}, Battery: {drone['battery']:.0f}%", end="")
                if detected_person:
                    print(f" 🚨 VICTIM DETECTED: {detected_person['injury_level']}")
                else:
                    print()
            else:
                print(f"❌ Failed to send telemetry for {drone['id']}")
                
        except Exception as e:
            print(f"❌ Error sending telemetry: {e}")
    
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
    
    def update_drone_positions(self):
        """Update drone positions and status"""
        for drone in self.drones:
            # Move drone
            drone['lat'] += random.uniform(-0.0001, 0.0001)
            drone['lon'] += random.uniform(-0.0001, 0.0001)
            drone['alt'] += random.uniform(-2, 2)
            drone['alt'] = max(10, min(50, drone['alt']))
            
            # Update battery (drain 0.5-2% per update)
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
            drone['speed'] = random.uniform(1, 4)
            drone['heading'] = (drone['heading'] + random.uniform(-30, 30)) % 360
    
    def get_system_status(self):
        """Get current system status"""
        try:
            response = requests.get(f"{self.api_url}/status", timeout=5)
            if response.status_code == 200:
                status = response.json()
                return status
        except Exception as e:
            print(f"❌ Error getting status: {e}")
        return None
    
    def display_status(self):
        """Display current simulation status"""
        status = self.get_system_status()
        if status:
            print(f"\n📊 SIMULATION STATUS:")
            print(f"🚁 Active Drones: {status.get('active_drones', 0)}")
            print(f"🚨 Total Victims: {status.get('total_victims', 0)}")
            print(f"🚑 Available Responders: {status.get('available_responders', 0)}")
            print(f"📈 Avg Survival Rate: {status.get('average_survival_likelihood', 0)*100:.1f}%")
            print(f"⚖️ System Load: {status.get('system_load', 0):.1f}")
            print(f"🕐 Time: {datetime.now().strftime('%H:%M:%S')}")
            print("-" * 50)
    
    async def run_simulation(self, duration_minutes=30):
        """Run the real-time simulation"""
        print("🚀 Starting Real-time Drone Swarm Simulation...")
        print(f"⏱️ Duration: {duration_minutes} minutes")
        print(f"🌐 Dashboard: http://localhost:3000/simple_dashboard.html")
        print(f"📚 API Docs: http://localhost:8000/docs")
        print("=" * 60)
        
        self.simulation_running = True
        start_time = time.time()
        
        try:
            while self.simulation_running and (time.time() - start_time) < duration_minutes * 60:
                # Update drone positions
                self.update_drone_positions()
                
                # Send telemetry for all drones
                for drone in self.drones:
                    self.send_telemetry(drone)
                
                # Display status every 30 seconds
                if int(time.time() - start_time) % 30 == 0:
                    self.display_status()
                
                # Wait 10 seconds before next update
                await asyncio.sleep(10)
                
        except KeyboardInterrupt:
            print("\n🛑 Simulation stopped by user")
        finally:
            self.simulation_running = False
            print("✅ Simulation completed")

def main():
    """Main function to run the simulation"""
    simulator = RealTimeSimulator()
    
    # Initialize the simulation
    simulator.initialize_simulation()
    
    # Wait a moment for initialization
    time.sleep(2)
    
    # Run the simulation
    asyncio.run(simulator.run_simulation(duration_minutes=30))

if __name__ == "__main__":
    main()
