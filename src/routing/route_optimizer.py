"""
Dynamic Route Optimization for Earthquake Rescue System
Optimizes rescue routes for emergency responders using OR-Tools
"""

import numpy as np
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from typing import List, Dict, Tuple, Optional
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
import math

@dataclass
class Victim:
    id: str
    lat: float
    lon: float
    survival_likelihood: float
    injury_level: str
    time_detected: datetime
    priority_score: float

@dataclass
class Responder:
    id: str
    lat: float
    lon: float
    capacity: int
    status: str
    current_route: List[str]

@dataclass
class RouteSolution:
    responder_id: str
    route: List[str]
    total_distance: float
    estimated_time: float
    victims_served: List[str]

class RouteOptimizer:
    def __init__(self):
        self.victims = {}
        self.responders = {}
        self.distance_matrix = None
        self.time_matrix = None
        
    def add_victim(self, victim: Victim):
        """Add or update victim information"""
        self.victims[victim.id] = victim
        
    def add_responder(self, responder: Responder):
        """Add or update responder information"""
        self.responders[responder.id] = responder
        
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate haversine distance between two points in meters"""
        R = 6371000  # Earth's radius in meters
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))
        
        return R * c
    
    def _calculate_time_matrix(self, distance_matrix: np.ndarray) -> np.ndarray:
        """Convert distance matrix to time matrix (assuming average speed)"""
        # Assume average speed of 5 km/h for rescue operations in rubble
        avg_speed_ms = 5000 / 3600  # 5 km/h in m/s
        time_matrix = distance_matrix / avg_speed_ms
        return time_matrix
    
    def _build_distance_matrix(self) -> np.ndarray:
        """Build distance matrix between all locations"""
        # Combine responders and victims
        locations = []
        
        # Add responder locations
        for responder in self.responders.values():
            locations.append((responder.lat, responder.lon))
        
        # Add victim locations
        for victim in self.victims.values():
            locations.append((victim.lat, victim.lon))
        
        n_locations = len(locations)
        distance_matrix = np.zeros((n_locations, n_locations))
        
        for i in range(n_locations):
            for j in range(n_locations):
                if i != j:
                    lat1, lon1 = locations[i]
                    lat2, lon2 = locations[j]
                    distance_matrix[i][j] = self._calculate_distance(lat1, lon1, lat2, lon2)
        
        return distance_matrix
    
    def _calculate_priority_score(self, victim: Victim) -> float:
        """Calculate priority score for victim based on multiple factors"""
        # Base score from survival likelihood
        base_score = victim.survival_likelihood * 100
        
        # Time factor (urgency increases with time)
        time_elapsed = (datetime.now() - victim.time_detected).total_seconds() / 3600  # hours
        time_factor = 1 + (time_elapsed / 24)  # Increase urgency over time
        
        # Injury level factor
        injury_factors = {
            'unconscious': 1.5,
            'severe': 1.3,
            'minor': 1.1,
            'none': 1.0
        }
        injury_factor = injury_factors.get(victim.injury_level, 1.0)
        
        # Calculate final priority score
        priority_score = base_score * time_factor * injury_factor
        
        return priority_score
    
    def _select_top_victims(self, max_victims: int = 10) -> List[Victim]:
        """Select top priority victims for routing"""
        # Calculate priority scores
        for victim in self.victims.values():
            victim.priority_score = self._calculate_priority_score(victim)
        
        # Sort by priority score and select top N
        sorted_victims = sorted(self.victims.values(), 
                              key=lambda v: v.priority_score, 
                              reverse=True)
        
        return sorted_victims[:max_victims]
    
    def optimize_routes(self, max_victims_per_responder: int = 5) -> List[RouteSolution]:
        """Optimize routes for all responders"""
        if not self.victims or not self.responders:
            return []
        
        # Select top priority victims
        top_victims = self._select_top_victims(max_victims=len(self.victims))
        
        if not top_victims:
            return []
        
        # Build distance matrix
        self.distance_matrix = self._build_distance_matrix()
        self.time_matrix = self._calculate_time_matrix(self.distance_matrix)
        
        solutions = []
        
        # Optimize route for each responder
        for responder in self.responders.values():
            if responder.status != 'available':
                continue
                
            # Create a subset of victims for this responder
            responder_victims = top_victims[:max_victims_per_responder]
            
            if not responder_victims:
                continue
            
            # Solve VRP for this responder
            route_solution = self._solve_vrp_for_responder(responder, responder_victims)
            
            if route_solution:
                solutions.append(route_solution)
        
        return solutions
    
    def _solve_vrp_for_responder(self, responder: Responder, victims: List[Victim]) -> Optional[RouteSolution]:
        """Solve Vehicle Routing Problem for a single responder"""
        if not victims:
            return None
        
        # Create data model
        data = {}
        data['distance_matrix'] = self._create_subset_distance_matrix(responder, victims)
        data['num_vehicles'] = 1
        data['depot'] = 0  # Responder is at index 0
        
        # Create routing model
        manager = pywrapcp.RoutingIndexManager(
            len(data['distance_matrix']),
            data['num_vehicles'],
            data['depot']
        )
        
        routing = pywrapcp.RoutingModel(manager)
        
        # Create distance callback
        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return data['distance_matrix'][from_node][to_node]
        
        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
        
        # Add time windows constraint (optional)
        time_dimension_name = 'Time'
        routing.AddDimension(
            transit_callback_index,
            30,  # allow waiting time
            300,  # maximum time per vehicle (5 hours)
            False,  # Don't force start cumul to zero
            time_dimension_name
        )
        time_dimension = routing.GetDimensionOrDie(time_dimension_name)
        
        # Set search parameters
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.seconds = 30
        
        # Solve the problem
        solution = routing.SolveWithParameters(search_parameters)
        
        if solution:
            return self._extract_solution(responder, victims, manager, routing, solution)
        
        return None
    
    def _create_subset_distance_matrix(self, responder: Responder, victims: List[Victim]) -> List[List[int]]:
        """Create distance matrix for responder and selected victims"""
        # Create location list: [responder, victim1, victim2, ...]
        locations = [(responder.lat, responder.lon)]
        for victim in victims:
            locations.append((victim.lat, victim.lon))
        
        n_locations = len(locations)
        distance_matrix = []
        
        for i in range(n_locations):
            row = []
            for j in range(n_locations):
                if i == j:
                    row.append(0)
                else:
                    lat1, lon1 = locations[i]
                    lat2, lon2 = locations[j]
                    distance = self._calculate_distance(lat1, lon1, lat2, lon2)
                    row.append(int(distance))  # OR-Tools expects integers
            distance_matrix.append(row)
        
        return distance_matrix
    
    def _extract_solution(self, responder: Responder, victims: List[Victim], 
                         manager, routing, solution) -> RouteSolution:
        """Extract route solution from OR-Tools solution"""
        route = []
        total_distance = 0
        estimated_time = 0
        
        index = routing.Start(0)
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            
            if node_index > 0:  # Skip depot (responder location)
                victim_index = node_index - 1
                if victim_index < len(victims):
                    route.append(victims[victim_index].id)
            
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            
            # Calculate distance
            if not routing.IsEnd(index):
                distance = routing.GetArcCostForVehicle(previous_index, index, 0)
                total_distance += distance
                estimated_time += distance / (5000 / 3600)  # Convert to time
        
        # Calculate total time
        estimated_time_hours = estimated_time / 3600
        
        return RouteSolution(
            responder_id=responder.id,
            route=route,
            total_distance=total_distance,
            estimated_time=estimated_time_hours,
            victims_served=[v.id for v in victims if v.id in route]
        )
    
    def get_route_visualization_data(self, solution: RouteSolution) -> Dict:
        """Get data for route visualization"""
        if not solution:
            return {}
        
        # Get responder location
        responder = self.responders.get(solution.responder_id)
        if not responder:
            return {}
        
        # Build route coordinates
        route_coords = [(responder.lat, responder.lon)]
        
        for victim_id in solution.route:
            victim = self.victims.get(victim_id)
            if victim:
                route_coords.append((victim.lat, victim.lon))
        
        return {
            'responder_id': solution.responder_id,
            'route_coordinates': route_coords,
            'total_distance': solution.total_distance,
            'estimated_time': solution.estimated_time,
            'victims_count': len(solution.victims_served)
        }
    
    def update_route_dynamically(self, new_victim: Victim) -> List[RouteSolution]:
        """Update routes when new victim is detected"""
        # Add new victim
        self.add_victim(new_victim)
        
        # Re-optimize all routes
        return self.optimize_routes()
    
    def get_system_status(self) -> Dict:
        """Get overall system status"""
        total_victims = len(self.victims)
        available_responders = len([r for r in self.responders.values() if r.status == 'available'])
        
        # Calculate average survival likelihood
        if self.victims:
            avg_survival = np.mean([v.survival_likelihood for v in self.victims.values()])
        else:
            avg_survival = 0
        
        return {
            'total_victims': total_victims,
            'available_responders': available_responders,
            'average_survival_likelihood': avg_survival,
            'system_load': total_victims / max(available_responders, 1)
        }

def main():
    """Main function to test the route optimizer"""
    # Create route optimizer
    optimizer = RouteOptimizer()
    
    # Add sample responders
    responders = [
        Responder('responder-01', 34.0522, -118.2437, 5, 'available', []),
        Responder('responder-02', 34.0530, -118.2440, 5, 'available', []),
    ]
    
    for responder in responders:
        optimizer.add_responder(responder)
    
    # Add sample victims
    victims = [
        Victim('victim-001', 34.0525, -118.2440, 0.85, 'severe', datetime.now(), 0),
        Victim('victim-002', 34.0520, -118.2430, 0.92, 'minor', datetime.now(), 0),
        Victim('victim-003', 34.0535, -118.2445, 0.45, 'unconscious', datetime.now(), 0),
        Victim('victim-004', 34.0515, -118.2425, 0.78, 'severe', datetime.now(), 0),
    ]
    
    for victim in victims:
        optimizer.add_victim(victim)
    
    # Optimize routes
    print("Optimizing routes...")
    solutions = optimizer.optimize_routes()
    
    # Print results
    for solution in solutions:
        print(f"\nResponder {solution.responder_id}:")
        print(f"  Route: {solution.route}")
        print(f"  Total distance: {solution.total_distance:.0f} meters")
        print(f"  Estimated time: {solution.estimated_time:.2f} hours")
        print(f"  Victims served: {len(solution.victims_served)}")
    
    # Get system status
    status = optimizer.get_system_status()
    print(f"\nSystem Status:")
    print(f"  Total victims: {status['total_victims']}")
    print(f"  Available responders: {status['available_responders']}")
    print(f"  Average survival likelihood: {status['average_survival_likelihood']:.3f}")

if __name__ == "__main__":
    main()
