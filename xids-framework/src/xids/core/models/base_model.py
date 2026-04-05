"""
Base Model Class - Abstract base for all X-IDS models
"""

import numpy as np
from abc import ABC, abstractmethod
from typing import Tuple, Dict, Any


class BaseModel(ABC):
    """Abstract base class for all X-IDS models"""

    def __init__(self, name: str, config: Dict[str, Any] = None):
        """
        Initialize base model
        
        Args:
            name: Model name
            config: Configuration dictionary
        """
        self.name = name
        self.config = config or {}
        self.model = None
        self.is_trained = False
        self.history = {}

    @abstractmethod
    def build(self) -> None:
        """Build model architecture"""
        pass

    @abstractmethod
    def train(self, X_train: np.ndarray, y_train: np.ndarray, 
              X_val: np.ndarray = None, y_val: np.ndarray = None) -> Dict:
        """
        Train the model
        
        Args:
            X_train: Training features
            y_train: Training labels
            X_val: Validation features (optional)
            y_val: Validation labels (optional)
            
        Returns:
            Training history dictionary
        """
        pass

    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Make predictions
        
        Args:
            X: Input features
            
        Returns:
            Predictions
        """
        pass

    @abstractmethod
    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
        """
        Evaluate model performance
        
        Args:
            X_test: Test features
            y_test: Test labels
            
        Returns:
            Metrics dictionary
        """
        pass

    def save(self, filepath: str) -> None:
        """Save model to disk"""
        raise NotImplementedError("Subclass must implement save()")

    def load(self, filepath: str) -> None:
        """Load model from disk"""
        raise NotImplementedError("Subclass must implement load()")

    def get_config(self) -> Dict:
        """Get model configuration"""
        return {
            "name": self.name,
            "config": self.config,
            "is_trained": self.is_trained
        }
