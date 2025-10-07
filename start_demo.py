#!/usr/bin/env python3
"""
Hackathon Demo Startup Script
Starts all components for the Drone Swarm Earthquake Rescue System
"""

import subprocess
import time
import webbrowser
import sys
import os

def start_api_server():
    """Start the API server"""
    print("🚀 Starting API Server...")
    try:
        # Start API server in background
        process = subprocess.Popen([
            sys.executable, "simple_api.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        time.sleep(5)
        
        # Test if server is running
        import requests
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ API Server started successfully")
            return process
        else:
            print("❌ API Server failed to start")
            return None
    except Exception as e:
        print(f"❌ Error starting API server: {e}")
        return None

def start_dashboard():
    """Start the dashboard server"""
    print("🌐 Starting Dashboard Server...")
    try:
        # Start HTTP server for dashboard
        process = subprocess.Popen([
            sys.executable, "-m", "http.server", "3000"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        time.sleep(3)
        print("✅ Dashboard server started")
        return process
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")
        return None

def start_simulation():
    """Start the enhanced real-time simulation"""
    print("🚁 Starting Enhanced Real-time Simulation...")
    try:
        # Start enhanced simulation in background
        process = subprocess.Popen([
            sys.executable, "enhanced_simulator.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print("✅ Enhanced simulation started")
        return process
    except Exception as e:
        print(f"❌ Error starting simulation: {e}")
        return None

def main():
    """Main demo startup function"""
    print("🚁 DRONE SWARM EARTHQUAKE RESCUE SYSTEM - HACKATHON DEMO")
    print("=" * 60)
    
    # Start all components
    api_process = start_api_server()
    if not api_process:
        print("❌ Cannot start demo without API server")
        return
    
    dashboard_process = start_dashboard()
    simulation_process = start_simulation()
    
    print("\n🎉 DEMO IS READY!")
    print("=" * 60)
    print("🌐 LIVE DASHBOARD: http://localhost:3000/live_demo_dashboard.html")
    print("📚 API DOCS: http://localhost:8000/docs")
    print("❤️ HEALTH: http://localhost:8000/health")
    print("=" * 60)
    print("🚀 Features:")
    print("✅ Real-time drone simulation")
    print("✅ ML survival predictions")
    print("✅ Dynamic route optimization")
    print("✅ Live dashboard updates")
    print("✅ Interactive map visualization")
    print("=" * 60)
    
    # Open dashboard in browser
    try:
        webbrowser.open("http://localhost:3000/live_demo_dashboard.html")
        print("🌐 Live dashboard opened in browser")
    except:
        print("🌐 Please open: http://localhost:3000/live_demo_dashboard.html")
    
    print("\n⏱️ Demo will run for 30 minutes")
    print("🛑 Press Ctrl+C to stop")
    
    try:
        # Keep running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping demo...")
        
        # Clean up processes
        if api_process:
            api_process.terminate()
        if dashboard_process:
            dashboard_process.terminate()
        if simulation_process:
            simulation_process.terminate()
        
        print("✅ Demo stopped")

if __name__ == "__main__":
    main()
