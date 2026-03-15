"""
LIME Explainer - Local feature importance
"""

import numpy as np
from lime import lime_tabular
from typing import Dict, Any, Optional
import time


class LIMEExplainer:
    """LIME explainer for local interpretability"""

    def __init__(self, model: Any, config: Dict = None):
        """
        Initialize LIME explainer
        
        Args:
            model: Trained model
            config: Configuration dictionary
        """
        self.model = model
        self.config = config or {}
        self.explainer = None
        self.feature_names = None
        self.class_names = ["Benign", "Attack"]

    def fit(self, X_train: np.ndarray, feature_names: Optional[list] = None) -> None:
        """
        Fit LIME explainer
        
        Args:
            X_train: Training data for LIME
            feature_names: Feature names
        """
        lime_config = self.config.get("explainability", {}).get("lime", {})
        
        self.explainer = lime_tabular.LimeTabularExplainer(
            training_data=X_train,
            feature_names=feature_names or [f"feature_{i}" for i in range(X_train.shape[1])],
            class_names=self.class_names,
            mode="classification",
            verbose=False
        )
        self.feature_names = feature_names

    def explain_instance(self, x: np.ndarray, num_features: int = 10) -> Dict[str, Any]:
        """
        Explain a single instance
        
        Args:
            x: Input instance (1D array)
            num_features: Number of top features to return
            
        Returns:
            Explanation dictionary
        """
        if self.explainer is None:
            raise RuntimeError("Explainer not fitted. Call fit() first.")

        start_time = time.time()

        lime_config = self.config.get("explainability", {}).get("lime", {})
        num_samples = lime_config.get("num_samples", 1000)
        kernel_width = lime_config.get("kernel_width", 0.25)

        def predict_fn(X):
            predictions = self.model.predict(X)
            # Return probability of attack class
            return np.column_stack([1 - predictions, predictions])

        exp = self.explainer.explain_instance(
            x,
            predict_fn,
            num_features=num_features,
            num_samples=num_samples
        )

        elapsed_time = time.time() - start_time

        # Extract feature contributions
        feature_weights = {}
        for feature_idx, weight in exp.as_list():
            feature_weights[feature_idx] = float(weight)

        prediction = self.model.predict(x.reshape(1, -1))[0]

        return {
            "prediction": float(prediction),
            "feature_weights": feature_weights,
            "intercept": float(exp.intercept[1]),
            "num_samples": num_samples,
            "elapsed_time_ms": elapsed_time * 1000
        }

    def explain_batch(self, X: np.ndarray, num_features: int = 10) -> list:
        """
        Explain multiple instances
        
        Args:
            X: Batch of instances
            num_features: Number of top features
            
        Returns:
            List of explanations
        """
        explanations = []
        for i in range(len(X)):
            exp = self.explain_instance(X[i], num_features=num_features)
            explanations.append(exp)
        return explanations
