#!/usr/bin/env python3
"""
Demo script for Drone Swarm Earthquake Rescue System
Runs a complete demonstration of the system
"""

import sys
import os
import json
import time
import requests
import subprocess
import threading
from datetime import datetime, timezone

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

class DemoRunner:
    def __init__(self):
        self.api_process = None
        self.simulator_process = None
        self.dashboard_process = None
        self.demo_data = []
        
    def start_api_server(self):
        """Start the API server"""
        print("Starting API server...")
        try:
            self.api_process = subprocess.Popen([
                sys.executable, "src/api/main.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for server to start
            time.sleep(5)
            
            # Test if server is running
            response = requests.get("http://localhost:8000/health", timeout=10)
            if response.status_code == 200:
                print("✓ API server started successfully")
                return True
            else:
                print("✗ API server failed to start")
                return False
        except Exception as e:
            print(f"✗ Failed to start API server: {e}")
            return False
    
    def start_drone_simulator(self):
        """Start the drone simulator"""
        print("Starting drone simulator...")
        try:
            # Import and run simulator
            from simulation.drone_simulator import DroneSimulator
            
            simulator = DroneSimulator(num_drones=20)
            
            # Run simulation in background
            def run_simulation():
                asyncio.run(simulator.run_simulation(duration_minutes=10))
            
            import asyncio
            self.simulator_thread = threading.Thread(target=run_simulation)
            self.simulator_thread.daemon = True
            self.simulator_thread.start()
            
            print("✓ Drone simulator started successfully")
            return True
        except Exception as e:
            print(f"✗ Failed to start drone simulator: {e}")
            return False
    
    def start_dashboard(self):
        """Start the dashboard"""
        print("Starting dashboard...")
        try:
            # Check if dashboard is already running
            response = requests.get("http://localhost:3000", timeout=5)
            if response.status_code == 200:
                print("✓ Dashboard already running")
                return True
            
            # Start dashboard in background
            self.dashboard_process = subprocess.Popen([
                "npm", "start"
            ], cwd="dashboard", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Wait for dashboard to start
            time.sleep(10)
            
            # Test if dashboard is running
            response = requests.get("http://localhost:3000", timeout=10)
            if response.status_code == 200:
                print("✓ Dashboard started successfully")
                return True
            else:
                print("✗ Dashboard failed to start")
                return False
        except Exception as e:
            print(f"✗ Failed to start dashboard: {e}")
            return False
    
    def run_demo_scenario(self):
        """Run the demo scenario"""
        print("\n" + "=" * 50)
        print("DEMO SCENARIO: Earthquake Rescue Operation")
        print("=" * 50)
        
        # Step 1: Show system status
        print("\n1. System Status Check:")
        try:
            response = requests.get("http://localhost:8000/status")
            status = response.json()
            
            print(f"   • Active Drones: {status.get('active_drones', 0)}")
            print(f"   • Total Victims: {status.get('total_victims', 0)}")
            print(f"   • Available Responders: {status.get('available_responders', 0)}")
            print(f"   • Average Survival Likelihood: {status.get('average_survival_likelihood', 0):.3f}")
        except Exception as e:
            print(f"   ✗ Failed to get system status: {e}")
        
        # Step 2: Show drone telemetry
        print("\n2. Drone Telemetry:")
        try:
            response = requests.get("http://localhost:8000/telemetry/latest?limit=5")
            telemetry = response.json().get('telemetry', [])
            
            for i, drone in enumerate(telemetry[:3]):
                print(f"   • Drone {drone['drone_id']}: {drone['status']}, Battery: {drone['battery_pct']}%")
                if drone.get('detected_person'):
                    print(f"     - Victim detected: {drone['detected_person']['person_id']}")
        except Exception as e:
            print(f"   ✗ Failed to get telemetry: {e}")
        
        # Step 3: Show victim information
        print("\n3. Victim Information:")
        try:
            response = requests.get("http://localhost:8000/victims")
            victims = response.json().get('victims', [])
            
            for i, victim in enumerate(victims[:3]):
                print(f"   • Victim {victim['id']}: {victim['injury_level']}, Survival: {victim['survival_likelihood']:.3f}")
        except Exception as e:
            print(f"   ✗ Failed to get victims: {e}")
        
        # Step 4: Show optimized routes
        print("\n4. Optimized Routes:")
        try:
            response = requests.get("http://localhost:8000/routes")
            routes = response.json().get('routes', [])
            
            for route in routes:
                print(f"   • Responder {route['responder_id']}: {len(route['route'])} victims, {route['estimated_time']:.1f} hours")
        except Exception as e:
            print(f"   ✗ Failed to get routes: {e}")
        
        # Step 5: Show real-time updates
        print("\n5. Real-time Updates:")
        print("   • Dashboard URL: http://localhost:3000")
        print("   • API Documentation: http://localhost:8000/docs")
        print("   • System updates every 5 seconds")
    
    def cleanup(self):
        """Clean up processes"""
        print("\nCleaning up...")
        
        if self.api_process:
            self.api_process.terminate()
            self.api_process.wait()
        
        if self.dashboard_process:
            self.dashboard_process.terminate()
            self.dashboard_process.wait()
        
        print("✓ Cleanup complete")
    
    def run_demo(self):
        """Run the complete demo"""
        print("Drone Swarm Earthquake Rescue System - Demo")
        print("=" * 50)
        
        try:
            # Start all services
            if not self.start_api_server():
                return False
            
            if not self.start_drone_simulator():
                return False
            
            if not self.start_dashboard():
                return False
            
            # Run demo scenario
            self.run_demo_scenario()
            
            # Keep running for demo
            print("\n" + "=" * 50)
            print("Demo is running! Press Ctrl+C to stop.")
            print("=" * 50)
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nDemo stopped by user")
            
            return True
            
        except Exception as e:
            print(f"Demo failed: {e}")
            return False
        finally:
            self.cleanup()

def main():
    """Main function"""
    demo = DemoRunner()
    success = demo.run_demo()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
