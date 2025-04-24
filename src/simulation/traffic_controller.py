"""
Traffic Controller Module

This module provides the main controller for the traffic simulation.
It integrates traffic data, control strategies, and visualization.
"""

import time
import random
import logging
import sys
import os
from datetime import datetime
from threading import Event
from pathlib import Path

# Add the parent directory to the path to allow imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

from strategies.base_strategy import TrafficControlStrategy
from strategies.fixed_time_strategy import FixedTimeStrategy
from strategies.proportional_strategy import ProportionalStrategy
from strategies.webster_strategy import WebsterStrategy
from strategies.adaptive_strategy import AdaptiveStrategy
from data.data_generator import DataGenerator
from ml.predictor import TrafficPredictor
from visualization.traffic_visualizer import TrafficVisualizer
from utils.data_encoder import DataEncoder


class TrafficController:
    """
    Main controller for the traffic simulation.
    Manages the traffic flow, signal states, and visualization.
    """
    
    def __init__(self, strategy_name="proportional", visualization=True, random_events=True):
        """
        Initialize the traffic controller with the specified strategy.
        
        Args:
            strategy_name: Name of the strategy to use (default: "proportional")
            visualization: Whether to visualize the simulation (default: True)
            random_events: Whether to include random traffic events (default: True)
        """
        self.strategy_name = strategy_name.lower()
        self.visualization = visualization
        self.random_events = random_events
        
        # Initialize components
        self.data_generator = DataGenerator()
        self.predictor = TrafficPredictor()
        self.visualizer = TrafficVisualizer() if visualization else None
        
        # Set up strategy
        self.strategy = self._create_strategy(strategy_name)
        
        # Simulation state
        self.current_phase = "north_south"
        self.phase_state = "green"
        self.time_elapsed = 0
        self.phase_start_time = 0
        self.phase_duration = 30  # Default duration
        self.vehicle_counts = {
            "north_inbound": 0,
            "south_inbound": 0,
            "east_inbound": 0,
            "west_inbound": 0
        }
        self.processed_vehicles = 0
        self.total_wait_time = 0
        self.phase_history = []
        self.stop_event = Event()
        
        # Ensure results directory exists
        self.results_dir = Path(__file__).resolve().parent.parent.parent / "results"
        self.results_dir.mkdir(exist_ok=True)
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.results_dir / f"simulation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
                logging.StreamHandler() if not visualization else logging.NullHandler()
            ]
        )
        self.logger = logging.getLogger("TrafficController")
        
    def _create_strategy(self, strategy_name):
        """
        Create the appropriate strategy based on the name.
        
        Args:
            strategy_name: Name of the strategy to create
            
        Returns:
            An instance of the specified TrafficControlStrategy
        """
        strategies = {
            "fixed": FixedTimeStrategy(),
            "proportional": ProportionalStrategy(),
            "webster": WebsterStrategy(),
            "adaptive": AdaptiveStrategy()
        }
        
        if strategy_name not in strategies:
            self.logger.warning(f"Unknown strategy '{strategy_name}'. Using proportional strategy instead.")
            return strategies["proportional"]
        
        return strategies[strategy_name]
    
    def update_vehicle_counts(self):
        """
        Update the vehicle counts using the data generator.
        """
        # Generate vehicle counts for this time step
        counts = self.data_generator.generate_data()
        
        # Update the vehicle counts
        for direction, count in counts.items():
            self.vehicle_counts[direction] += count
        
        # Predict future traffic if using adaptive strategy
        if self.strategy_name == "adaptive":
            predicted_counts = self.predictor.predict(counts)
            self.strategy.update(counts, predicted_counts)
        else:
            self.strategy.update(counts)
        
        # Log the update
        self.logger.debug(f"Updated vehicle counts: {self.vehicle_counts}")
    
    def add_random_traffic_event(self):
        """
        Add a random traffic event (surge in traffic, roadblock, etc.).
        """
        if not self.random_events:
            return
        
        # Decide if a random event should occur (10% chance each update)
        if random.random() < 0.10:
            event_type = random.choice(["surge", "roadblock", "accident"])
            direction = random.choice(list(self.vehicle_counts.keys()))
            
            if event_type == "surge":
                # Add a surge of 10-30 vehicles in one direction
                surge_amount = random.randint(10, 30)
                self.vehicle_counts[direction] += surge_amount
                self.logger.info(f"Traffic event: Surge of {surge_amount} vehicles in {direction}")
                
                if self.visualization:
                    print(f"\n⚠️ TRAFFIC EVENT: Surge of {surge_amount} vehicles in {direction.upper()}")
                    time.sleep(1)
            
            elif event_type == "roadblock":
                # Slow down traffic by 50% in one direction
                self.vehicle_counts[direction] = max(0, int(self.vehicle_counts[direction] * 0.5))
                self.logger.info(f"Traffic event: Roadblock reducing traffic by 50% in {direction}")
                
                if self.visualization:
                    print(f"\n⚠️ TRAFFIC EVENT: Roadblock reducing traffic in {direction.upper()}")
                    time.sleep(1)
            
            elif event_type == "accident":
                # Block traffic completely in one direction for a time
                original_count = self.vehicle_counts[direction]
                self.vehicle_counts[direction] = 0
                self.logger.info(f"Traffic event: Accident blocking traffic in {direction}")
                
                if self.visualization:
                    print(f"\n⚠️ TRAFFIC EVENT: Accident blocking traffic in {direction.upper()}")
                    time.sleep(1)
                
                # After some time, restore traffic
                self.phase_history.append({
                    "time": self.time_elapsed,
                    "event": "accident_clear",
                    "direction": direction,
                    "count_restore": original_count
                })
    
    def process_vehicles(self):
        """
        Process vehicles passing through the intersection based on the current phase.
        """
        # Define directions active in each phase
        active_directions = {
            "north_south": ["north_inbound", "south_inbound"],
            "east_west": ["east_inbound", "west_inbound"]
        }
        
        # Calculate how many vehicles to process based on the current phase
        directions = active_directions[self.current_phase]
        
        # Green phase processes more vehicles than yellow
        flow_rate = 3 if self.phase_state == "green" else 1
        
        for direction in directions:
            to_process = min(self.vehicle_counts[direction], flow_rate)
            self.vehicle_counts[direction] -= to_process
            self.processed_vehicles += to_process
        
        # Calculate and add wait time for vehicles in the inactive directions
        inactive_directions = active_directions["east_west" if self.current_phase == "north_south" else "north_south"]
        
        for direction in inactive_directions:
            self.total_wait_time += self.vehicle_counts[direction]
        
        # Log the processed vehicles
        self.logger.debug(f"Processed vehicles for {self.current_phase}, {self.phase_state}: {flow_rate}/direction")
    
    def update_phase(self):
        """
        Update the traffic signal phase based on the current strategy.
        """
        # Check if phase duration has elapsed
        time_in_phase = self.time_elapsed - self.phase_start_time
        
        if time_in_phase >= self.phase_duration:
            # Record phase in history
            self.phase_history.append({
                "time": self.time_elapsed,
                "phase": self.current_phase,
                "state": self.phase_state,
                "duration": self.phase_duration,
                "vehicle_counts": self.vehicle_counts.copy()
            })
            
            # Update phase state
            if self.phase_state == "green":
                self.phase_state = "yellow"
                self.phase_duration = 5  # Fixed yellow phase duration
            else:  # Yellow -> Green for the other direction
                self.phase_state = "green"
                
                # Switch direction
                if self.current_phase == "north_south":
                    self.current_phase = "east_west"
                else:
                    self.current_phase = "north_south"
                
                # Get duration from strategy
                self.phase_duration = self.strategy.get_phase_duration(self.current_phase, self.vehicle_counts)
            
            # Reset phase start time
            self.phase_start_time = self.time_elapsed
            
            # Log the phase change
            self.logger.info(f"Phase changed to {self.current_phase}, {self.phase_state} for {self.phase_duration}s")
            
            # Animate the phase change if visualization is enabled
            if self.visualization and self.phase_state == "green":
                prev_phase = "east_west" if self.current_phase == "north_south" else "north_south"
                self.visualizer.animate_phase_change(prev_phase, self.current_phase)
    
    def calculate_statistics(self):
        """
        Calculate statistics about the current traffic state.
        
        Returns:
            Tuple of (average_wait_time, throughput)
        """
        if self.processed_vehicles == 0:
            avg_wait_time = 0
        else:
            avg_wait_time = self.total_wait_time / max(1, self.processed_vehicles)
        
        # Calculate throughput (vehicles per minute)
        throughput = (self.processed_vehicles / max(1, self.time_elapsed)) * 60
        
        return avg_wait_time, throughput
    
    def visualize_current_state(self):
        """
        Visualize the current state of the traffic controller.
        """
        if not self.visualization:
            return
        
        time_remaining = self.phase_duration - (self.time_elapsed - self.phase_start_time)
        avg_wait_time, throughput = self.calculate_statistics()
        
        self.visualizer.visualize_traffic_state(
            self.strategy_name,
            self.time_elapsed,
            self.current_phase,
            self.phase_state,
            time_remaining,
            self.vehicle_counts,
            avg_wait_time,
            throughput
        )
    
    def save_results(self):
        """
        Save the simulation results to a file.
        """
        # Create a result object
        result = {
            "strategy": self.strategy_name,
            "total_time": self.time_elapsed,
            "processed_vehicles": self.processed_vehicles,
            "final_vehicle_counts": self.vehicle_counts,
            "average_wait_time": self.calculate_statistics()[0],
            "throughput": self.calculate_statistics()[1],
            "phase_history": self.phase_history
        }
        
        # Save the result to a file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.results_dir / f"result_{self.strategy_name}_{timestamp}.json"
        
        with open(filename, "w") as f:
            f.write(DataEncoder().encode(result))
            
        self.logger.info(f"Results saved to {filename}")
        
        return filename
    
    def print_summary(self):
        """
        Print a summary of the simulation results.
        """
        avg_wait_time, throughput = self.calculate_statistics()
        
        print("\n" + "=" * 40)
        print(f"SIMULATION SUMMARY - {self.strategy_name.upper()} STRATEGY")
        print("=" * 40)
        print(f"Total simulation time: {self.time_elapsed} seconds")
        print(f"Total vehicles processed: {self.processed_vehicles}")
        print(f"Average wait time: {avg_wait_time:.2f} seconds")
        print(f"Throughput: {throughput:.2f} vehicles/minute")
        print(f"Final vehicle counts:")
        
        for direction, count in self.vehicle_counts.items():
            print(f"  {direction}: {count}")
        
        print(f"Phase changes: {len(self.phase_history)}")
        print("=" * 40)
    
    def stop_simulation(self):
        """
        Stop the simulation.
        """
        self.stop_event.set()
    
    def run_simulation(self, duration=300):
        """
        Run the traffic simulation for the specified duration.
        
        Args:
            duration: Duration of the simulation in seconds
            
        Returns:
            Dictionary containing the simulation results
        """
        self.logger.info(f"Starting simulation with {self.strategy_name} strategy for {duration}s")
        
        # Main simulation loop
        try:
            while self.time_elapsed < duration and not self.stop_event.is_set():
                # Update vehicle counts
                self.update_vehicle_counts()
                
                # Add random traffic events if enabled
                self.add_random_traffic_event()
                
                # Process vehicles through the intersection
                self.process_vehicles()
                
                # Update the phase if necessary
                self.update_phase()
                
                # Visualize the current state
                self.visualize_current_state()
                
                # Check for any accident clearance events
                for event in self.phase_history:
                    if event.get("event") == "accident_clear" and event["time"] + 20 <= self.time_elapsed:
                        self.vehicle_counts[event["direction"]] = event["count_restore"]
                        event["event"] = "accident_cleared"  # Mark as processed
                        self.logger.info(f"Accident cleared in {event['direction']}")
                
                # Increment the simulation time
                self.time_elapsed += 1
                
                # Sleep to control the simulation speed
                time.sleep(0.2 if self.visualization else 0.01)
                
        except KeyboardInterrupt:
            self.logger.info("Simulation stopped by user")
        finally:
            # Save the results
            results_file = self.save_results()
            
            # Print summary if visualization was disabled
            if not self.visualization:
                self.print_summary()
            else:
                print("\nSimulation completed!")
                print(f"Results saved to {results_file}")
            
            return {
                "strategy": self.strategy_name,
                "total_time": self.time_elapsed,
                "processed_vehicles": self.processed_vehicles,
                "average_wait_time": self.calculate_statistics()[0],
                "throughput": self.calculate_statistics()[1],
                "results_file": str(results_file)
            } 