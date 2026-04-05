"""
Evaluation metrics and reporting
"""

import numpy as np
from sklearn.metrics import (
    confusion_matrix, precision_score, recall_score, f1_score,
    roc_auc_score, roc_curve, precision_recall_curve, auc
)
from typing import Dict, Tuple, Any
import json


class EvaluationMetrics:
    """Compute comprehensive evaluation metrics"""

    @staticmethod
    def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_pred_proba: np.ndarray = None) -> Dict[str, float]:
        """
        Compute classification metrics
        
        Args:
            y_true: True labels
            y_pred: Predicted labels (binary)
            y_pred_proba: Predicted probabilities (optional)
            
        Returns:
            Metrics dictionary
        """
        metrics = {
            "accuracy": float(np.mean(y_pred == y_true)),
            "precision": float(precision_score(y_true, y_pred, zero_division=0)),
            "recall": float(recall_score(y_true, y_pred, zero_division=0)),
            "f1_score": float(f1_score(y_true, y_pred, zero_division=0)),
        }
        
        if y_pred_proba is not None:
            metrics["roc_auc"] = float(roc_auc_score(y_true, y_pred_proba))
        
        return metrics

    @staticmethod
    def confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray) -> np.ndarray:
        """Compute confusion matrix"""
        return confusion_matrix(y_true, y_pred)

    @staticmethod
    def roc_curve_data(y_true: np.ndarray, y_pred_proba: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Get ROC curve data"""
        fpr, tpr, thresholds = roc_curve(y_true, y_pred_proba)
        return fpr, tpr, thresholds

    @staticmethod
    def precision_recall_curve_data(y_true: np.ndarray, y_pred_proba: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Get precision-recall curve data"""
        precision, recall, thresholds = precision_recall_curve(y_true, y_pred_proba)
        return precision, recall, thresholds


class EvaluationReport:
    """Generate comprehensive evaluation reports"""

    def __init__(self):
        """Initialize report"""
        self.results = {}

    def add_model_results(self, model_name: str, metrics: Dict[str, float], 
                         cm: np.ndarray = None, feature_importance: Dict = None) -> None:
        """
        Add model results to report
        
        Args:
            model_name: Name of the model
            metrics: Metrics dictionary
            cm: Confusion matrix
            feature_importance: Feature importance scores
        """
        self.results[model_name] = {
            "metrics": metrics,
            "confusion_matrix": cm.tolist() if cm is not None else None,
            "feature_importance": feature_importance
        }

    def generate_comparison(self) -> str:
        """Generate model comparison report"""
        report = "=" * 80 + "\n"
        report += "MODEL COMPARISON REPORT\n"
        report += "=" * 80 + "\n\n"

        # Metrics comparison table
        report += "Metrics Comparison:\n"
        report += "-" * 80 + "\n"
        
        if self.results:
            metrics_keys = list(list(self.results.values())[0]["metrics"].keys())
            header = f"{'Model':<20}"
            for key in metrics_keys:
                header += f"{key:<15}"
            report += header + "\n"
            report += "-" * 80 + "\n"

            for model_name, data in self.results.items():
                line = f"{model_name:<20}"
                for key in metrics_keys:
                    value = data["metrics"].get(key, 0)
                    line += f"{value:<15.4f}"
                report += line + "\n"

        report += "\n" + "=" * 80 + "\n"
        return report

    def to_json(self) -> str:
        """Export results to JSON"""
        return json.dumps(self.results, indent=2)
