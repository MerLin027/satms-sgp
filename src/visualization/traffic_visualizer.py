"""
Traffic Visualizer Module

This module provides visualization components for traffic data and signal states.
It creates a simple ASCII-based visualization for the terminal.
"""

import os
import time
from datetime import datetime


class TrafficVisualizer:
    """
    A class to visualize traffic data and signal states in the terminal.
    """
    
    def __init__(self):
        """
        Initialize the visualizer with default values.
        """
        self.terminal_width = self._get_terminal_width()
        self.clear_screen_command = 'cls' if os.name == 'nt' else 'clear'
        
    def _get_terminal_width(self):
        """
        Get the terminal width for proper formatting.
        """
        try:
            return os.get_terminal_size().columns
        except (AttributeError, OSError):
            return 80  # Default width
    
    def clear_screen(self):
        """
        Clear the terminal screen.
        """
        os.system(self.clear_screen_command)
    
    def draw_header(self, strategy_name, simulation_time):
        """
        Draw the header section with simulation info.
        
        Args:
            strategy_name: Name of the active strategy
            simulation_time: Current simulation time in seconds
        """
        self.clear_screen()
        width = self.terminal_width
        
        # Draw top border
        print("=" * width)
        
        # Draw title
        title = f" TRAFFIC CONTROL SIMULATION - {strategy_name.upper()} STRATEGY "
        padding = (width - len(title)) // 2
        print(" " * padding + title)
        
        # Draw time
        time_str = f" Simulation Time: {simulation_time}s | {datetime.now().strftime('%H:%M:%S')} "
        padding = (width - len(time_str)) // 2
        print(" " * padding + time_str)
        
        # Draw bottom border
        print("=" * width)
        print()
    
    def draw_traffic_signals(self, current_phase, phase_state, time_remaining):
        """
        Draw a visual representation of the traffic signals.
        
        Args:
            current_phase: Current active phase (north_south or east_west)
            phase_state: State of the current phase (green or yellow)
            time_remaining: Time remaining for the current phase
        """
        width = self.terminal_width
        
        # Define colors based on state
        ns_color = "GREEN" if current_phase == "north_south" and phase_state == "green" else \
                   "YELLOW" if current_phase == "north_south" and phase_state == "yellow" else "RED"
        
        ew_color = "GREEN" if current_phase == "east_west" and phase_state == "green" else \
                   "YELLOW" if current_phase == "east_west" and phase_state == "yellow" else "RED"
        
        # Draw traffic light diagram
        print(f"{'TRAFFIC SIGNALS':^{width}}")
        print(f"{f'Current Phase: {current_phase.upper()} | State: {phase_state.upper()} | Remaining: {time_remaining}s':^{width}}")
        print()
        
        # North-South signals
        print(f"{'NORTH-SOUTH':^{width//2}}{'EAST-WEST':^{width//2}}")
        print(f"{ns_color:^{width//2}}{ew_color:^{width//2}}")
        
        # Draw the lights
        print(f"{self._draw_signal_light(ns_color):^{width//2}}{self._draw_signal_light(ew_color):^{width//2}}")
        print()
    
    def _draw_signal_light(self, color):
        """
        Draw an ASCII art traffic light.
        
        Args:
            color: The color of the signal light
        
        Returns:
            ASCII representation of the traffic light
        """
        if color == "RED":
            return "   [R]   \n   [•]   \n   [•]   "
        elif color == "YELLOW":
            return "   [•]   \n   [Y]   \n   [•]   "
        else:  # GREEN
            return "   [•]   \n   [•]   \n   [G]   "
    
    def draw_vehicle_data(self, vehicle_counts):
        """
        Draw the vehicle counts for each direction.
        
        Args:
            vehicle_counts: Dictionary of vehicle counts by direction
        """
        width = self.terminal_width
        
        print(f"{'VEHICLE COUNTS':^{width}}")
        print(f"{'-' * (width // 2):^{width}}")
        
        # Create a table
        directions = list(vehicle_counts.keys())
        half = len(directions) // 2
        
        # Print first half of directions
        for i in range(half):
            dir_name = directions[i].upper().replace('_', ' ')
            count = vehicle_counts[directions[i]]
            dir_name2 = directions[i + half].upper().replace('_', ' ')
            count2 = vehicle_counts[directions[i + half]]
            
            print(f"{dir_name:>15}: {count:<8}{dir_name2:>15}: {count2:<8}")
        
        # If odd number of directions, print the last one
        if len(directions) % 2 != 0:
            dir_name = directions[-1].upper().replace('_', ' ')
            count = vehicle_counts[directions[-1]]
            print(f"{dir_name:>15}: {count:<8}")
        
        print()
    
    def draw_statistics(self, avg_wait_time, throughput):
        """
        Draw statistics about the current traffic state.
        
        Args:
            avg_wait_time: Average wait time for vehicles
            throughput: Vehicles per minute passing through the intersection
        """
        width = self.terminal_width
        
        print(f"{'TRAFFIC STATISTICS':^{width}}")
        print(f"{'-' * (width // 2):^{width}}")
        
        print(f"{'Average Wait Time:':>25} {avg_wait_time:.2f}s")
        print(f"{'Throughput:':>25} {throughput:.2f} vehicles/min")
        print()
    
    def visualize_traffic_state(self, strategy_name, simulation_time, current_phase, 
                               phase_state, time_remaining, vehicle_counts,
                               avg_wait_time=0.0, throughput=0.0):
        """
        Visualize the complete traffic state.
        
        Args:
            strategy_name: Name of the active strategy
            simulation_time: Current simulation time
            current_phase: Current active phase
            phase_state: Current phase state
            time_remaining: Time remaining for the current phase
            vehicle_counts: Vehicle counts by direction
            avg_wait_time: Average wait time for vehicles
            throughput: Vehicles per minute passing through
        """
        self.draw_header(strategy_name, simulation_time)
        self.draw_traffic_signals(current_phase, phase_state, time_remaining)
        self.draw_vehicle_data(vehicle_counts)
        self.draw_statistics(avg_wait_time, throughput)
        
        # Add a timestamp at the bottom
        print(f"Last Updated: {datetime.now().strftime('%H:%M:%S')}")
    
    def animate_phase_change(self, from_phase, to_phase):
        """
        Create a simple animation for phase changes.
        
        Args:
            from_phase: The phase changing from
            to_phase: The phase changing to
        """
        # Simple animation showing the transition
        print(f"\nChanging phase: {from_phase.upper()} → {to_phase.upper()}")
        print("⏳ ", end="", flush=True)
        for _ in range(5):
            time.sleep(0.2)
            print("■", end="", flush=True)
        print(" Done!")
        time.sleep(0.5) 