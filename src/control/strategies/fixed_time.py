from src.control.strategies.base_strategy import TrafficControlStrategy

class FixedTimeStrategy(TrafficControlStrategy):
    """
    Fixed Time Strategy: Uses predetermined fixed timing for traffic signals
    regardless of current traffic conditions.
    """
    
    def __init__(self):
        """Initialize the fixed time strategy"""
        super().__init__(
            name="Fixed Time",
            description="Uses predetermined fixed timing for traffic signals"
        )
        # Default fixed times
        self.ns_green_time = 30  # seconds
        self.ew_green_time = 30  # seconds
    
    def set_times(self, ns_green_time, ew_green_time):
        """
        Set custom green times
        
        Args:
            ns_green_time: Green time for north-south direction
            ew_green_time: Green time for east-west direction
        """
        self.ns_green_time = max(self.min_green_time, min(self.max_green_time, ns_green_time))
        self.ew_green_time = max(self.min_green_time, min(self.max_green_time, ew_green_time))
    
    def calculate_phase_times(self, traffic_data=None):
        """
        Calculate phase times (ignores traffic data)
        
        Args:
            traffic_data: Ignored, included for API compatibility
            
        Returns:
            dict: Phase times for each direction pair
        """
        # In fixed time, we ignore the traffic data and use predetermined times
        return {
            'north_south': {
                'green': self.ns_green_time,
                'yellow': self.yellow_time
            },
            'east_west': {
                'green': self.ew_green_time,
                'yellow': self.yellow_time
            }
        }
    
    def get_info(self):
        """
        Get strategy info including fixed times
        
        Returns:
            dict: Strategy information
        """
        info = super().get_info()
        info.update({
            'north_south_green_time': self.ns_green_time,
            'east_west_green_time': self.ew_green_time
        })
        return info 