#!/usr/bin/env python3
"""
Traffic Control Simulation Runner

This script runs traffic control simulations with different strategies.
"""

import os
import sys
import argparse
from pathlib import Path

# Add the parent directory to the path to allow imports
sys.path.append(str(Path(__file__).resolve().parent))

from simulation.traffic_controller import TrafficController


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run traffic control simulation")
    
    parser.add_argument(
        "--strategy", 
        type=str, 
        default="proportional",
        choices=["fixed", "proportional", "webster", "adaptive"],
        help="Traffic control strategy to use"
    )
    
    parser.add_argument(
        "--duration", 
        type=int, 
        default=300,
        help="Duration of the simulation in seconds"
    )
    
    parser.add_argument(
        "--no-viz", 
        action="store_true",
        help="Disable visualization"
    )
    
    parser.add_argument(
        "--no-events", 
        action="store_true",
        help="Disable random traffic events"
    )
    
    parser.add_argument(
        "--compare", 
        action="store_true",
        help="Run all strategies and compare results"
    )
    
    return parser.parse_args()


def run_single_simulation(strategy, duration, visualization, random_events):
    """Run a single simulation with the specified parameters."""
    controller = TrafficController(
        strategy_name=strategy,
        visualization=visualization,
        random_events=random_events
    )
    
    return controller.run_simulation(duration=duration)


def compare_strategies(duration, visualization, random_events):
    """Run simulations with all strategies and compare results."""
    strategies = ["fixed", "proportional", "webster", "adaptive"]
    results = []
    
    print(f"\nRunning comparison of all strategies ({duration}s each)...\n")
    
    for strategy in strategies:
        print(f"Running {strategy.upper()} strategy...")
        result = run_single_simulation(
            strategy=strategy,
            duration=duration,
            visualization=False,  # Disable visualization for comparison
            random_events=random_events
        )
        results.append(result)
    
    # Print comparison table
    print("\n" + "=" * 80)
    print("STRATEGY COMPARISON RESULTS")
    print("=" * 80)
    
    print(f"{'STRATEGY':<12} | {'PROCESSED':<10} | {'AVG WAIT TIME':<15} | {'THROUGHPUT':<12}")
    print("-" * 80)
    
    for result in results:
        print(
            f"{result['strategy']:<12} | "
            f"{result['processed_vehicles']:<10} | "
            f"{result['average_wait_time']:.2f}s{' ' * (14 - len(f'{result['average_wait_time']:.2f}s'))} | "
            f"{result['throughput']:.2f}/min"
        )
    
    print("=" * 80)
    
    # Determine the best strategy
    best_throughput = max(results, key=lambda x: x['throughput'])
    best_wait_time = min(results, key=lambda x: x['average_wait_time'])
    
    print(f"\nBest throughput: {best_throughput['strategy'].upper()} strategy "
          f"({best_throughput['throughput']:.2f} vehicles/min)")
    
    print(f"Best wait time: {best_wait_time['strategy'].upper()} strategy "
          f"({best_wait_time['average_wait_time']:.2f} seconds)")
    
    print("\nResults saved to the 'results' directory.")
    

def main():
    """Main function to run the simulation."""
    args = parse_arguments()
    
    # Create results directory if it doesn't exist
    results_dir = Path(__file__).resolve().parent.parent / "results"
    results_dir.mkdir(exist_ok=True)
    
    if args.compare:
        compare_strategies(
            duration=args.duration,
            visualization=False,
            random_events=not args.no_events
        )
    else:
        run_single_simulation(
            strategy=args.strategy,
            duration=args.duration,
            visualization=not args.no_viz,
            random_events=not args.no_events
        )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSimulation interrupted by user. Exiting...")
        sys.exit(0) 