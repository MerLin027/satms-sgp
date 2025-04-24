import numpy as np
import datetime
import random
import math
from datetime import datetime, timedelta

class DataGenerator:
    """
    Generates simulated traffic data with realistic patterns
    including rush hours, weekday/weekend variations, and random events.
    """
    
    def __init__(self, 
                 base_volume={
                    'north': 10, 
                    'south': 12, 
                    'east': 8, 
                    'west': 9
                 },
                 random_seed=None):
        """
        Initialize the data generator with base traffic volumes
        
        Args:
            base_volume: Dict of base vehicle counts for each direction
            random_seed: Seed for random number generator (for reproducibility)
        """
        if random_seed is not None:
            random.seed(random_seed)
            np.random.seed(random_seed)
            
        self.base_volume = base_volume
        self.directions = list(base_volume.keys())
        
        # Special events that can affect traffic (e.g. accidents, construction)
        self.active_events = {}
        
    def get_time_factors(self, timestamp=None):
        """
        Calculate traffic volume factors based on time of day and day of week
        
        Args:
            timestamp: Datetime object for which to generate factors
            
        Returns:
            dict: Factors for each direction
        """
        if timestamp is None:
            timestamp = datetime.now()
            
        # Extract hour and weekday
        hour = timestamp.hour
        weekday = timestamp.weekday()  # 0=Monday, 6=Sunday
        is_weekend = weekday >= 5
        
        # Base time factor is 1.0
        factors = {direction: 1.0 for direction in self.directions}
        
        # Time of day factors - Morning rush (7-9 AM), Evening rush (4-6 PM)
        if 7 <= hour < 9:  # Morning rush
            if not is_weekend:
                # On weekdays, more traffic going towards the center
                factors['south'] *= 1.8  # People driving into the city
                factors['east'] *= 1.5
                factors['north'] *= 0.9  # Less traffic leaving the city
                factors['west'] *= 0.8
        elif 16 <= hour < 18:  # Evening rush
            if not is_weekend:
                # On weekdays, more traffic leaving the center
                factors['north'] *= 1.8  # People driving out of the city
                factors['west'] *= 1.6
                factors['south'] *= 0.8  # Less traffic entering the city
                factors['east'] *= 0.9
        elif 22 <= hour or hour < 5:  # Night time
            # Reduced traffic at night
            for direction in factors:
                factors[direction] *= 0.3
        
        # Weekend factors
        if is_weekend:
            # Less commuter traffic but more leisure travel
            if 10 <= hour < 20:  # Daytime on weekends
                factors['north'] *= 1.3  # People going to recreational areas
                factors['west'] *= 1.2
            else:
                # Quieter at other times on weekends
                for direction in factors:
                    factors[direction] *= 0.7
        
        return factors
    
    def add_random_event(self, duration_minutes=30):
        """
        Add a random traffic event (accident, construction, etc.)
        that affects traffic in some directions
        
        Args:
            duration_minutes: How long the event will last
            
        Returns:
            dict: Event details
        """
        event_types = ['accident', 'construction', 'weather', 'event']
        event_type = random.choice(event_types)
        
        # Select which directions are affected
        affected_directions = random.sample(self.directions, random.randint(1, len(self.directions)))
        
        # Impact factors
        impact = {}
        for direction in self.directions:
            if direction in affected_directions:
                # Reduce traffic flow by 30-70%
                impact[direction] = random.uniform(0.3, 0.7)
            else:
                # Other directions might see slight increases
                impact[direction] = random.uniform(1.0, 1.2)
        
        # Set end time
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        
        # Create event object
        event = {
            'type': event_type,
            'affected_directions': affected_directions,
            'impact': impact,
            'end_time': end_time
        }
        
        # Store the event
        event_id = random.randint(10000, 99999)
        self.active_events[event_id] = event
        
        return {'id': event_id, **event}
    
    def remove_expired_events(self):
        """Remove events that have expired"""
        now = datetime.now()
        expired_events = [
            event_id for event_id, event in self.active_events.items()
            if event['end_time'] < now
        ]
        
        for event_id in expired_events:
            del self.active_events[event_id]
        
        return expired_events
    
    def get_traffic_data(self, timestamp=None, include_events=True):
        """
        Generate traffic data for the given timestamp
        
        Args:
            timestamp: Datetime for the data (default: current time)
            include_events: Whether to include impact of active events
            
        Returns:
            dict: Traffic data including vehicle counts for each direction
        """
        if timestamp is None:
            timestamp = datetime.now()
        
        # Get time-based factors
        time_factors = self.get_time_factors(timestamp)
        
        # Process any expired events
        if include_events:
            self.remove_expired_events()
        
        # Calculate base volumes with time factors
        result = {
            'timestamp': timestamp,
            'vehicle_counts': {}
        }
        
        for direction in self.directions:
            base = self.base_volume[direction]
            factor = time_factors[direction]
            
            # Apply event factors if needed
            if include_events and self.active_events:
                for event in self.active_events.values():
                    factor *= event['impact'].get(direction, 1.0)
            
            # Calculate mean volume
            mean_volume = base * factor
            
            # Add some random noise (±20%)
            noise_factor = random.uniform(0.8, 1.2)
            volume = math.floor(mean_volume * noise_factor)
            
            # Ensure volume is at least 1
            volume = max(1, volume)
            
            result['vehicle_counts'][direction] = volume
        
        # Add vehicle types (cars, trucks, buses, motorcycles)
        vehicle_types = {
            'cars': 0,
            'trucks': 0,
            'buses': 0,
            'motorcycles': 0
        }
        
        total_vehicles = sum(result['vehicle_counts'].values())
        
        # Distribute vehicles by type
        vehicle_types['cars'] = math.floor(total_vehicles * random.uniform(0.7, 0.8))
        vehicle_types['trucks'] = math.floor(total_vehicles * random.uniform(0.1, 0.15))
        vehicle_types['buses'] = math.floor(total_vehicles * random.uniform(0.03, 0.07))
        vehicle_types['motorcycles'] = total_vehicles - sum(vehicle_types.values())
        
        result['vehicle_types'] = vehicle_types
        
        # Add average speeds
        result['avg_speeds'] = {
            direction: max(10, random.normalvariate(40, 10)) 
            for direction in self.directions
        }
        
        # If there are events, add congestion factor
        if include_events and self.active_events:
            result['active_events'] = list(self.active_events.keys())
            
            # Calculate congestion levels (0-1 scale)
            congestion = {}
            for direction in self.directions:
                # Base congestion on traffic volume vs. capacity
                # Assume capacity is 20 vehicles
                capacity = 20
                congestion[direction] = min(1.0, result['vehicle_counts'][direction] / capacity)
                
                # Events increase congestion
                for event in self.active_events.values():
                    if direction in event['affected_directions']:
                        # Increase congestion more for affected directions
                        congestion[direction] = min(1.0, congestion[direction] * 1.5)
            
            result['congestion'] = congestion
        
        return result
    
    def generate_time_series(self, duration_minutes=60, interval_seconds=30):
        """
        Generate a time series of traffic data
        
        Args:
            duration_minutes: Duration of the time series in minutes
            interval_seconds: Interval between data points in seconds
            
        Returns:
            list: List of traffic data points
        """
        start_time = datetime.now()
        data_points = []
        
        # Add a random event with 30% probability
        if random.random() < 0.3:
            self.add_random_event(duration_minutes=random.randint(10, 30))
        
        # Generate data points
        for i in range(int(duration_minutes * 60 / interval_seconds)):
            timestamp = start_time + timedelta(seconds=i * interval_seconds)
            data = self.get_traffic_data(timestamp)
            data_points.append(data)
        
        return data_points 