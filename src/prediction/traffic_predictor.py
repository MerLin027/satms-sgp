import numpy as np
import os
import pickle
import json
from datetime import datetime, timedelta
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout

class TrafficPredictor:
    """
    Traffic prediction model that can be trained on traffic data
    and used to make future traffic predictions
    """
    
    def __init__(self, model_path=None):
        """
        Initialize traffic predictor with optional pre-trained model
        
        Args:
            model_path: Path to a saved model (optional)
        """
        self.model = None
        self.feature_scaler = None
        self.target_scaler = None
        self.input_shape = None
        self.directions = ['north', 'south', 'east', 'west']
        self.sequence_length = 10  # Use 10 time steps for prediction
        
        # Load model if provided
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
    
    def build_model(self, input_shape=(10, 4)):
        """
        Build a new LSTM model for traffic prediction
        
        Args:
            input_shape: Tuple of (sequence_length, features)
            
        Returns:
            The built model
        """
        self.input_shape = input_shape
        
        model = Sequential([
            LSTM(64, activation='relu', input_shape=input_shape, return_sequences=True),
            Dropout(0.2),
            LSTM(32, activation='relu'),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dense(len(self.directions))  # Output for each direction
        ])
        
        model.compile(
            optimizer='adam',
            loss='mse',
            metrics=['mae']
        )
        
        self.model = model
        return model
    
    def _preprocess_data(self, raw_data):
        """
        Convert raw traffic data to model input format
        
        Args:
            raw_data: List of raw traffic data points
            
        Returns:
            Numpy array of features ready for the model
        """
        # Extract vehicle counts for each direction
        features = np.zeros((len(raw_data), len(self.directions)))
        
        for i, data_point in enumerate(raw_data):
            for j, direction in enumerate(self.directions):
                features[i, j] = data_point['vehicle_counts'][direction]
        
        # Scale features if scaler exists
        if self.feature_scaler:
            features = self.feature_scaler.transform(features)
        
        return features
    
    def _create_sequences(self, features, sequence_length=None):
        """
        Create input sequences for the LSTM model
        
        Args:
            features: Feature array
            sequence_length: Length of sequences to create
            
        Returns:
            X, y arrays for training or prediction
        """
        if sequence_length is None:
            sequence_length = self.sequence_length
            
        X, y = [], []
        for i in range(len(features) - sequence_length):
            X.append(features[i:i + sequence_length])
            y.append(features[i + sequence_length])
            
        return np.array(X), np.array(y)
    
    def train(self, training_data, epochs=50, batch_size=32, validation_split=0.2):
        """
        Train the model on traffic data
        
        Args:
            training_data: List of traffic data points
            epochs: Number of training epochs
            batch_size: Batch size for training
            validation_split: Fraction of data to use for validation
            
        Returns:
            Training history
        """
        # Preprocess data
        features = self._preprocess_data(training_data)
        
        # Create sequences
        X, y = self._create_sequences(features)
        
        # Build model if not already built
        if self.model is None:
            self.build_model(input_shape=(X.shape[1], X.shape[2]))
        
        # Train the model
        history = self.model.fit(
            X, y,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=validation_split,
            verbose=1
        )
        
        return history
    
    def predict_next(self, recent_data):
        """
        Predict traffic for the next time step
        
        Args:
            recent_data: List of recent traffic data points
            
        Returns:
            Dict with predicted vehicle counts for each direction
        """
        if self.model is None:
            raise ValueError("Model hasn't been trained or loaded yet")
        
        # Preprocess data
        features = self._preprocess_data(recent_data)
        
        # Check if we have enough data points
        if len(features) < self.sequence_length:
            raise ValueError(f"Need at least {self.sequence_length} data points for prediction")
        
        # Use the most recent sequence
        input_sequence = features[-self.sequence_length:].reshape(1, self.sequence_length, -1)
        
        # Make prediction
        predicted_features = self.model.predict(input_sequence)[0]
        
        # Convert back to predictions
        predictions = {}
        for i, direction in enumerate(self.directions):
            # Round to nearest integer and ensure positive
            value = max(0, round(predicted_features[i]))
            predictions[direction] = int(value)
        
        return predictions
    
    def predict_future(self, recent_data, steps=5):
        """
        Predict traffic multiple steps into the future
        
        Args:
            recent_data: List of recent traffic data points
            steps: Number of future steps to predict
            
        Returns:
            List of predictions for future time steps
        """
        if self.model is None:
            raise ValueError("Model hasn't been trained or loaded yet")
        
        # Start with the known data
        features = self._preprocess_data(recent_data)
        working_data = features.copy()
        
        predictions = []
        last_time = recent_data[-1]['timestamp']
        interval = (last_time - recent_data[-2]['timestamp']).total_seconds()
        
        for step in range(steps):
            # Get the most recent sequence
            if len(working_data) < self.sequence_length:
                raise ValueError(f"Need at least {self.sequence_length} data points for prediction")
                
            input_sequence = working_data[-self.sequence_length:].reshape(1, self.sequence_length, -1)
            
            # Predict the next data point
            next_features = self.model.predict(input_sequence)[0]
            
            # Add to working data
            working_data = np.vstack([working_data, next_features])
            
            # Create prediction object
            prediction = {
                'timestamp': last_time + timedelta(seconds=interval * (step + 1)),
                'vehicle_counts': {}
            }
            
            # Fill in predictions
            for i, direction in enumerate(self.directions):
                # Round to nearest integer and ensure positive
                value = max(0, round(next_features[i]))
                prediction['vehicle_counts'][direction] = int(value)
            
            # Calculate confidence (decreases with each step into the future)
            prediction['confidence'] = max(0.95 - (step * 0.05), 0.5)  # From 95% to 50%
            
            predictions.append(prediction)
        
        return predictions
    
    def save_model(self, model_path):
        """
        Save the model to disk
        
        Args:
            model_path: Path to save the model
        """
        if self.model is None:
            raise ValueError("No model to save")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        
        # Save model
        self.model.save(model_path)
        print(f"Model saved to {model_path}")
    
    def load_model(self, model_path):
        """
        Load a model from disk
        
        Args:
            model_path: Path to the saved model
        """
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at {model_path}")
        
        # Load the model
        self.model = load_model(model_path)
        
        # Set input shape from the loaded model
        self.input_shape = self.model.layers[0].input_shape[1:]
        
        print(f"Model loaded from {model_path}")
        
    def generate_dummy_model(self, save_path='models/saved_models/traffic_lstm_model.h5'):
        """
        Generate a dummy model trained on random data
        Useful for testing when no real data is available
        
        Args:
            save_path: Path to save the generated model
            
        Returns:
            The trained model
        """
        # Generate dummy training data
        from src.monitoring.data_generator import DataGenerator
        
        print("Generating dummy training data...")
        generator = DataGenerator()
        
        # Generate data for 24 hours with 5-minute intervals
        # This gives 24 * 12 = 288 data points
        dummy_data = generator.generate_time_series(
            duration_minutes=24*60,  # 24 hours
            interval_seconds=5*60    # 5 minutes
        )
        
        print(f"Generated {len(dummy_data)} data points for training")
        
        # Train a model on this dummy data
        print("Training dummy model...")
        self.train(
            dummy_data,
            epochs=10,
            batch_size=16,
            validation_split=0.2
        )
        
        # Save the model
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        self.save_model(save_path)
        
        return self.model 