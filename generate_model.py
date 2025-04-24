#!/usr/bin/env python
"""
Generate and save a traffic prediction model based on simulated data.
This script creates a model that can predict future traffic patterns.
"""

import os
import argparse
from datetime import datetime
import tensorflow as tf

from src.prediction.traffic_predictor import TrafficPredictor
from src.monitoring.data_generator import DataGenerator
from src.utils.data_utilities import save_data_to_json

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Generate a traffic prediction model')
    parser.add_argument('--epochs', type=int, default=20, help='Number of training epochs')
    parser.add_argument('--output', type=str, default='models/saved_models/traffic_lstm_model.h5',
                        help='Path to save the model')
    parser.add_argument('--sample-data', type=str, default='data/sample_traffic_data.json',
                        help='Path to save sample training data')
    args = parser.parse_args()
    
    print(f"=== Traffic Prediction Model Generator ===")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create directories if they don't exist
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    os.makedirs(os.path.dirname(args.sample_data), exist_ok=True)
    
    # Step 1: Generate simulated traffic data
    print("\nGenerating simulated traffic data...")
    generator = DataGenerator(random_seed=42)  # Use a fixed seed for reproducibility
    
    # Generate data for 7 days with 5-minute intervals
    # This gives 7 * 24 * 12 = 2016 data points
    training_data = generator.generate_time_series(
        duration_minutes=7*24*60,  # 7 days
        interval_seconds=5*60      # 5 minutes
    )
    
    print(f"Generated {len(training_data)} data points for training")
    
    # Save a sample of the training data
    print(f"Saving sample data to {args.sample_data}")
    save_data_to_json(training_data[:100], args.sample_data)
    
    # Step 2: Create and train the model
    print("\nCreating traffic prediction model...")
    predictor = TrafficPredictor()
    
    print(f"Training model with {args.epochs} epochs...")
    history = predictor.train(
        training_data,
        epochs=args.epochs,
        batch_size=32,
        validation_split=0.2
    )
    
    # Step 3: Save the model
    print(f"\nSaving model to {args.output}")
    predictor.save_model(args.output)
    
    # Step 4: Test the model with some predictions
    print("\nTesting model with predictions...")
    
    # Generate some test data (last hour with 5-minute intervals)
    test_data = generator.generate_time_series(
        duration_minutes=60,
        interval_seconds=5*60
    )
    
    # Make predictions for the next 6 time steps (30 minutes)
    predictions = predictor.predict_future(test_data, steps=6)
    
    print("\nSample predictions for the next 30 minutes:")
    for i, prediction in enumerate(predictions):
        time_str = prediction['timestamp'].strftime('%H:%M:%S')
        confidence = prediction['confidence'] * 100
        counts = prediction['vehicle_counts']
        total = sum(counts.values())
        
        print(f"Step {i+1} [{time_str}] (Confidence: {confidence:.1f}%):")
        for direction, count in sorted(counts.items()):
            print(f"  {direction.capitalize()}: {count} vehicles")
        print(f"  Total: {total} vehicles\n")
    
    print("Model generation completed successfully!")
    print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 40)

if __name__ == "__main__":
    main() 