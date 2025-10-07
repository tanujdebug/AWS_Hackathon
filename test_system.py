#!/usr/bin/env python3
"""
Test script for Drone Swarm Earthquake Rescue System
Validates all components are working correctly
"""

import sys
import os
import json
import time
import requests
from datetime import datetime, timezone

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

def test_drone_simulator():
    """Test drone simulator"""
    print("Testing drone simulator...")
    try:
        from simulation.drone_simulator import DroneSimulator
        
        simulator = DroneSimulator(num_drones=5)
        telemetry = simulator.generate_telemetry()
        
        assert len(telemetry) == 5, f"Expected 5 drones, got {len(telemetry)}"
        assert all(t.drone_id for t in telemetry), "All drones should have IDs"
        
        print("✓ Drone simulator working correctly")
        return True
    except Exception as e:
        print(f"✗ Drone simulator failed: {e}")
        return False

def test_ml_model():
    """Test ML model"""
    print("Testing ML model...")
    try:
        from ml.survival_model import SurvivalLikelihoodModel
        
        model = SurvivalLikelihoodModel()
        
        # Create synthetic data
        df = model._create_synthetic_dataset(n_samples=100)
        X, y = model.prepare_features(df)
        
        # Train model
        model.train(X, y, model_type='xgboost')
        
        # Test prediction
        test_features = {
            'age': 30,
            'injury_level': 'minor',
            'time_since_detection': 30,
            'distance_to_responder': 200,
            'rubble_density': 0.5,
            'time_of_day': 12,
            'hr': 75,
            'resp': 16,
            'spo2': 95,
            'detection_confidence': 0.8,
            'comms_quality': 0.9
        }
        
        prediction = model.predict_survival_likelihood(test_features)
        assert 0 <= prediction <= 1, f"Prediction should be between 0 and 1, got {prediction}"
        
        print("✓ ML model working correctly")
        return True
    except Exception as e:
        print(f"✗ ML model failed: {e}")
        return False

def test_route_optimizer():
    """Test route optimizer"""
    print("Testing route optimizer...")
    try:
        from routing.route_optimizer import RouteOptimizer, Victim, Responder
        
        optimizer = RouteOptimizer()
        
        # Add sample data
        responder = Responder('responder-01', 34.0522, -118.2437, 5, 'available', [])
        optimizer.add_responder(responder)
        
        victim = Victim('victim-01', 34.0525, -118.2440, 0.85, 'severe', datetime.now(), 0)
        optimizer.add_victim(victim)
        
        # Test optimization
        solutions = optimizer.optimize_routes()
        assert len(solutions) > 0, "Should have at least one route solution"
        
        print("✓ Route optimizer working correctly")
        return True
    except Exception as e:
        print(f"✗ Route optimizer failed: {e}")
        return False

def test_api_server():
    """Test API server"""
    print("Testing API server...")
    try:
        # Check if server is running
        response = requests.get("http://localhost:8000/health", timeout=5)
        assert response.status_code == 200, f"API server not responding: {response.status_code}"
        
        # Test telemetry endpoint
        telemetry_data = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "drone_id": "test-drone-001",
            "position": {"lat": 34.0522, "lon": -118.2437},
            "speed_m_s": 2.5,
            "heading_deg": 45.0,
            "battery_pct": 85.0,
            "status": "searching",
            "detected_person": None,
            "nearest_responder_id": "responder-01",
            "dist_to_nearest_responder_m": 250.0,
            "neighbor_beacons": [],
            "message_seq": 1
        }
        
        response = requests.post("http://localhost:8000/telemetry", json=telemetry_data)
        assert response.status_code == 200, f"Telemetry endpoint failed: {response.status_code}"
        
        print("✓ API server working correctly")
        return True
    except requests.exceptions.ConnectionError:
        print("✗ API server not running - start with: python src/api/main.py")
        return False
    except Exception as e:
        print(f"✗ API server failed: {e}")
        return False

def test_dashboard():
    """Test dashboard"""
    print("Testing dashboard...")
    try:
        # Check if dashboard is running
        response = requests.get("http://localhost:3000", timeout=5)
        assert response.status_code == 200, f"Dashboard not responding: {response.status_code}"
        
        print("✓ Dashboard working correctly")
        return True
    except requests.exceptions.ConnectionError:
        print("✗ Dashboard not running - start with: cd dashboard && npm start")
        return False
    except Exception as e:
        print(f"✗ Dashboard failed: {e}")
        return False

def test_integration():
    """Test full system integration"""
    print("Testing system integration...")
    try:
        # Test API endpoints
        response = requests.get("http://localhost:8000/dashboard/data")
        assert response.status_code == 200, f"Dashboard data endpoint failed: {response.status_code}"
        
        data = response.json()
        assert 'system_status' in data, "Dashboard data should include system status"
        assert 'telemetry' in data, "Dashboard data should include telemetry"
        assert 'victims' in data, "Dashboard data should include victims"
        assert 'routes' in data, "Dashboard data should include routes"
        
        print("✓ System integration working correctly")
        return True
    except requests.exceptions.ConnectionError:
        print("✗ API server not running")
        return False
    except Exception as e:
        print(f"✗ System integration failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("Drone Swarm Earthquake Rescue System - Test Suite")
    print("=" * 50)
    
    tests = [
        ("Drone Simulator", test_drone_simulator),
        ("ML Model", test_ml_model),
        ("Route Optimizer", test_route_optimizer),
        ("API Server", test_api_server),
        ("Dashboard", test_dashboard),
        ("System Integration", test_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 30)
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready for demo.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
