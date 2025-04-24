import time
from datetime import datetime, timedelta

from src.monitoring.data_generator import DataGenerator
from src.prediction.traffic_predictor import TrafficPredictor
from src.control.strategies.fixed_time import FixedTimeStrategy
from src.control.strategies.proportional import ProportionalStrategy
from src.control.strategies.webster import WebsterStrategy
from src.control.strategies.adaptive import AdaptiveStrategy

class TrafficController:
    """
    Central controller that coordinates traffic data, prediction,
    and signal timing strategies.
    """
    
    def __init__(self, strategy_name="proportional"):
        """
        Initialize the controller with the specified strategy
        
        Args:
            strategy_name: Name of the strategy to use (fixed, proportional, webster, adaptive)
        """
        # Initialize components
        self.data_generator = DataGenerator()
        self.predictor = None
        
        # Load predictor if available
        try:
            self.predictor = TrafficPredictor("models/saved_models/traffic_lstm_model.h5")
            self.prediction_available = True
        except:
            self.prediction_available = False
            print("Traffic prediction model not found. Predictions will not be available.")
        
        # Initialize strategies
        self.strategies = {
            "fixed": FixedTimeStrategy(),
            "proportional": ProportionalStrategy(),
            "webster": WebsterStrategy(),
            "adaptive": AdaptiveStrategy()
        }
        
        # Set active strategy
        self.set_strategy(strategy_name)
        
        # Current state
        self.current_data = None
        self.current_phase = "north_south"  # or "east_west"
        self.phase_end_time = None
        self.phase_history = []
        
    def set_strategy(self, strategy_name):
        """
        Set the active traffic control strategy
        
        Args:
            strategy_name: Name of the strategy to use
            
        Returns:
            bool: True if successful, False if strategy not found
        """
        if strategy_name.lower() in self.strategies:
            self.active_strategy = self.strategies[strategy_name.lower()]
            print(f"Strategy set to: {self.active_strategy.name}")
            return True
        else:
            print(f"Strategy '{strategy_name}' not found. Available strategies: {', '.join(self.strategies.keys())}")
            return False
    
    def get_current_data(self, use_generator=True):
        """
        Get current traffic data
        
        Args:
            use_generator: Whether to generate new data or use the last data
            
        Returns:
            dict: Current traffic data
        """
        if use_generator or self.current_data is None:
            self.current_data = self.data_generator.get_traffic_data()
            
        return self.current_data
    
    def calculate_signal_timings(self):
        """
        Calculate signal timing based on current data and active strategy
        
        Returns:
            dict: Signal timing for each direction
        """
        # Get current traffic data
        data = self.get_current_data()
        
        # Calculate timing using the active strategy
        return self.active_strategy.calculate_phase_times(data)
    
    def start_simulation(self, duration_seconds=300, update_interval=5):
        """
        Run a traffic signal simulation for the specified duration
        
        Args:
            duration_seconds: Duration of simulation in seconds
            update_interval: How often to update traffic data (seconds)
            
        Returns:
            list: History of phase changes during simulation
        """
        print(f"Starting simulation with {self.active_strategy.name} strategy")
        print(f"Duration: {duration_seconds} seconds, Update interval: {update_interval} seconds")
        
        start_time = datetime.now()
        end_time = start_time + timedelta(seconds=duration_seconds)
        next_update = start_time
        
        # Initial phase calculation
        timings = self.calculate_signal_timings()
        self.current_phase = "north_south"
        self.phase_end_time = start_time + timedelta(seconds=timings[self.current_phase]["green"])
        
        # Record initial state
        self.phase_history.append({
            "timestamp": start_time,
            "phase": self.current_phase,
            "state": "green",
            "duration": timings[self.current_phase]["green"],
            "vehicle_counts": self.current_data["vehicle_counts"].copy() if self.current_data else {}
        })
        
        print(f"Initial phase: {self.current_phase.upper()} GREEN for {timings[self.current_phase]['green']} seconds")
        
        # Simulation loop
        current_time = start_time
        while current_time < end_time:
            # Increment simulation time
            current_time += timedelta(seconds=1)
            
            # Update traffic data at intervals
            if current_time >= next_update:
                next_update = current_time + timedelta(seconds=update_interval)
                self.get_current_data(use_generator=True)
            
            # Check if current phase should end
            if current_time >= self.phase_end_time:
                # Switch to yellow
                yellow_duration = timings[self.current_phase]["yellow"]
                
                # Record yellow phase
                self.phase_history.append({
                    "timestamp": current_time,
                    "phase": self.current_phase,
                    "state": "yellow",
                    "duration": yellow_duration,
                    "vehicle_counts": self.current_data["vehicle_counts"].copy() if self.current_data else {}
                })
                
                print(f"{current_time.strftime('%H:%M:%S')} - {self.current_phase.upper()} YELLOW for {yellow_duration} seconds")
                
                # Advance time to end of yellow
                current_time += timedelta(seconds=yellow_duration)
                
                # Switch to next phase
                self.current_phase = "east_west" if self.current_phase == "north_south" else "north_south"
                
                # Recalculate timings if using adaptive strategy
                if self.active_strategy.name in ["Adaptive", "Webster"]:
                    self.get_current_data(use_generator=True)
                    timings = self.calculate_signal_timings()
                
                # Set end time for new phase
                self.phase_end_time = current_time + timedelta(seconds=timings[self.current_phase]["green"])
                
                # Record new phase
                self.phase_history.append({
                    "timestamp": current_time,
                    "phase": self.current_phase,
                    "state": "green", 
                    "duration": timings[self.current_phase]["green"],
                    "vehicle_counts": self.current_data["vehicle_counts"].copy() if self.current_data else {}
                })
                
                print(f"{current_time.strftime('%H:%M:%S')} - {self.current_phase.upper()} GREEN for {timings[self.current_phase]['green']} seconds")
            
            # In a real system, we would sleep here, but for simulation we'll continue
        
        print(f"Simulation completed. Total phases: {len(self.phase_history)}")
        return self.phase_history
    
    def get_strategy_info(self):
        """
        Get information about all available strategies
        
        Returns:
            dict: Information about each strategy
        """
        return {name: strategy.get_info() for name, strategy in self.strategies.items()}
    
    def add_random_event(self, duration_minutes=15):
        """
        Add a random traffic event to the simulation
        
        Args:
            duration_minutes: Duration of the event in minutes
            
        Returns:
            dict: Event details
        """
        return self.data_generator.add_random_event(duration_minutes) 