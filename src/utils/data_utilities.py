import json
from datetime import datetime
import time

class DataEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects"""
    
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)
        
def print_traffic_data(data):
    """
    Pretty print traffic data
    
    Args:
        data: Traffic data dictionary
    """
    print("\n===== TRAFFIC DATA =====")
    print(f"Timestamp: {data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nVehicle Counts:")
    
    for direction, count in data['vehicle_counts'].items():
        print(f"  {direction.capitalize()}: {count} vehicles")
        
    print("\nVehicle Types:")
    for type_name, count in data['vehicle_types'].items():
        print(f"  {type_name.capitalize()}: {count}")
        
    print("\nAverage Speeds (km/h):")
    for direction, speed in data['avg_speeds'].items():
        print(f"  {direction.capitalize()}: {speed:.1f}")
    
    if 'congestion' in data:
        print("\nCongestion Levels (0-1):")
        for direction, level in data['congestion'].items():
            # Convert to percentage
            percentage = level * 100
            status = "Heavy" if level > 0.7 else "Moderate" if level > 0.4 else "Light"
            print(f"  {direction.capitalize()}: {percentage:.1f}% ({status})")
            
    if 'active_events' in data and data['active_events']:
        print("\nActive Events: ", ", ".join([str(e) for e in data['active_events']]))
        
    print("=======================\n")
    
def save_data_to_json(data, filename):
    """
    Save traffic data to a JSON file
    
    Args:
        data: Traffic data (single point or list)
        filename: Output filename
    """
    with open(filename, 'w') as f:
        json.dump(data, f, cls=DataEncoder, indent=2)
    print(f"Data saved to {filename}")

def demo_data_generator():
    """
    Run a demo of the data generator to show its capabilities
    """
    from src.monitoring.data_generator import DataGenerator
    
    # Create data generator
    generator = DataGenerator()
    
    # Generate current traffic data
    current_data = generator.get_traffic_data()
    print_traffic_data(current_data)
    
    # Simulate a traffic incident
    print("Adding a traffic incident...")
    event = generator.add_random_event(duration_minutes=30)
    print(f"Event created: {event['type']} affecting {', '.join(event['affected_directions'])}")
    
    # Get data with the incident
    time.sleep(1)  # Small pause for demonstration
    incident_data = generator.get_traffic_data()
    print_traffic_data(incident_data)
    
    # Generate a time series
    print("Generating a 10-minute time series (20 data points)...")
    time_series = generator.generate_time_series(duration_minutes=10, interval_seconds=30)
    print(f"Generated {len(time_series)} data points")
    
    # Save to JSON
    save_data_to_json(time_series, "traffic_data_series.json")
    
    return time_series

if __name__ == "__main__":
    # Run the demo if this file is executed directly
    demo_data_generator() 