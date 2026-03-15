"""
Imbalance handling - SMOTE, ADASYN, and class weighting

Classes:
    ImbalanceHandler: Handle class imbalance using multiple strategies
"""

import numpy as np
import pandas as pd
from imblearn.over_sampling import SMOTE, ADASYN
from imblearn.under_sampling import RandomUnderSampler
from imblearn.pipeline import Pipeline as ImbPipeline
from sklearn.utils.class_weight import compute_class_weight
from typing import Tuple, Dict, Optional, Union
import logging
import pickle
from pathlib import Path

logger = logging.getLogger(__name__)


class ImbalanceHandler:
    """
    Handle class imbalance using SMOTE, ADASYN, class weighting, or combinations.
    
    Features:
    - SMOTE: Synthetic Minority Over-sampling Technique
    - ADASYN: Adaptive Synthetic Sampling
    - Random Under-sampling: Reduce majority class
    - Combined pipelines: SMOTE + ADASYN + Under-sampling
    - Class weighting: For algorithms supporting sample_weight
    - Statistics tracking: Monitor class distribution changes
    
    Attributes:
        config: Configuration dictionary
        strategy: Fitted resampling strategy
        class_weights: Dictionary of class weights
        original_distribution: Class distribution before resampling
        resampled_distribution: Class distribution after resampling
    """

    def __init__(self, config: Dict = None):
        """
        Initialize imbalance handler.
        
        Args:
            config: Configuration dictionary with imbalance settings
        """
        self.config = config or {}
        self.strategy = None
        self.class_weights: Dict[int, float] = {}
        self.original_distribution: Dict = {}
        self.resampled_distribution: Dict = {}
        self._is_fitted = False
        
    def _get_class_distribution(self, y: np.ndarray) -> Dict[int, int]:
        """
        Get class distribution statistics.
        
        Args:
            y: Target labels
            
        Returns:
            Dictionary mapping class -> count
        """
        unique, counts = np.unique(y, return_counts=True)
        return {c: count for c, count in zip(unique, counts)}
    
    def fit_resample(self, 
                    X: Union[np.ndarray, pd.DataFrame], 
                    y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Fit and resample data to handle class imbalance.
        
        Args:
            X: Feature matrix (numpy array or DataFrame)
            y: Target labels
            
        Returns:
            Resampled (X, y) tuple
        """
        logger.info("Starting class imbalance handling...")
        
        # Store original distribution
        self.original_distribution = self._get_class_distribution(y)
        logger.info(f"Original distribution: {self.original_distribution}")
        
        method = self.config.get("imbalance", {}).get("method", "smote")
        
        if method == "smote":
            X_res, y_res = self._apply_smote(X, y)
        elif method == "adasyn":
            X_res, y_res = self._apply_adasyn(X, y)
        elif method == "combined":
            X_res, y_res = self._apply_combined(X, y)
        elif method == "undersampling":
            X_res, y_res = self._apply_undersampling(X, y)
        elif method == "mixed":
            X_res, y_res = self._apply_mixed(X, y)
        elif method == "none":
            X_res, y_res = X, y
        else:
            logger.warning(f"Unknown method: {method}. Using SMOTE.")
            X_res, y_res = self._apply_smote(X, y)
        
        # Store resampled distribution
        self.resampled_distribution = self._get_class_distribution(y_res)
        logger.info(f"Resampled distribution: {self.resampled_distribution}")
        
        # Log imbalance ratio
        majority_class = max(self.resampled_distribution, 
                            key=self.resampled_distribution.get)
        minority_class = min(self.resampled_distribution, 
                            key=self.resampled_distribution.get)
        ratio = self.resampled_distribution[majority_class] / \
                self.resampled_distribution[minority_class]
        logger.info(f"Class imbalance ratio after resampling: {ratio:.2f}:1")
        
        self._is_fitted = True
        return X_res, y_res
    
    def _apply_smote(self, 
                    X: Union[np.ndarray, pd.DataFrame], 
                    y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Apply SMOTE (Synthetic Minority Over-sampling Technique).
        
        Args:
            X: Feature matrix
            y: Target labels
            
        Returns:
            Resampled (X, y)
        """
        logger.info("Applying SMOTE...")
        
        imbalance_config = self.config.get("imbalance", {})
        smote_config = imbalance_config.get("smote", {})
        
        smote = SMOTE(
            k_neighbors=smote_config.get("k_neighbors", 5),
            sampling_strategy=smote_config.get("sampling_strategy", 0.3),
            random_state=imbalance_config.get("random_state", 42)
        )
        
        X_res, y_res = smote.fit_resample(X, y)
        logger.info(f"SMOTE completed. New shape: {X_res.shape}")
        
        return X_res, y_res
    
    def _apply_adasyn(self, 
                     X: Union[np.ndarray, pd.DataFrame], 
                     y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Apply ADASYN (Adaptive Synthetic Sampling).
        
        Args:
            X: Feature matrix
            y: Target labels
            
        Returns:
            Resampled (X, y)
        """
        logger.info("Applying ADASYN...")
        
        imbalance_config = self.config.get("imbalance", {})
        adasyn_config = imbalance_config.get("adasyn", {})
        
        adasyn = ADASYN(
            n_neighbors=adasyn_config.get("n_neighbors", 5),
            sampling_strategy=adasyn_config.get("sampling_strategy", 0.3),
            random_state=imbalance_config.get("random_state", 42)
        )
        
        X_res, y_res = adasyn.fit_resample(X, y)
        logger.info(f"ADASYN completed. New shape: {X_res.shape}")
        
        return X_res, y_res
    
    def _apply_combined(self, 
                       X: Union[np.ndarray, pd.DataFrame], 
                       y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Apply SMOTE followed by ADASYN for best balance.
        
        Args:
            X: Feature matrix
            y: Target labels
            
        Returns:
            Resampled (X, y)
        """
        logger.info("Applying combined SMOTE + ADASYN...")
        
        imbalance_config = self.config.get("imbalance", {})
        
        # First SMOTE
        X, y = self._apply_smote(X, y)
        
        # Then ADASYN on the SMOTE output
        X, y = self._apply_adasyn(X, y)
        
        logger.info(f"Combined resampling completed. Final shape: {X.shape}")
        return X, y
    
    def _apply_undersampling(self, 
                            X: Union[np.ndarray, pd.DataFrame], 
                            y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Apply random under-sampling of majority class.
        
        Args:
            X: Feature matrix
            y: Target labels
            
        Returns:
            Resampled (X, y)
        """
        logger.info("Applying random under-sampling...")
        
        imbalance_config = self.config.get("imbalance", {})
        undersample_config = imbalance_config.get("undersampling", {})
        
        undersampler = RandomUnderSampler(
            sampling_strategy=undersample_config.get("sampling_strategy", 0.5),
            random_state=imbalance_config.get("random_state", 42)
        )
        
        X_res, y_res = undersampler.fit_resample(X, y)
        logger.info(f"Under-sampling completed. New shape: {X_res.shape}")
        
        return X_res, y_res
    
    def _apply_mixed(self, 
                    X: Union[np.ndarray, pd.DataFrame], 
                    y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Apply mixed strategy: SMOTE over-sampling + under-sampling.
        
        Args:
            X: Feature matrix
            y: Target labels
            
        Returns:
            Resampled (X, y)
        """
        logger.info("Applying mixed SMOTE + under-sampling...")
        
        imbalance_config = self.config.get("imbalance", {})
        
        pipeline = ImbPipeline([
            ('smote', SMOTE(
                sampling_strategy=0.5,
                random_state=imbalance_config.get("random_state", 42)
            )),
            ('undersample', RandomUnderSampler(
                sampling_strategy=0.8,
                random_state=imbalance_config.get("random_state", 42)
            ))
        ])
        
        X_res, y_res = pipeline.fit_resample(X, y)
        logger.info(f"Mixed resampling completed. New shape: {X_res.shape}")
        
        return X_res, y_res
    
    @staticmethod
    def compute_class_weights(y: np.ndarray) -> Dict[Union[int, str], float]:
        """
        Compute class weights for imbalanced data.
        
        Useful for algorithms that support sample_weight parameter
        (e.g., XGBoost, LightGBM, scikit-learn models).
        
        Formula: weight = total_samples / (n_classes * samples_per_class)
        
        Args:
            y: Target labels
            
        Returns:
            Dictionary mapping class -> weight
        """
        classes = np.unique(y)
        
        try:
            weights = compute_class_weight("balanced", classes=classes, y=y)
            class_weights = {c: w for c, w in zip(classes, weights)}
        except Exception as e:
            logger.warning(f"Error computing class weights: {e}")
            # Fallback: simple inverse frequency
            unique, counts = np.unique(y, return_counts=True)
            total = counts.sum()
            class_weights = {c: total / (len(unique) * count) 
                           for c, count in zip(unique, counts)}
        
        logger.info(f"Computed class weights: {class_weights}")
        return class_weights
    
    def get_sample_weights(self, y: np.ndarray) -> np.ndarray:
        """
        Get per-sample weights based on class.
        
        Args:
            y: Target labels
            
        Returns:
            Array of weights, one per sample
        """
        if not self.class_weights:
            self.class_weights = self.compute_class_weights(y)
        
        sample_weights = np.array([self.class_weights[label] for label in y])
        return sample_weights
    
    def get_statistics(self) -> Dict:
        """
        Get imbalance handling statistics.
        
        Returns:
            Dictionary with before/after statistics
        """
        stats = {
            'original_distribution': self.original_distribution,
            'resampled_distribution': self.resampled_distribution,
            'original_total': sum(self.original_distribution.values()),
            'resampled_total': sum(self.resampled_distribution.values()),
        }
        
        if self.original_distribution and self.resampled_distribution:
            # Calculate balance improvements
            original_max = max(self.original_distribution.values())
            original_min = min(self.original_distribution.values())
            original_ratio = original_max / original_min if original_min > 0 else float('inf')
            
            resampled_max = max(self.resampled_distribution.values())
            resampled_min = min(self.resampled_distribution.values())
            resampled_ratio = resampled_max / resampled_min if resampled_min > 0 else float('inf')
            
            stats['original_ratio'] = original_ratio
            stats['resampled_ratio'] = resampled_ratio
            stats['improvement'] = original_ratio / resampled_ratio if resampled_ratio > 0 else 0
        
        return stats
    
    def save(self, filepath: str) -> None:
        """
        Save imbalance handler state.
        
        Args:
            filepath: Path to save handler
        """
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        handler_state = {
            'config': self.config,
            'class_weights': self.class_weights,
            'original_distribution': self.original_distribution,
            'resampled_distribution': self.resampled_distribution,
            '_is_fitted': self._is_fitted
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(handler_state, f)
        
        logger.info(f"Imbalance handler saved to {filepath}")
    
    @classmethod
    def load(cls, filepath: str) -> 'ImbalanceHandler':
        """
        Load imbalance handler from disk.
        
        Args:
            filepath: Path to saved handler
            
        Returns:
            ImbalanceHandler instance
        """
        with open(filepath, 'rb') as f:
            handler_state = pickle.load(f)
        
        handler = cls(config=handler_state['config'])
        handler.class_weights = handler_state['class_weights']
        handler.original_distribution = handler_state['original_distribution']
        handler.resampled_distribution = handler_state['resampled_distribution']
        handler._is_fitted = handler_state['_is_fitted']
        
        logger.info(f"Imbalance handler loaded from {filepath}")
        return handler
