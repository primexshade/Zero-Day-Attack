"""
SHAP Explainer - Global feature importance
"""

import numpy as np
import shap
from typing import Dict, Any, Optional
import time


class SHAPExplainer:
    """SHAP kernel explainer for global interpretability"""

    def __init__(self, model: Any, config: Dict = None):
        """
        Initialize SHAP explainer
        
        Args:
            model: Trained model
            config: Configuration dictionary
        """
        self.model = model
        self.config = config or {}
        self.explainer = None
        self.background_data = None

    def fit(self, X_background: np.ndarray) -> None:
        """
        Fit explainer with background data
        
        Args:
            X_background: Background dataset for SHAP
        """
        shap_config = self.config.get("explainability", {}).get("shap", {})
        background_samples = shap_config.get("background_samples", 100)
        
        # Sample background data
        if len(X_background) > background_samples:
            indices = np.random.choice(len(X_background), background_samples, replace=False)
            self.background_data = X_background[indices]
        else:
            self.background_data = X_background

        # Create explainer
        explainer_type = shap_config.get("explainer_type", "kernel")
        
        if explainer_type == "kernel":
            self.explainer = shap.KernelExplainer(
                self.model.predict,
                self.background_data
            )

    def explain_instance(self, x: np.ndarray, check_additivity: bool = False) -> Dict[str, Any]:
        """
        Explain a single instance
        
        Args:
            x: Input instance
            check_additivity: Check SHAP additivity
            
        Returns:
            Explanation dictionary
        """
        if self.explainer is None:
            raise RuntimeError("Explainer not fitted. Call fit() first.")

        start_time = time.time()
        
        if x.ndim == 1:
            x = x.reshape(1, -1)

        shap_config = self.config.get("explainability", {}).get("shap", {})
        num_samples = shap_config.get("num_samples", 2048)
        
        shap_values = self.explainer.shap_values(x, check_additivity=check_additivity)
        prediction = self.model.predict(x)[0]

        elapsed_time = time.time() - start_time

        return {
            "prediction": float(prediction),
            "shap_values": shap_values[0] if isinstance(shap_values, list) else shap_values[0],
            "base_value": self.explainer.expected_value,
            "elapsed_time_ms": elapsed_time * 1000
        }

    def explain_batch(self, X: np.ndarray) -> list:
        """
        Explain multiple instances
        
        Args:
            X: Batch of instances
            
        Returns:
            List of explanations
        """
        explanations = []
        for i in range(len(X)):
            exp = self.explain_instance(X[i:i+1])
            explanations.append(exp)
        return explanations

    def get_feature_importance(self, X: np.ndarray, feature_names: Optional[list] = None) -> Dict[str, float]:
        """
        Get global feature importance from SHAP values
        
        Args:
            X: Dataset
            feature_names: Feature names (optional)
            
        Returns:
            Feature importance scores
        """
        shap_values = self.explainer.shap_values(X)
        
        # Handle different output formats
        if isinstance(shap_values, list):
            importance = np.abs(shap_values[0]).mean(axis=0)
        else:
            importance = np.abs(shap_values).mean(axis=0)

        if feature_names:
            return {name: float(imp) for name, imp in zip(feature_names, importance)}
        else:
            return {f"feature_{i}": float(imp) for i, imp in enumerate(importance)}
