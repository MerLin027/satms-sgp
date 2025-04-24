#!/usr/bin/env python
"""
Traffic Control Simulation Demo

This script demonstrates the different traffic control strategies
by simulating traffic flow and signal timing.

Usage:
    python simulate_traffic.py [strategy] [duration]
    
    strategy: fixed, proportional, webster, adaptive (default: proportional)
    duration: simulation duration in seconds (default: 300)
"""

import sys
import os
import json
import time
from datetime import datetime

from src.control.controller import TrafficController
from src.utils.data_utilities import DataEncoder

def print_simulation_summary(history):
    """
    Print a summary of the simulation results
    
    Args:
        history: List of phase changes during simulation
    """
    total_time = 0
    total_vehicles = 0
    phases_by_direction = {"north_south": 0, "east_west": 0}
    
    for entry in history:
        if entry["state"] == "green":
            total_time += entry["duration"]
            phases_by_direction[entry["phase"]] += 1
            
            # Count vehicles
            for direction, count in entry["vehicle_counts"].items():
                total_vehicles += count
    
    print("\n=== Simulation Summary ===")
    print(f"Total simulation time: {total_time} seconds")
    print(f"Total phase changes: {len(history)}")
    print(f"Total vehicles processed: {total_vehicles}")
    
    print("\nTime allocation:")
    ns_time = sum(entry["duration"] for entry in history 
                 if entry["phase"] == "north_south" and entry["state"] == "green")
    ew_time = sum(entry["duration"] for entry in history 
                 if entry["phase"] == "east_west" and entry["state"] == "green")
    
    print(f"  NORTH-SOUTH: {ns_time} seconds ({ns_time/total_time*100:.1f}%)")
    print(f"  EAST-WEST: {ew_time} seconds ({ew_time/total_time*100:.1f}%)")
    
    # Find the longest and shortest green phases
    green_phases = [entry for entry in history if entry["state"] == "green"]
    longest = max(green_phases, key=lambda x: x["duration"])
    shortest = min(green_phases, key=lambda x: x["duration"])
    
    print("\nPhase statistics:")
    print(f"  Longest green phase: {longest['phase'].upper()} for {longest['duration']} seconds")
    print(f"  Shortest green phase: {shortest['phase'].upper()} for {shortest['duration']} seconds")
    print("=========================")

def save_results(history, strategy_name):
    """
    Save simulation results to a file
    
    Args:
        history: Simulation history
        strategy_name: Name of the strategy used
    """
    # Create directory if it doesn't exist
    os.makedirs("results", exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"results/simulation_{strategy_name}_{timestamp}.json"
    
    # Save to file
    with open(filename, "w") as f:
        json.dump(history, f, cls=DataEncoder, indent=2)
    
    print(f"\nSimulation results saved to {filename}")

def main():
    # Parse command line arguments
    strategy = "proportional"  # default
    duration = 300  # default: 5 minutes
    
    if len(sys.argv) > 1:
        strategy = sys.argv[1].lower()
    
    if len(sys.argv) > 2:
        try:
            duration = int(sys.argv[2])
        except ValueError:
            print(f"Invalid duration: {sys.argv[2]}. Using default: 300 seconds")
            duration = 300
    
    # Print header
    print("=" * 60)
    print(f"TRAFFIC CONTROL SIMULATION - {strategy.upper()} STRATEGY")
    print("=" * 60)
    
    # Initialize controller with selected strategy
    controller = TrafficController(strategy_name=strategy)
    
    # Add a random traffic event with 50% probability
    if time.time() % 2 > 1:
        event = controller.add_random_event(duration_minutes=5)
        print(f"\nTraffic event added: {event['type']} affecting {', '.join(event['affected_directions'])}")
        print(f"Event impact: {', '.join([f'{k}: {v:.2f}' for k, v in event['impact'].items()])}")
    
    # Run simulation
    history = controller.start_simulation(duration_seconds=duration, update_interval=5)
    
    # Print summary
    print_simulation_summary(history)
    
    # Save results
    save_results(history, strategy)

if __name__ == "__main__":
    main() 