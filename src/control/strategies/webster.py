import math
from src.control.strategies.base_strategy import TrafficControlStrategy

class WebsterStrategy(TrafficControlStrategy):
    """
    Webster Strategy: Implements Webster's method for traffic signal timing.
    This is a well-established method in traffic engineering that minimizes 
    overall vehicle delay.
    """
    
    def __init__(self):
        """Initialize the Webster strategy"""
        super().__init__(
            name="Webster",
            description="Uses Webster's method to minimize overall vehicle delay"
        )
        # Default parameters
        self.saturation_flow = 1800  # vehicles per hour of green per lane
        self.lanes = {
            'north': 1,
            'south': 1,
            'east': 1,
            'west': 1
        }
        self.min_cycle_length = 30
        self.max_cycle_length = 180
        self.lost_time = 4  # lost time per phase (seconds)
    
    def set_saturation_flow(self, flow_rate):
        """
        Set the saturation flow rate
        
        Args:
            flow_rate: Saturation flow rate in vehicles per hour
        """
        self.saturation_flow = max(600, min(2400, flow_rate))
    
    def set_lanes(self, north=1, south=1, east=1, west=1):
        """
        Set the number of lanes for each direction
        
        Args:
            north: Number of lanes in north direction
            south: Number of lanes in south direction
            east: Number of lanes in east direction
            west: Number of lanes in west direction
        """
        self.lanes = {
            'north': max(1, north),
            'south': max(1, south),
            'east': max(1, east),
            'west': max(1, west)
        }
    
    def calculate_phase_times(self, traffic_data):
        """
        Calculate phase times using Webster's method
        
        Args:
            traffic_data: Current traffic data
            
        Returns:
            dict: Phase times for each direction pair
        """
        if not traffic_data or 'vehicle_counts' not in traffic_data:
            # Default to equal times if no data
            return {
                'north_south': {
                    'green': 30,
                    'yellow': self.yellow_time
                },
                'east_west': {
                    'green': 30,
                    'yellow': self.yellow_time
                }
            }
        
        # Convert traffic counts to flow rates (vehicles per hour)
        # Assuming traffic_data is a snapshot representing current flow
        # We scale it to hourly flow for Webster's calculations
        vehicle_counts = traffic_data['vehicle_counts']
        
        # Scale factor (assuming data represents 5-minute average)
        scale = 12  # 12 * 5 minutes = 60 minutes (1 hour)
        
        # Calculate flow rates for each direction
        flows = {
            'north': vehicle_counts.get('north', 0) * scale,
            'south': vehicle_counts.get('south', 0) * scale,
            'east': vehicle_counts.get('east', 0) * scale,
            'west': vehicle_counts.get('west', 0) * scale
        }
        
        # Calculate critical flow ratios for each phase
        ns_flow_ratio = max(
            flows['north'] / (self.saturation_flow * self.lanes['north']),
            flows['south'] / (self.saturation_flow * self.lanes['south'])
        )
        
        ew_flow_ratio = max(
            flows['east'] / (self.saturation_flow * self.lanes['east']),
            flows['west'] / (self.saturation_flow * self.lanes['west'])
        )
        
        # Sum of critical flow ratios
        total_flow_ratio = ns_flow_ratio + ew_flow_ratio
        
        # If no traffic, default to equal times
        if total_flow_ratio < 0.001:
            return {
                'north_south': {
                    'green': 30,
                    'yellow': self.yellow_time
                },
                'east_west': {
                    'green': 30,
                    'yellow': self.yellow_time
                }
            }
        
        # Calculate optimal cycle length using Webster's formula
        total_lost_time = 2 * self.lost_time  # lost time for the whole cycle
        
        # Webster's formula: C = (1.5L + 5) / (1 - Y)
        # where L is the total lost time and Y is the sum of critical flow ratios
        if total_flow_ratio < 0.95:  # Ensure we don't divide by near-zero
            cycle_length = (1.5 * total_lost_time + 5) / (1 - total_flow_ratio)
            cycle_length = max(self.min_cycle_length, min(self.max_cycle_length, cycle_length))
        else:
            # If demand approaches capacity, use maximum cycle length
            cycle_length = self.max_cycle_length
        
        # Calculate effective green times
        effective_green = cycle_length - total_lost_time
        
        # Allocate green time proportional to flow ratios
        if total_flow_ratio > 0:
            ns_green = effective_green * (ns_flow_ratio / total_flow_ratio)
            ew_green = effective_green * (ew_flow_ratio / total_flow_ratio)
        else:
            # Equal split if no traffic
            ns_green = ew_green = effective_green / 2
        
        # Convert to actual green times
        ns_green = max(self.min_green_time, int(ns_green))
        ew_green = max(self.min_green_time, int(ew_green))
        
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
        Get strategy info including Webster parameters
        
        Returns:
            dict: Strategy information
        """
        info = super().get_info()
        info.update({
            'saturation_flow': self.saturation_flow,
            'lanes': self.lanes,
            'lost_time': self.lost_time
        })
        return info 