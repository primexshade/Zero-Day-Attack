"""
Random Forest baseline model for comparison
Traditional signature-based approach
"""

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from typing import Dict, Any
import pickle
import os

from .base_model import BaseModel


class RandomForestBaseline(BaseModel):
    """Random Forest classifier for IDS baseline"""

    def __init__(self, config: Dict[str, Any] = None):
        """Initialize Random Forest model"""
        super().__init__(name="RandomForest", config=config)
        self.config = config or {}
        
    def build(self) -> None:
        """Initialize Random Forest"""
        rf_config = self.config.get("random_forest", {})
        
        self.model = RandomForestClassifier(
            n_estimators=rf_config.get("n_estimators", 500),
            max_depth=rf_config.get("max_depth", 20),
            min_samples_split=rf_config.get("min_samples_split", 5),
            min_samples_leaf=rf_config.get("min_samples_leaf", 2),
            random_state=rf_config.get("random_state", 42),
            n_jobs=rf_config.get("n_jobs", -1),
            verbose=1
        )

    def train(self, X_train: np.ndarray, y_train: np.ndarray,
              X_val: np.ndarray = None, y_val: np.ndarray = None) -> Dict:
        """Train Random Forest"""
        if self.model is None:
            self.build()
        
        self.model.fit(X_train, y_train)
        
        self.is_trained = True
        self.history = {
            "feature_importances": self.model.feature_importances_.tolist()
        }
        return self.history

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Make predictions"""
        if self.model is None:
            raise RuntimeError("Model not trained. Call train() first.")
        return self.model.predict_proba(X)[:, 1]

    def evaluate(self, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, float]:
        """Evaluate Random Forest"""
        if self.model is None:
            raise RuntimeError("Model not trained. Call train() first.")
        
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]
        
        metrics = {
            "accuracy": accuracy_score(y_test, y_pred),
            "precision": precision_score(y_test, y_pred, zero_division=0),
            "recall": recall_score(y_test, y_pred, zero_division=0),
            "f1_score": f1_score(y_test, y_pred, zero_division=0)
        }
        return metrics

    def save(self, filepath: str) -> None:
        """Save model"""
        if self.model is None:
            raise RuntimeError("No model to save.")
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "wb") as f:
            pickle.dump(self.model, f)
        
    def load(self, filepath: str) -> None:
        """Load model"""
        with open(filepath, "rb") as f:
            self.model = pickle.load(f)
        self.is_trained = True

    def get_feature_importance(self) -> np.ndarray:
        """Get feature importance"""
        if self.model is None:
            raise RuntimeError("Model not trained.")
        return self.model.feature_importances_
