from src.control.strategies.base_strategy import TrafficControlStrategy

class AdaptiveStrategy(TrafficControlStrategy):
    """
    Adaptive Strategy: A real-time adaptive traffic signal control strategy
    that adjusts signal timing based on current traffic conditions and trends.
    This strategy can respond to changing traffic patterns more dynamically
    than fixed or proportional strategies.
    """
    
    def __init__(self):
        """Initialize the adaptive strategy"""
        super().__init__(
            name="Adaptive",
            description="Dynamically adjusts signal timing based on current and historical traffic patterns"
        )
        # Default parameters
        self.max_cycle_length = 120
        self.responsiveness = 0.7  # How quickly to adjust to changing conditions (0-1)
        self.historical_weight = 0.3  # Weight for historical data vs current data
        
        # Tracking parameters
        self.previous_times = {
            'north_south': {
                'green': 30,
                'yellow': self.yellow_time
            },
            'east_west': {
                'green': 30,
                'yellow': self.yellow_time
            }
        }
        
        # Trend tracking (for recent traffic flow changes)
        self.trend_data = {
            'north': [],
            'south': [],
            'east': [],
            'west': []
        }
        self.max_trend_points = 5  # Number of historical points to track
    
    def set_responsiveness(self, value):
        """
        Set how responsive the system is to traffic changes
        
        Args:
            value: Responsiveness factor (0-1), where 1 is most responsive
        """
        self.responsiveness = max(0.1, min(1.0, value))
        self.historical_weight = 1.0 - self.responsiveness
    
    def update_trends(self, traffic_data):
        """
        Update trend data with new traffic information
        
        Args:
            traffic_data: Current traffic data
        """
        if not traffic_data or 'vehicle_counts' not in traffic_data:
            return
            
        vehicle_counts = traffic_data['vehicle_counts']
        
        # Update each direction's trend data
        for direction in ['north', 'south', 'east', 'west']:
            count = vehicle_counts.get(direction, 0)
            self.trend_data[direction].append(count)
            
            # Keep only the most recent points
            if len(self.trend_data[direction]) > self.max_trend_points:
                self.trend_data[direction].pop(0)
    
    def get_trend_factor(self, direction):
        """
        Calculate a trend factor for the given direction
        
        Args:
            direction: Traffic direction to analyze
            
        Returns:
            float: Factor representing trend (>1 means increasing traffic)
        """
        data = self.trend_data[direction]
        if len(data) < 2:
            return 1.0
            
        # Simple linear trend calculation
        latest = sum(data[-2:]) / 2  # Average of last 2 points
        earliest = sum(data[:2]) / 2  # Average of first 2 points
        
        if earliest == 0:
            return 1.0 if latest == 0 else 1.2  # Assume slight growth if no earlier data
            
        trend = latest / earliest
        
        # Limit extreme values
        return max(0.8, min(1.5, trend))
    
    def calculate_phase_times(self, traffic_data):
        """
        Calculate phase times based on current traffic and historical trends
        
        Args:
            traffic_data: Current traffic data
            
        Returns:
            dict: Phase times for each direction pair
        """
        # Update trend data with new traffic information
        self.update_trends(traffic_data)
        
        if not traffic_data or 'vehicle_counts' not in traffic_data:
            return self.previous_times
        
        vehicle_counts = traffic_data['vehicle_counts']
        
        # Calculate base demand for each direction pair
        ns_count = vehicle_counts.get('north', 0) + vehicle_counts.get('south', 0)
        ew_count = vehicle_counts.get('east', 0) + vehicle_counts.get('west', 0)
        
        # Get trend factors
        ns_trend = (self.get_trend_factor('north') + self.get_trend_factor('south')) / 2
        ew_trend = (self.get_trend_factor('east') + self.get_trend_factor('west')) / 2
        
        # Apply trend factors to counts
        ns_adjusted = ns_count * ns_trend
        ew_adjusted = ew_count * ew_trend
        
        total_adjusted = ns_adjusted + ew_adjusted
        
        # Calculate new target green times
        if total_adjusted > 0:
            # Allocate green time proportionally
            available_green = self.max_cycle_length - 2 * self.yellow_time
            
            ns_target_green = available_green * (ns_adjusted / total_adjusted)
            ew_target_green = available_green * (ew_adjusted / total_adjusted)
        else:
            # Equal split if no traffic
            ns_target_green = ew_target_green = (self.max_cycle_length - 2 * self.yellow_time) / 2
        
        # Ensure minimum green times
        ns_target_green = max(self.min_green_time, ns_target_green)
        ew_target_green = max(self.min_green_time, ew_target_green)
        
        # Blend with previous times based on responsiveness
        ns_green = (self.responsiveness * ns_target_green + 
                   self.historical_weight * self.previous_times['north_south']['green'])
        ew_green = (self.responsiveness * ew_target_green + 
                   self.historical_weight * self.previous_times['east_west']['green'])
        
        # Ensure integer values
        ns_green = int(ns_green)
        ew_green = int(ew_green)
        
        # Update previous times
        new_times = {
            'north_south': {
                'green': ns_green,
                'yellow': self.yellow_time
            },
            'east_west': {
                'green': ew_green,
                'yellow': self.yellow_time
            }
        }
        
        self.previous_times = new_times
        return new_times
    
    def get_info(self):
        """
        Get strategy info including adaptive parameters
        
        Returns:
            dict: Strategy information
        """
        info = super().get_info()
        info.update({
            'responsiveness': self.responsiveness,
            'historical_weight': self.historical_weight,
            'max_cycle_length': self.max_cycle_length
        })
        return info 