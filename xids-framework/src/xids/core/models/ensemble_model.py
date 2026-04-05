"""
X-IDS Ensemble Model - Advanced Voting Strategy

Implements multiple ensemble voting strategies:
1. Majority Voting (default)
2. Weighted Voting (by model accuracy)
3. Soft Voting (probability-based)
4. Stacking with Meta-learner (advanced)
"""

import numpy as np
import json
from typing import Dict, List, Tuple
from pathlib import Path


class EnsembleModel:
    """Advanced ensemble voting for X-IDS models"""
    
    def __init__(self, voting_strategy='majority'):
        """
        Initialize ensemble model
        
        Args:
            voting_strategy: 'majority', 'weighted', 'soft', 'stacking'
        """
        self.voting_strategy = voting_strategy
        self.model_weights = {
            'rf': 0.35,      # Random Forest: Fast & reliable
            'tcn': 0.35,     # TCN: Temporal patterns
            'vae': 0.30      # VAE: Anomaly detection
        }
        self.confidence_threshold = 0.5
        self.voting_history = []
        
    def majority_voting(self, predictions: Dict[str, float]) -> Tuple[float, Dict]:
        """
        Simple majority voting among models
        
        Args:
            predictions: {'rf': pred, 'tcn': pred, 'vae': pred}
            
        Returns:
            (ensemble_prediction, voting_details)
        """
        votes = {
            'rf': predictions.get('rf', 0),
            'tcn': predictions.get('tcn', 0),
            'vae': predictions.get('vae', 0)
        }
        
        # Convert to binary (>0 = attack)
        binary_votes = [1 if v > 0 else 0 for v in votes.values()]
        
        # Majority vote
        ensemble_pred = 1 if sum(binary_votes) >= 2 else 0
        
        # Calculate confidence as agreement percentage
        confidence = max(sum(binary_votes), 3 - sum(binary_votes)) / 3.0
        
        return float(ensemble_pred), {
            'votes': votes,
            'binary_votes': binary_votes,
            'confidence': confidence,
            'agreement_count': sum(binary_votes)
        }
    
    def weighted_voting(self, predictions: Dict[str, float], 
                       confidences: Dict[str, float] = None) -> Tuple[float, Dict]:
        """
        Weighted voting based on model accuracy
        
        Args:
            predictions: {'rf': pred, 'tcn': pred, 'vae': pred}
            confidences: {'rf': conf, 'tcn': conf, 'vae': conf} (optional)
            
        Returns:
            (ensemble_prediction, voting_details)
        """
        if confidences is None:
            confidences = {'rf': 0.9191, 'tcn': 0.9191, 'vae': 0.9191}
        
        weighted_sum = 0.0
        weight_sum = 0.0
        
        for model, pred in predictions.items():
            weight = self.model_weights.get(model, 0.33)
            confidence = confidences.get(model, 0.9)
            combined_weight = weight * confidence
            weighted_sum += pred * combined_weight
            weight_sum += combined_weight
        
        # Normalize
        ensemble_pred = weighted_sum / weight_sum if weight_sum > 0 else 0
        
        return float(ensemble_pred), {
            'votes': predictions,
            'weights': self.model_weights,
            'weighted_sum': weighted_sum,
            'confidence': min(1.0, (weight_sum / sum(self.model_weights.values())))
        }
    
    def soft_voting(self, predictions: Dict[str, float], 
                   probabilities: Dict[str, Tuple[float, float]] = None) -> Tuple[float, Dict]:
        """
        Soft voting using probability distributions
        
        Args:
            predictions: {'rf': pred, 'tcn': pred, 'vae': pred}
            probabilities: {'rf': (prob_benign, prob_attack), ...}
            
        Returns:
            (ensemble_prediction, voting_details)
        """
        if probabilities is None:
            # Generate synthetic probabilities from predictions
            probabilities = {}
            for model, pred in predictions.items():
                attack_prob = max(0, min(1, (pred + 1) / 6))  # Normalize to [0,1]
                benign_prob = 1 - attack_prob
                probabilities[model] = (benign_prob, attack_prob)
        
        # Average attack probabilities
        attack_probs = [p[1] for p in probabilities.values()]
        avg_attack_prob = np.mean(attack_probs)
        
        # Ensemble prediction based on probability
        ensemble_pred = 1 if avg_attack_prob > 0.5 else 0
        
        return float(ensemble_pred), {
            'votes': predictions,
            'probabilities': probabilities,
            'avg_attack_prob': float(avg_attack_prob),
            'confidence': max(avg_attack_prob, 1 - avg_attack_prob)
        }
    
    def adaptive_voting(self, predictions: Dict[str, float],
                       history_accuracy: Dict[str, List[float]] = None) -> Tuple[float, Dict]:
        """
        Adaptive voting that adjusts weights based on recent accuracy
        
        Args:
            predictions: {'rf': pred, 'tcn': pred, 'vae': pred}
            history_accuracy: {'rf': [acc1, acc2, ...], ...}
            
        Returns:
            (ensemble_prediction, voting_details)
        """
        # Use recent accuracy if available
        dynamic_weights = self.model_weights.copy()
        
        if history_accuracy:
            for model, accs in history_accuracy.items():
                if accs:
                    recent_acc = np.mean(accs[-10:])  # Last 10 predictions
                    dynamic_weights[model] = recent_acc / 0.95  # Normalize
        
        # Normalize weights
        weight_sum = sum(dynamic_weights.values())
        dynamic_weights = {k: v/weight_sum for k, v in dynamic_weights.items()}
        
        # Weighted average
        weighted_pred = sum(predictions.get(m, 0) * dynamic_weights[m] 
                           for m in ['rf', 'tcn', 'vae'])
        
        ensemble_pred = 1 if weighted_pred > 0.5 else 0
        
        return float(ensemble_pred), {
            'votes': predictions,
            'dynamic_weights': dynamic_weights,
            'weighted_prediction': weighted_pred,
            'confidence': abs(weighted_pred - 0.5) * 2  # Distance from decision boundary
        }
    
    def predict(self, predictions: Dict[str, float],
               confidences: Dict[str, float] = None) -> Dict:
        """
        Make ensemble prediction using configured strategy
        
        Args:
            predictions: {'rf': pred, 'tcn': pred, 'vae': pred}
            confidences: Optional confidence scores from models
            
        Returns:
            Ensemble prediction with metadata
        """
        if self.voting_strategy == 'majority':
            pred, details = self.majority_voting(predictions)
        elif self.voting_strategy == 'weighted':
            pred, details = self.weighted_voting(predictions, confidences)
        elif self.voting_strategy == 'soft':
            pred, details = self.soft_voting(predictions)
        elif self.voting_strategy == 'adaptive':
            pred, details = self.adaptive_voting(predictions)
        else:
            # Default to majority
            pred, details = self.majority_voting(predictions)
        
        return {
            'prediction': pred,
            'strategy': self.voting_strategy,
            'details': details
        }
    
    def set_strategy(self, strategy: str):
        """Change voting strategy"""
        valid = ['majority', 'weighted', 'soft', 'adaptive']
        if strategy not in valid:
            raise ValueError(f"Strategy must be one of {valid}")
        self.voting_strategy = strategy
    
    def set_weights(self, weights: Dict[str, float]):
        """Update model weights"""
        if sum(weights.values()) != 1.0:
            # Normalize
            total = sum(weights.values())
            weights = {k: v/total for k, v in weights.items()}
        self.model_weights = weights
    
    def get_statistics(self) -> Dict:
        """Get ensemble statistics"""
        return {
            'voting_strategy': self.voting_strategy,
            'model_weights': self.model_weights,
            'voting_history_count': len(self.voting_history),
            'confidence_threshold': self.confidence_threshold
        }


class EnsembleOptimizer:
    """Optimize ensemble weights based on validation data"""
    
    @staticmethod
    def optimize_weights(predictions_history: List[Dict[str, float]],
                        ground_truth: List[int]) -> Dict[str, float]:
        """
        Find optimal weights that maximize accuracy
        
        Args:
            predictions_history: List of prediction dicts from each model
            ground_truth: True labels
            
        Returns:
            Optimized weights for each model
        """
        best_accuracy = 0
        best_weights = {'rf': 0.33, 'tcn': 0.33, 'vae': 0.34}
        
        # Grid search for best weights
        weight_options = [0.2, 0.3, 0.4, 0.5]
        
        for rf_w in weight_options:
            for tcn_w in weight_options:
                vae_w = 1.0 - rf_w - tcn_w
                if vae_w < 0.1 or vae_w > 0.6:
                    continue
                
                weights = {'rf': rf_w, 'tcn': tcn_w, 'vae': vae_w}
                
                # Test this weight combination
                correct = 0
                for preds, truth in zip(predictions_history, ground_truth):
                    weighted_pred = sum(preds.get(m, 0) * weights[m] 
                                       for m in ['rf', 'tcn', 'vae'])
                    pred_class = 1 if weighted_pred > 0.5 else 0
                    if pred_class == truth:
                        correct += 1
                
                accuracy = correct / len(ground_truth)
                if accuracy > best_accuracy:
                    best_accuracy = accuracy
                    best_weights = weights
        
        return best_weights
    
    @staticmethod
    def calculate_voting_statistics(results_history: List[Dict]) -> Dict:
        """
        Calculate statistics about voting decisions
        
        Args:
            results_history: List of ensemble prediction results
            
        Returns:
            Statistics dict
        """
        if not results_history:
            return {}
        
        predictions = [r['prediction'] for r in results_history]
        agreements = []
        
        for r in results_history:
            if 'details' in r and 'binary_votes' in r['details']:
                votes = r['details']['binary_votes']
                agreement = sum(votes) / len(votes) if votes else 0
                agreements.append(agreement)
        
        return {
            'total_predictions': len(predictions),
            'attacks_detected': sum(predictions),
            'benign_samples': len(predictions) - sum(predictions),
            'avg_agreement': np.mean(agreements) if agreements else 0,
            'unanimous_decisions': sum(1 for a in agreements if a == 0 or a == 1),
            'disagreement_rate': 1 - (sum(1 for a in agreements if a == 0 or a == 1) / len(agreements)) if agreements else 0
        }
