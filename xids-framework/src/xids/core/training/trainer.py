"""
Unified training pipeline for all X-IDS models.

This module provides a complete training framework supporting:
- Multiple model types (TCN, VAE, Random Forest)
- Configurable hyperparameters
- Training callbacks (early stopping, LR scheduling, checkpointing)
- Loss tracking and visualization
- Cross-validation support
- Model serialization and restoration

Classes:
    ModelTrainer: Unified trainer for all model types
    TrainingCallback: Base callback interface
    EarlyStoppingCallback: Stop training when validation loss plateaus
    LearningRateScheduler: Adjust learning rate during training
"""

import numpy as np
import pandas as pd
import tensorflow as tf
import torch
from pathlib import Path
from typing import Dict, Optional, Tuple, List, Union, Callable
import logging
import json
from datetime import datetime
import pickle
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class TrainingCallback(ABC):
    """Base class for training callbacks."""
    
    @abstractmethod
    def on_epoch_start(self, epoch: int, logs: Dict) -> None:
        """Called at the start of each epoch."""
        pass
    
    @abstractmethod
    def on_epoch_end(self, epoch: int, logs: Dict) -> None:
        """Called at the end of each epoch."""
        pass
    
    @abstractmethod
    def on_training_start(self) -> None:
        """Called at the start of training."""
        pass
    
    @abstractmethod
    def on_training_end(self, logs: Dict) -> None:
        """Called at the end of training."""
        pass


class EarlyStoppingCallback(TrainingCallback):
    """
    Stop training when monitored metric stops improving.
    
    Args:
        monitor: Metric to monitor (e.g., 'val_loss')
        patience: Number of epochs to wait for improvement
        mode: 'min' (lower is better) or 'max' (higher is better)
        restore_best_weights: Restore weights from best epoch
    """
    
    def __init__(self, 
                 monitor: str = 'val_loss',
                 patience: int = 10,
                 mode: str = 'min',
                 restore_best_weights: bool = True,
                 min_delta: float = 0.001):
        """Initialize early stopping callback."""
        self.monitor = monitor
        self.patience = patience
        self.mode = mode
        self.restore_best_weights = restore_best_weights
        self.min_delta = min_delta
        
        self.wait_count = 0
        self.best_value = float('inf') if mode == 'min' else float('-inf')
        self.best_epoch = 0
        self.best_weights = None
        self.stopped = False
    
    def on_epoch_start(self, epoch: int, logs: Dict) -> None:
        """Called at epoch start."""
        pass
    
    def on_epoch_end(self, epoch: int, logs: Dict) -> None:
        """Check if should stop."""
        current_value = logs.get(self.monitor, self.best_value)
        
        if self.mode == 'min':
            improved = current_value < self.best_value - self.min_delta
        else:
            improved = current_value > self.best_value + self.min_delta
        
        if improved:
            self.best_value = current_value
            self.best_epoch = epoch
            self.wait_count = 0
            logger.info(f"EarlyStopping: {self.monitor} improved to {current_value:.4f}")
        else:
            self.wait_count += 1
            if self.wait_count >= self.patience:
                self.stopped = True
                logger.info(f"EarlyStopping: Stopping at epoch {epoch} after "
                           f"{self.patience} epochs without improvement")
    
    def on_training_start(self) -> None:
        """Called at training start."""
        self.wait_count = 0
        self.best_value = float('inf') if self.mode == 'min' else float('-inf')
        self.stopped = False
    
    def on_training_end(self, logs: Dict) -> None:
        """Called at training end."""
        logs['early_stopping_epoch'] = self.best_epoch
        logs['early_stopping_value'] = self.best_value


class LearningRateScheduler(TrainingCallback):
    """
    Adjust learning rate during training.
    
    Args:
        schedule: Function(epoch) -> new_lr
        verbose: Log learning rate changes
    """
    
    def __init__(self, schedule: Callable, verbose: bool = True):
        """Initialize learning rate scheduler."""
        self.schedule = schedule
        self.verbose = verbose
        self.current_lr = None
    
    def on_epoch_start(self, epoch: int, logs: Dict) -> None:
        """Adjust learning rate."""
        new_lr = self.schedule(epoch)
        if new_lr != self.current_lr:
            self.current_lr = new_lr
            if self.verbose:
                logger.info(f"Learning rate changed to {new_lr:.6f}")
    
    def on_epoch_end(self, epoch: int, logs: Dict) -> None:
        """Called at epoch end."""
        pass
    
    def on_training_start(self) -> None:
        """Called at training start."""
        self.current_lr = self.schedule(0)
    
    def on_training_end(self, logs: Dict) -> None:
        """Called at training end."""
        pass


class ModelTrainer:
    """
    Unified trainer for all X-IDS models (TCN, VAE, Random Forest).
    
    Features:
    - Model-agnostic training loop
    - Callback support (early stopping, LR scheduling)
    - Loss and metric tracking
    - Model checkpointing and restoration
    - Training history serialization
    - Cross-validation support
    
    Attributes:
        model: The model to train
        config: Training configuration
        history: Dictionary with loss/metric history
        callbacks: List of training callbacks
        best_model_path: Path to best model checkpoint
    """
    
    def __init__(self, 
                 model,
                 config: Dict = None,
                 callbacks: List[TrainingCallback] = None):
        """
        Initialize trainer.
        
        Args:
            model: Model instance (TCN, VAE, or RF)
            config: Training configuration dictionary
            callbacks: List of callbacks
        """
        self.model = model
        self.config = config or {}
        self.callbacks = callbacks or []
        self.history: Dict[str, List[float]] = {}
        self.best_model_path: Optional[str] = None
        
        # Training state
        self.current_epoch = 0
        self.training_started = False
    
    def add_callback(self, callback: TrainingCallback) -> None:
        """Add a callback to the trainer."""
        self.callbacks.append(callback)
    
    def train_tcn(self,
                 X_train: np.ndarray,
                 y_train: np.ndarray,
                 X_val: Optional[np.ndarray] = None,
                 y_val: Optional[np.ndarray] = None,
                 **kwargs) -> Dict:
        """
        Train Temporal Convolutional Network.
        
        Args:
            X_train: Training features
            y_train: Training labels
            X_val: Validation features
            X_val: Validation labels
            **kwargs: Additional training arguments
            
        Returns:
            Training history dictionary
        """
        logger.info("Starting TCN training...")
        
        train_config = self.config.get("training", {})
        tcn_config = self.config.get("tcn", {})
        
        # Prepare data
        if len(X_train.shape) == 2:
            # Reshape (N, features) -> (N//window, window, features)
            window_size = tcn_config.get("window_size", 30)
            X_train = self._create_sequences(X_train, window_size)
            if X_val is not None:
                X_val = self._create_sequences(X_val, window_size)
        
        # Configure model (assuming it's a Keras/TensorFlow model)
        optimizer = tf.keras.optimizers.Adam(
            learning_rate=train_config.get("learning_rate", 0.001)
        )
        
        loss_fn = tf.keras.losses.BinaryCrossentropy()
        
        self.model.compile(
            optimizer=optimizer,
            loss=loss_fn,
            metrics=['accuracy', tf.keras.metrics.Precision(), 
                    tf.keras.metrics.Recall()]
        )
        
        # Prepare callbacks for Keras
        keras_callbacks = []
        
        early_stopping = tf.keras.callbacks.EarlyStopping(
            monitor='val_loss' if X_val is not None else 'loss',
            patience=train_config.get("early_stopping_patience", 10),
            restore_best_weights=True
        )
        keras_callbacks.append(early_stopping)
        
        # Learning rate scheduler
        def lr_schedule(epoch):
            initial_lr = train_config.get("learning_rate", 0.001)
            decay = train_config.get("lr_decay", 0.1)
            return initial_lr * (decay ** (epoch // 10))
        
        lr_scheduler = tf.keras.callbacks.LearningRateScheduler(lr_schedule)
        keras_callbacks.append(lr_scheduler)
        
        # Train model
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val) if X_val is not None else None,
            epochs=train_config.get("num_epochs", 50),
            batch_size=train_config.get("batch_size", 32),
            callbacks=keras_callbacks,
            verbose=train_config.get("verbose", 1)
        )
        
        self.history = history.history
        logger.info(f"TCN training completed. Final loss: {self.history['loss'][-1]:.4f}")
        
        return self.history
    
    def train_vae(self,
                 X_train: np.ndarray,
                 y_train: Optional[np.ndarray] = None,
                 X_val: Optional[np.ndarray] = None,
                 **kwargs) -> Dict:
        """
        Train Variational Autoencoder.
        
        Args:
            X_train: Training features
            y_train: Training labels (unused, for consistency)
            X_val: Validation features
            **kwargs: Additional training arguments
            
        Returns:
            Training history dictionary
        """
        logger.info("Starting VAE training...")
        
        train_config = self.config.get("training", {})
        vae_config = self.config.get("autoencoder", {})
        
        # Configure model
        optimizer = tf.keras.optimizers.Adam(
            learning_rate=train_config.get("learning_rate", 0.001)
        )
        
        self.model.compile(optimizer=optimizer)
        
        # Prepare callbacks
        keras_callbacks = []
        
        early_stopping = tf.keras.callbacks.EarlyStopping(
            monitor='val_loss' if X_val is not None else 'loss',
            patience=train_config.get("early_stopping_patience", 10),
            restore_best_weights=True
        )
        keras_callbacks.append(early_stopping)
        
        # Train model
        history = self.model.fit(
            X_train, X_train,  # VAE trains to reconstruct input
            validation_data=(X_val, X_val) if X_val is not None else None,
            epochs=train_config.get("num_epochs", 50),
            batch_size=train_config.get("batch_size", 32),
            callbacks=keras_callbacks,
            verbose=train_config.get("verbose", 1)
        )
        
        self.history = history.history
        logger.info(f"VAE training completed. Final loss: {self.history['loss'][-1]:.4f}")
        
        return self.history
    
    def train_rf(self,
                X_train: np.ndarray,
                y_train: np.ndarray,
                X_val: Optional[np.ndarray] = None,
                y_val: Optional[np.ndarray] = None,
                **kwargs) -> Dict:
        """
        Train Random Forest baseline model.
        
        Args:
            X_train: Training features
            y_train: Training labels
            X_val: Validation features (unused)
            y_val: Validation labels (unused)
            **kwargs: Additional training arguments
            
        Returns:
            Training history dictionary
        """
        logger.info("Starting Random Forest training...")
        
        rf_config = self.config.get("random_forest", {})
        
        # Train model
        self.model.fit(X_train, y_train)
        
        # Evaluate on validation if provided
        self.history = {
            'train_accuracy': [self.model.score(X_train, y_train)],
            'train_loss': []
        }
        
        if X_val is not None and y_val is not None:
            self.history['val_accuracy'] = [self.model.score(X_val, y_val)]
        
        logger.info(f"Random Forest training completed. "
                   f"Train accuracy: {self.history['train_accuracy'][0]:.4f}")
        
        return self.history
    
    def train(self,
             X_train: np.ndarray,
             y_train: np.ndarray,
             X_val: Optional[np.ndarray] = None,
             y_val: Optional[np.ndarray] = None,
             model_type: str = "tcn",
             **kwargs) -> Dict:
        """
        Train model with automatic model type detection.
        
        Args:
            X_train: Training features
            y_train: Training labels
            X_val: Validation features
            y_val: Validation labels
            model_type: Type of model ('tcn', 'vae', 'rf')
            **kwargs: Additional arguments
            
        Returns:
            Training history
        """
        self.training_started = True
        
        # Call appropriate training method
        if model_type.lower() == "tcn":
            return self.train_tcn(X_train, y_train, X_val, y_val, **kwargs)
        elif model_type.lower() == "vae" or model_type.lower() == "autoencoder":
            return self.train_vae(X_train, y_train, X_val, **kwargs)
        elif model_type.lower() == "rf" or model_type.lower() == "random_forest":
            return self.train_rf(X_train, y_train, X_val, y_val, **kwargs)
        else:
            raise ValueError(f"Unknown model type: {model_type}")
    
    def _create_sequences(self, X: np.ndarray, seq_length: int) -> np.ndarray:
        """
        Create sequences for TCN/LSTM models.
        
        Args:
            X: Input array (N, features)
            seq_length: Sequence length
            
        Returns:
            Array (N_new, seq_length, features)
        """
        sequences = []
        for i in range(len(X) - seq_length + 1):
            sequences.append(X[i:i + seq_length])
        
        return np.array(sequences)
    
    def save_history(self, filepath: str) -> None:
        """
        Save training history to JSON.
        
        Args:
            filepath: Path to save history
        """
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        # Convert numpy arrays to lists for JSON serialization
        history_dict = {
            k: v.tolist() if isinstance(v, np.ndarray) else v 
            for k, v in self.history.items()
        }
        
        with open(filepath, 'w') as f:
            json.dump(history_dict, f, indent=2)
        
        logger.info(f"Training history saved to {filepath}")
    
    def get_training_stats(self) -> Dict:
        """
        Get summary statistics from training.
        
        Returns:
            Dictionary with training statistics
        """
        if not self.history:
            return {}
        
        stats = {}
        for metric_name, values in self.history.items():
            if isinstance(values, list) and len(values) > 0:
                stats[f"{metric_name}_final"] = values[-1]
                stats[f"{metric_name}_best"] = min(values) if 'loss' in metric_name \
                                               else max(values)
        
        return stats


def create_trainer(model,
                  config: Dict = None,
                  early_stopping: bool = True,
                  lr_schedule: Optional[Callable] = None) -> ModelTrainer:
    """
    Factory function to create a trainer with standard configuration.
    
    Args:
        model: Model instance
        config: Training configuration
        early_stopping: Enable early stopping
        lr_schedule: Learning rate schedule function
        
    Returns:
        Configured ModelTrainer instance
    """
    trainer = ModelTrainer(model, config)
    
    if early_stopping:
        early_stopping_cb = EarlyStoppingCallback(
            monitor='val_loss',
            patience=config.get("training", {}).get("early_stopping_patience", 10)
        )
        trainer.add_callback(early_stopping_cb)
    
    if lr_schedule:
        lr_scheduler = LearningRateScheduler(lr_schedule)
        trainer.add_callback(lr_scheduler)
    
    return trainer


# Example usage
if __name__ == "__main__":
    # Example: Training configuration
    config = {
        "training": {
            "num_epochs": 50,
            "batch_size": 32,
            "learning_rate": 0.001,
            "early_stopping_patience": 10,
            "verbose": 1
        },
        "tcn": {
            "window_size": 30
        },
        "autoencoder": {
            "latent_dim": 16
        }
    }
    
    # Create trainer (model would be actual model instance)
    # trainer = ModelTrainer(model, config)
    # history = trainer.train(X_train, y_train, X_val, y_val, model_type="tcn")
