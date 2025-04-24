#!/usr/bin/env python
"""
Test script for traffic prediction model.
This script generates a dummy model if one doesn't exist,
then tests prediction functionality.
"""

import os
from src.prediction.traffic_predictor import TrafficPredictor
from src.monitoring.data_generator import DataGenerator
from src.utils.data_utilities import print_traffic_data, save_data_to_json

def main():
    print("=== Traffic Prediction Model Test ===")
    
    # Check if we have a model
    model_path = 'models/saved_models/traffic_lstm_model.h5'
    
    predictor = TrafficPredictor()
    
    if not os.path.exists(model_path):
        print(f"Model not found at {model_path}, generating a dummy model...")
        predictor.generate_dummy_model(model_path)
    else:
        print(f"Loading existing model from {model_path}")
        predictor.load_model(model_path)
    
    # Generate some test data
    print("\nGenerating test data...")
    generator = DataGenerator()
    test_data = generator.generate_time_series(
        duration_minutes=30,     # 30 minutes
        interval_seconds=60      # 1 minute intervals
    )
    
    print(f"Generated {len(test_data)} data points")
    
    # Show the last data point (current traffic)
    print("\nCurrent Traffic Data:")
    print_traffic_data(test_data[-1])
    
    # Make predictions
    print("\nMaking predictions for the next 15 minutes...")
    predictions = predictor.predict_future(test_data, steps=15)
    
    # Display predictions
    print("\nPredicted Traffic:")
    for i, prediction in enumerate(predictions[:5]):  # Show just first 5 for brevity
        minutes = i + 1
        confidence = prediction['confidence'] * 100
        
        print(f"\n--- Prediction for {minutes} minute{'s' if minutes > 1 else ''} ahead (Confidence: {confidence:.1f}%) ---")
        
        # Extract just the vehicle counts
        simple_data = {
            'timestamp': prediction['timestamp'],
            'vehicle_counts': prediction['vehicle_counts'],
            'confidence': prediction['confidence']
        }
        
        # Convert to a format similar to regular traffic data for printing
        for k in test_data[-1]:
            if k not in simple_data and k != 'timestamp':
                simple_data[k] = test_data[-1][k]
                
        print_traffic_data(simple_data)
    
    # Save predictions to file
    output_file = 'data/predictions.json'
    save_data_to_json(predictions, output_file)
    print(f"\nSaved all predictions to {output_file}")
    
    print("\nPrediction test completed successfully!")

if __name__ == "__main__":
    main() 