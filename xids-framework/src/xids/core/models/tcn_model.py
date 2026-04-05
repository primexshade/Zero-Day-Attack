"""
Temporal Convolutional Network (TCN) for sequence classification
Optimized for network traffic analysis
"""

import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, Model
from typing import Tuple, Dict, Any
import pickle
import os

from .base_model import BaseModel


class TemporalConvNetwork(BaseModel):
    """TCN model for real-time intrusion detection"""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize TCN model"""
        super().__init__(name="TCN", config=config)
        self.config = config or {}
        
    def build(self) -> None:
        """Build TCN architecture"""
        tcn_config = self.config.get("tcn", {})
        input_shape = tcn_config.get("input_shape", [None, 50])
        num_filters = tcn_config.get("num_filters", 64)
        kernel_size = tcn_config.get("kernel_size", 3)
        num_layers = tcn_config.get("num_layers", 3)
        dropout = tcn_config.get("dropout", 0.3)
        
        inputs = keras.Input(shape=input_shape)
        x = inputs
        
        # Temporal convolutional layers
        for i in range(num_layers):
            x = layers.Conv1D(
                filters=num_filters * (2 ** i),
                kernel_size=kernel_size,
                padding="causal",
                activation="relu",
                dilation_rate=2 ** i,
                name=f"tcn_conv_{i}"
            )(x)
            x = layers.Dropout(dropout)(x)
            x = layers.BatchNormalization()(x)
        
        # Global average pooling
        x = layers.GlobalAveragePooling1D()(x)
        
        # Dense layers
        x = layers.Dense(128, activation="relu", name="dense_1")(x)
        x = layers.Dropout(dropout)(x)
        x = layers.Dense(64, activation="relu", name="dense_2")(x)
        x = layers.Dropout(dropout)(x)
        
        # Output layer
        outputs = layers.Dense(1, activation="sigmoid", name="output")(x)
        
        self.model = Model(inputs=inputs, outputs=outputs, name="TCN")
        
        # Compile model
        self.model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=0.001),
            loss="binary_crossentropy",
            metrics=["accuracy", keras.metrics.Precision(), keras.metrics.Recall()]
        )

    def train(self, X_train: np.ndarray, y_train: np.ndarray,
              X_val: np.ndarray = None, y_val: np.ndarray = None) -> Dict:
        """Train TCN model"""
        if self.model is None:
            self.build()
        
        training_config = self.config.get("training", {})
        batch_size = training_config.get("batch_size", 32)
        epochs = training_config.get("num_epochs", 100)
        patience = training_config.get("early_stopping_patience", 10)
        
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor="val_loss",
                patience=patience,
                restore_best_weights=True
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor="val_loss",
                factor=0.5,
                patience=5,
                min_lr=0.00001
            )
        ]
        
        validation_data = None
        if X_val is not None and y_val is not None:
            validation_data = (X_val, y_val)
        
        history = self.model.fit(
            X_train, y_train,
            batch_size=batch_size,
            epochs=epochs,
            validation_data=validation_data,
            callbacks=callbacks,
            verbose=1
        )
        
        self.is_trained = True
        self.history = history.history
        return self.history

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions"""
        if self.model is None:
            raise RuntimeError("Model not built. Call build() first.")
        return self.model.predict(X, verbose=0)

    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
        """Evaluate model"""
        if self.model is None:
            raise RuntimeError("Model not built. Call build() first.")
        
        results = self.model.evaluate(X_test, y_test, verbose=0)
        metrics = {
            "loss": float(results[0]),
            "accuracy": float(results[1]),
            "precision": float(results[2]),
            "recall": float(results[3])
        }
        return metrics

    def save(self, filepath: str) -> None:
        """Save model"""
        if self.model is None:
            raise RuntimeError("No model to save.")
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        self.model.save(filepath)
        
    def load(self, filepath: str) -> None:
        """Load model"""
        self.model = keras.models.load_model(filepath)
        self.is_trained = True
