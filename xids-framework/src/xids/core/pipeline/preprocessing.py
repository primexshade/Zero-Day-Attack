"""
Data preprocessing pipeline
Handles normalization, feature engineering, and missing value handling

Classes:
    DataPreprocessor: Complete preprocessing pipeline with feature engineering,
                      scaling, encoding, and missing value handling
"""

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler, LabelEncoder
from sklearn.impute import SimpleImputer
from typing import Tuple, Dict, Optional, List
import logging
import pickle
from pathlib import Path

logger = logging.getLogger(__name__)


class DataPreprocessor:
    """
    Complete preprocessing pipeline for network traffic data.
    
    Features:
    - Missing value handling (mean, median, forward-fill)
    - Feature scaling (MinMax, Standard, Robust)
    - Categorical encoding (Label, One-Hot)
    - Feature engineering (derived statistics)
    - Fit-transform consistency for train/test splits
    - Savepoint/restoration for reproducibility
    
    Attributes:
        scaler: Fitted scaler for feature normalization
        imputer: Fitted imputer for missing values
        label_encoders: Dictionary of label encoders for categorical features
        feature_names: Names of features after preprocessing
        numeric_features: List of numeric feature names
        categorical_features: List of categorical feature names
    """

    def __init__(self, config: Dict = None):
        """
        Initialize preprocessor.
        
        Args:
            config: Configuration dictionary with preprocessing settings
        """
        self.config = config or {}
        self.scaler = None
        self.imputer = None
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.feature_names: Optional[List[str]] = None
        self.numeric_features: List[str] = []
        self.categorical_features: List[str] = []
        self._is_fitted = False
        
    def _identify_feature_types(self, X: pd.DataFrame) -> None:
        """
        Identify numeric and categorical features.
        
        Args:
            X: Input DataFrame
        """
        self.numeric_features = X.select_dtypes(
            include=['int64', 'float64']
        ).columns.tolist()
        
        self.categorical_features = X.select_dtypes(
            include=['object', 'category']
        ).columns.tolist()
        
        logger.info(f"Identified {len(self.numeric_features)} numeric and "
                   f"{len(self.categorical_features)} categorical features")
    
    def _handle_missing_values(self, X: pd.DataFrame, fit: bool = False) -> pd.DataFrame:
        """
        Handle missing values in dataset.
        
        Args:
            X: Input DataFrame
            fit: Whether to fit imputer on this data
            
        Returns:
            DataFrame with missing values handled
        """
        if X.isnull().sum().sum() == 0:
            return X
        
        prep_config = self.config.get("preprocessing", {})
        
        if not prep_config.get("handle_missing", True):
            logger.warning("Missing values not handled by config")
            return X
        
        strategy = prep_config.get("missing_strategy", "mean")
        
        X_copy = X.copy()
        
        # Handle numeric features
        if self.numeric_features:
            if fit:
                self.imputer = SimpleImputer(strategy=strategy)
                X_copy[self.numeric_features] = self.imputer.fit_transform(
                    X_copy[self.numeric_features]
                )
            else:
                if self.imputer is None:
                    raise ValueError("Imputer not fitted. Call fit first.")
                X_copy[self.numeric_features] = self.imputer.transform(
                    X_copy[self.numeric_features]
                )
        
        # Handle categorical features (forward fill or mode)
        for col in self.categorical_features:
            if X_copy[col].isnull().sum() > 0:
                if strategy == "forward_fill":
                    X_copy[col] = X_copy[col].fillna(method='ffill')
                else:
                    X_copy[col] = X_copy[col].fillna(X_copy[col].mode()[0])
        
        missing_count = X_copy.isnull().sum().sum()
        logger.info(f"Handled missing values. Remaining: {missing_count}")
        
        return X_copy
    
    def _encode_categorical(self, X: pd.DataFrame, fit: bool = False) -> pd.DataFrame:
        """
        Encode categorical features.
        
        Args:
            X: Input DataFrame
            fit: Whether to fit encoders on this data
            
        Returns:
            DataFrame with categorical features encoded
        """
        if not self.categorical_features:
            return X
        
        prep_config = self.config.get("preprocessing", {})
        encoding_method = prep_config.get("encoding_method", "label")
        
        X_copy = X.copy()
        
        if encoding_method == "label":
            for col in self.categorical_features:
                if fit:
                    self.label_encoders[col] = LabelEncoder()
                    X_copy[col] = self.label_encoders[col].fit_transform(
                        X_copy[col].astype(str)
                    )
                else:
                    if col not in self.label_encoders:
                        raise ValueError(f"Encoder for {col} not fitted")
                    X_copy[col] = self.label_encoders[col].transform(
                        X_copy[col].astype(str)
                    )
        
        elif encoding_method == "onehot":
            X_copy = pd.get_dummies(
                X_copy,
                columns=self.categorical_features,
                drop_first=True
            )
        
        logger.info(f"Encoded {len(self.categorical_features)} categorical features")
        return X_copy
    
    def _normalize_features(self, X: np.ndarray, fit: bool = False) -> np.ndarray:
        """
        Normalize numeric features.
        
        Args:
            X: Input array (numeric features)
            fit: Whether to fit scaler on this data
            
        Returns:
            Normalized array
        """
        prep_config = self.config.get("preprocessing", {})
        
        if not prep_config.get("normalize", True):
            return X
        
        method = prep_config.get("normalization_method", "minmax")
        
        if method == "minmax":
            scaler_class = MinMaxScaler
        elif method == "standard":
            scaler_class = StandardScaler
        elif method == "robust":
            scaler_class = RobustScaler
        else:
            logger.warning(f"Unknown normalization method: {method}. Using MinMax")
            scaler_class = MinMaxScaler
        
        if fit:
            self.scaler = scaler_class()
            X_normalized = self.scaler.fit_transform(X)
        else:
            if self.scaler is None:
                raise ValueError("Scaler not fitted. Call fit first.")
            X_normalized = self.scaler.transform(X)
        
        logger.info(f"Normalized features using {method} scaling")
        return X_normalized
    
    def _engineer_features(self, X: pd.DataFrame) -> pd.DataFrame:
        """
        Create derived features from raw features.
        
        Args:
            X: Input DataFrame
            
        Returns:
            DataFrame with engineered features
        """
        prep_config = self.config.get("preprocessing", {})
        
        if not prep_config.get("feature_engineering", False):
            return X
        
        X_eng = X.copy()
        
        # Example: Create flow statistics if available
        flow_cols = [col for col in X.columns 
                    if 'flow' in col.lower() or 'packet' in col.lower()]
        
        if len(flow_cols) > 1:
            try:
                X_eng['flow_stats_mean'] = X_eng[flow_cols].mean(axis=1)
                X_eng['flow_stats_std'] = X_eng[flow_cols].std(axis=1)
                X_eng['flow_stats_max'] = X_eng[flow_cols].max(axis=1)
                X_eng['flow_stats_min'] = X_eng[flow_cols].min(axis=1)
                logger.info("Created flow statistics features")
            except Exception as e:
                logger.warning(f"Could not create flow features: {e}")
        
        return X_eng
    
    def fit(self, X: pd.DataFrame, y: Optional[pd.Series] = None) -> None:
        """
        Fit preprocessing transforms on training data.
        
        Args:
            X: Training features (DataFrame)
            y: Training labels (optional)
        """
        logger.info("Fitting preprocessor...")
        
        # Identify feature types
        self._identify_feature_types(X)
        
        # Handle missing values
        X = self._handle_missing_values(X, fit=True)
        
        # Encode categorical features
        X = self._encode_categorical(X, fit=True)
        
        # Engineer features
        X = self._engineer_features(X)
        
        # Get numeric features for scaling
        numeric_cols = X.select_dtypes(
            include=['int64', 'float64']
        ).columns.tolist()
        
        # Normalize
        if numeric_cols:
            X_numeric = X[numeric_cols].values
            self._normalize_features(X_numeric, fit=True)
        
        self.feature_names = X.columns.tolist()
        self._is_fitted = True
        logger.info("Preprocessor fitted successfully")
    
    def transform(self, X: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
        """
        Apply fitted preprocessing transforms.
        
        Args:
            X: Features to transform (DataFrame)
            
        Returns:
            (transformed_array, feature_names) tuple
        """
        if not self._is_fitted:
            raise ValueError("Preprocessor not fitted. Call fit first.")
        
        logger.info("Transforming data...")
        
        # Handle missing values
        X = self._handle_missing_values(X, fit=False)
        
        # Encode categorical features
        X = self._encode_categorical(X, fit=False)
        
        # Engineer features
        X = self._engineer_features(X)
        
        # Get numeric features
        numeric_cols = X.select_dtypes(
            include=['int64', 'float64']
        ).columns.tolist()
        
        # Normalize
        if numeric_cols:
            X_numeric = X[numeric_cols].values
            X_numeric = self._normalize_features(X_numeric, fit=False)
            X[numeric_cols] = X_numeric
        
        return X.values, X.columns.tolist()
    
    def fit_transform(self, X: pd.DataFrame, 
                     y: Optional[pd.Series] = None) -> Tuple[np.ndarray, List[str]]:
        """
        Fit and transform in one step.
        
        Args:
            X: Features
            y: Labels (optional)
            
        Returns:
            (transformed_array, feature_names) tuple
        """
        self.fit(X, y)
        return self.transform(X)
    
    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        """
        Inverse transform normalized features back to original scale.
        
        Args:
            X: Normalized features
            
        Returns:
            Features in original scale
        """
        if self.scaler is None:
            logger.warning("No scaler fitted. Returning data unchanged.")
            return X
        
        return self.scaler.inverse_transform(X)
    
    def save(self, filepath: str) -> None:
        """
        Save fitted preprocessor to disk.
        
        Args:
            filepath: Path to save preprocessor
        """
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        preprocessor_state = {
            'scaler': self.scaler,
            'imputer': self.imputer,
            'label_encoders': self.label_encoders,
            'feature_names': self.feature_names,
            'numeric_features': self.numeric_features,
            'categorical_features': self.categorical_features,
            'config': self.config,
            '_is_fitted': self._is_fitted
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(preprocessor_state, f)
        
        logger.info(f"Preprocessor saved to {filepath}")
    
    @classmethod
    def load(cls, filepath: str) -> 'DataPreprocessor':
        """
        Load fitted preprocessor from disk.
        
        Args:
            filepath: Path to saved preprocessor
            
        Returns:
            DataPreprocessor instance
        """
        with open(filepath, 'rb') as f:
            preprocessor_state = pickle.load(f)
        
        preprocessor = cls(config=preprocessor_state['config'])
        preprocessor.scaler = preprocessor_state['scaler']
        preprocessor.imputer = preprocessor_state['imputer']
        preprocessor.label_encoders = preprocessor_state['label_encoders']
        preprocessor.feature_names = preprocessor_state['feature_names']
        preprocessor.numeric_features = preprocessor_state['numeric_features']
        preprocessor.categorical_features = preprocessor_state['categorical_features']
        preprocessor._is_fitted = preprocessor_state['_is_fitted']
        
        logger.info(f"Preprocessor loaded from {filepath}")
        return preprocessor
    
    def get_feature_names(self) -> List[str]:
        """Get names of features after preprocessing."""
        if self.feature_names is None:
            raise ValueError("Preprocessor not fitted")
        return self.feature_names
    
    def set_feature_names(self, names: List[str]) -> None:
        """Set feature names."""
        self.feature_names = names
