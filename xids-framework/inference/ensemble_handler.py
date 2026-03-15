"""
Advanced Ensemble Handler for X-IDS API
Provides enhanced voting strategies and analysis
"""

import numpy as np
from typing import Dict, Tuple
import time
import logging

logger = logging.getLogger(__name__)


class AdvancedEnsemble:
    """Advanced ensemble voting with multiple strategies"""
    
    def __init__(self):
        self.model_weights = {
            'rf': 0.35,      # Random Forest: Fast & reliable
            'tcn': 0.35,     # TCN: Temporal patterns
            'vae': 0.30      # VAE: Anomaly detection
        }
    
    def majority_vote(self, predictions: Dict[str, float]) -> Dict:
        """Simple majority voting"""
        binary_votes = {m: 1 if p > 0 else 0 for m, p in predictions.items()}
        vote_count = sum(binary_votes.values())
        consensus = 1 if vote_count >= 2 else 0
        confidence = max(vote_count, 3 - vote_count) / 3.0
        
        return {
            'prediction': float(consensus),
            'strategy': 'majority',
            'votes': binary_votes,
            'vote_count': vote_count,
            'confidence': confidence
        }
    
    def weighted_vote(self, predictions: Dict[str, float], 
                     confidences: Dict[str, float] = None) -> Dict:
        """Weighted voting by model accuracy"""
        if confidences is None:
            confidences = {'rf': 0.9191, 'tcn': 0.9191, 'vae': 0.9191}
        
        weighted_sum = 0.0
        weight_sum = 0.0
        
        for model in ['rf', 'tcn', 'vae']:
            pred = predictions.get(model, 0)
            conf = confidences.get(model, 0.9)
            weight = self.model_weights.get(model, 0.33)
            combined_weight = weight * conf
            weighted_sum += pred * combined_weight
            weight_sum += combined_weight
        
        ensemble_pred = weighted_sum / weight_sum if weight_sum > 0 else 0
        
        return {
            'prediction': float(1 if ensemble_pred > 0.5 else 0),
            'strategy': 'weighted',
            'weighted_score': float(ensemble_sum / weight_sum) if weight_sum > 0 else 0,
            'predictions': predictions,
            'weights': self.model_weights,
            'confidence': min(1.0, weight_sum / sum(self.model_weights.values()))
        }
    
    def soft_vote(self, predictions: Dict[str, float]) -> Dict:
        """Probability-based voting"""
        # Normalize predictions to [0, 1]
        attack_probs = {}
        for model, pred in predictions.items():
            attack_prob = max(0, min(1, (pred + 1) / 6))
            attack_probs[model] = attack_prob
        
        avg_prob = np.mean(list(attack_probs.values()))
        
        return {
            'prediction': float(1 if avg_prob > 0.5 else 0),
            'strategy': 'soft',
            'attack_probabilities': attack_probs,
            'average_attack_probability': float(avg_prob),
            'confidence': max(avg_prob, 1 - avg_prob)
        }
    
    def predict(self, predictions: Dict[str, float], strategy: str = 'weighted',
               confidences: Dict[str, float] = None) -> Dict:
        """
        Make ensemble prediction
        
        Args:
            predictions: {'rf': pred, 'tcn': pred, 'vae': pred}
            strategy: 'majority', 'weighted', or 'soft'
            confidences: Optional model confidences
            
        Returns:
            Ensemble prediction with metadata
        """
        if strategy == 'majority':
            return self.majority_vote(predictions)
        elif strategy == 'weighted':
            return self.weighted_vote(predictions, confidences)
        elif strategy == 'soft':
            return self.soft_vote(predictions)
        else:
            return self.weighted_vote(predictions, confidences)


def create_ensemble_response(rf_pred, rf_conf, tcn_pred, tcn_conf, 
                            vae_pred, vae_conf, strategy='weighted'):
    """Create ensemble response with all strategies"""
    
    predictions = {'rf': rf_pred, 'tcn': tcn_pred, 'vae': vae_pred}
    confidences = {'rf': rf_conf, 'tcn': tcn_conf, 'vae': vae_conf}
    
    ensemble = AdvancedEnsemble()
    
    # Get all strategies
    majority = ensemble.majority_vote(predictions)
    weighted = ensemble.weighted_vote(predictions, confidences)
    soft = ensemble.soft_vote(predictions)
    
    selected = {
        'majority': majority,
        'weighted': weighted,
        'soft': soft
    }.get(strategy, weighted)
    
    return {
        'selected_strategy': strategy,
        'ensemble_prediction': selected['prediction'],
        'ensemble_confidence': selected.get('confidence', 0.5),
        'model_predictions': predictions,
        'model_confidences': confidences,
        'all_strategies': {
            'majority': majority,
            'weighted': weighted,
            'soft': soft
        },
        'voting_details': selected
    }
