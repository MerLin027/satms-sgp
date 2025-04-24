class TrafficControlStrategy:
    """Base class for all traffic control strategies"""
    
    def __init__(self, name, description):
        """
        Initialize the strategy
        
        Args:
            name: Strategy name
            description: Strategy description
        """
        self.name = name
        self.description = description
        self.min_green_time = 5  # Minimum time in seconds for green light
        self.max_green_time = 60  # Maximum time in seconds for green light
        self.yellow_time = 3  # Time in seconds for yellow light
        self.directions = ['north', 'south', 'east', 'west']
        
    def calculate_phase_times(self, traffic_data):
        """
        Calculate traffic light phase times based on traffic data
        
        Args:
            traffic_data: Current traffic data
            
        Returns:
            dict: Phase times for each direction
        """
        raise NotImplementedError("Subclasses must implement this method")
    
    def get_info(self):
        """
        Get information about the strategy
        
        Returns:
            dict: Strategy information
        """
        return {
            'name': self.name,
            'description': self.description,
            'min_green_time': self.min_green_time,
            'max_green_time': self.max_green_time,
            'yellow_time': self.yellow_time
        } 