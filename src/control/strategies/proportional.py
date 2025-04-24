from src.control.strategies.base_strategy import TrafficControlStrategy

class ProportionalStrategy(TrafficControlStrategy):
    """
    Proportional Strategy: Allocates green time in proportion to the traffic volume in each direction.
    """
    
    def __init__(self):
        """Initialize the proportional strategy"""
        super().__init__(
            name="Proportional",
            description="Allocates green time proportionally to traffic volume"
        )
        self.cycle_length = 90  # Total cycle length in seconds
        self.min_green_ratio = 0.3  # Minimum ratio of time for any direction
    
    def set_cycle_length(self, cycle_length):
        """
        Set the total cycle length
        
        Args:
            cycle_length: Total cycle length in seconds
        """
        self.cycle_length = max(30, min(180, cycle_length))
    
    def calculate_phase_times(self, traffic_data):
        """
        Calculate phase times based on traffic volume
        
        Args:
            traffic_data: Current traffic data
            
        Returns:
            dict: Phase times for each direction pair
        """
        if not traffic_data or 'vehicle_counts' not in traffic_data:
            # Default to equal times if no data
            ns_green = ew_green = (self.cycle_length - 2 * self.yellow_time) / 2
            return {
                'north_south': {
                    'green': int(ns_green),
                    'yellow': self.yellow_time
                },
                'east_west': {
                    'green': int(ew_green),
                    'yellow': self.yellow_time
                }
            }
        
        # Get vehicle counts
        vehicle_counts = traffic_data['vehicle_counts']
        ns_count = vehicle_counts.get('north', 0) + vehicle_counts.get('south', 0)
        ew_count = vehicle_counts.get('east', 0) + vehicle_counts.get('west', 0)
        total_count = ns_count + ew_count
        
        # Calculate available green time
        available_green = self.cycle_length - 2 * self.yellow_time
        
        # Calculate proportional green times
        if total_count > 0:
            ns_ratio = ns_count / total_count
            ew_ratio = ew_count / total_count
            
            # Apply minimum ratio
            if ns_ratio < self.min_green_ratio:
                ns_ratio = self.min_green_ratio
                ew_ratio = 1 - self.min_green_ratio
            elif ew_ratio < self.min_green_ratio:
                ew_ratio = self.min_green_ratio
                ns_ratio = 1 - self.min_green_ratio
            
            ns_green = int(available_green * ns_ratio)
            ew_green = int(available_green * ew_ratio)
            
            # Ensure minimum green times
            ns_green = max(self.min_green_time, ns_green)
            ew_green = max(self.min_green_time, ew_green)
            
            # Ensure we don't exceed available time
            total_green = ns_green + ew_green
            if total_green > available_green:
                # Scale down proportionally
                ns_green = int(ns_green * available_green / total_green)
                ew_green = int(ew_green * available_green / total_green)
                
                # Final check for minimum times
                ns_green = max(self.min_green_time, ns_green)
                ew_green = max(self.min_green_time, ew_green)
        else:
            # Equal distribution if no vehicles
            ns_green = ew_green = available_green // 2
        
        return {
            'north_south': {
                'green': ns_green,
                'yellow': self.yellow_time
            },
            'east_west': {
                'green': ew_green,
                'yellow': self.yellow_time
            }
        }
    
    def get_info(self):
        """
        Get strategy info including cycle length
        
        Returns:
            dict: Strategy information
        """
        info = super().get_info()
        info.update({
            'cycle_length': self.cycle_length,
            'min_green_ratio': self.min_green_ratio
        })
        return info 