"""
Data loaders for CICIDS2017 and UNSW-NB15 datasets.

This module provides functionality to download, validate, and load network
intrusion detection datasets with proper error handling and data validation.

Classes:
    CICIDSDataLoader: Loads and validates CICIDS2017 dataset
    UNSWDataLoader: Loads and validates UNSW-NB15 dataset
    DatasetManager: Orchestrates loading and merging of multiple datasets
"""

import os
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, List, Dict
import logging
from abc import ABC, abstractmethod
import hashlib
import requests
from urllib.parse import urljoin

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseDataLoader(ABC):
    """Abstract base class for dataset loaders."""
    
    def __init__(self, data_dir: str = "./data/raw"):
        """
        Initialize base data loader.
        
        Args:
            data_dir: Directory to store raw datasets
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    @abstractmethod
    def download(self, force: bool = False) -> str:
        """Download dataset. Returns path to downloaded file."""
        pass
    
    @abstractmethod
    def load(self) -> pd.DataFrame:
        """Load dataset from file."""
        pass
    
    @abstractmethod
    def validate(self, df: pd.DataFrame) -> bool:
        """Validate dataset integrity."""
        pass
    
    def _verify_file(self, filepath: str, expected_size: Optional[int] = None) -> bool:
        """
        Verify file exists and optionally check size.
        
        Args:
            filepath: Path to file
            expected_size: Expected file size in bytes (optional)
            
        Returns:
            True if file is valid
        """
        if not os.path.exists(filepath):
            logger.error(f"File not found: {filepath}")
            return False
        
        file_size = os.path.getsize(filepath)
        if expected_size and abs(file_size - expected_size) > 1e6:  # 1MB tolerance
            logger.warning(f"File size mismatch: {file_size} vs expected {expected_size}")
        
        return True


class CICIDSDataLoader(BaseDataLoader):
    """
    Loader for CICIDS2017 dataset.
    
    Source: https://www.unb.ca/cic/datasets/ids-2017.html
    
    Dataset contains:
    - 2,830,743 records
    - 83 features
    - 14 attack types + normal traffic
    - File size: ~1.2 GB
    """
    
    DATASET_NAME = "CICIDS2017"
    REMOTE_URL = "https://www.unb.ca/cic/datasets/ids-2017.html"
    EXPECTED_SIZE = 1.2e9  # 1.2 GB
    
    # Column mapping for CICIDS2017
    ATTACK_LABELS = {
        'Label': 'attack_type',
        'label': 'attack_type'
    }
    
    KNOWN_ATTACKS = [
        'Benign',
        'FTP-Patator',
        'SSH-Patator',
        'DoS Hulk',
        'DoS GoldenEye',
        'DoS SlowHTTP',
        'DoS Slowloris',
        'Heartbleed',
        'Web Attack – Brute Force',
        'Web Attack – XSS',
        'Web Attack – SQL Injection',
        'Infiltration',
        'Bot',
        'PortScan'
    ]
    
    def download(self, force: bool = False) -> str:
        """
        Download CICIDS2017 dataset.
        
        Note: This is a manual download dataset. The method provides
        instructions and checks for local availability.
        
        Args:
            force: Force re-download (ignored for manual datasets)
            
        Returns:
            Path to dataset file
            
        Raises:
            FileNotFoundError: If dataset not found locally
        """
        filepath = self.data_dir / "CICIDS2017.csv"
        
        if filepath.exists():
            logger.info(f"Dataset already exists: {filepath}")
            return str(filepath)
        
        logger.error(f"CICIDS2017 dataset not found at {filepath}")
        logger.info("=" * 70)
        logger.info("Please download CICIDS2017 manually from:")
        logger.info(self.REMOTE_URL)
        logger.info(f"And save to: {filepath}")
        logger.info("=" * 70)
        raise FileNotFoundError(
            f"CICIDS2017 dataset not found. Please download manually from "
            f"{self.REMOTE_URL} and place at {filepath}"
        )
    
    def load(self, filepath: Optional[str] = None) -> pd.DataFrame:
        """
        Load CICIDS2017 dataset.
        
        Args:
            filepath: Path to dataset (if None, searches default location)
            
        Returns:
            DataFrame with network traffic data
        """
        if filepath is None:
            filepath = self.data_dir / "CICIDS2017.csv"
        
        if not self._verify_file(str(filepath)):
            raise FileNotFoundError(f"Dataset file not found: {filepath}")
        
        logger.info(f"Loading CICIDS2017 from {filepath}...")
        
        # Load with proper dtype handling
        df = pd.read_csv(
            filepath,
            low_memory=False,
            skipinitialspace=True
        )
        
        # Clean column names
        df.columns = df.columns.str.strip()
        
        logger.info(f"Loaded {len(df)} records with {len(df.columns)} features")
        
        return df
    
    def validate(self, df: pd.DataFrame) -> bool:
        """
        Validate CICIDS2017 dataset integrity.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            True if valid
        """
        # Check minimum records
        if len(df) < 1e6:
            logger.warning(f"Dataset too small: {len(df)} records (expected > 1M)")
        
        # Check for label column
        label_cols = [col for col in df.columns if 'label' in col.lower()]
        if not label_cols:
            logger.error("No label column found in dataset")
            return False
        
        # Check feature columns (at least 80)
        non_label_cols = [col for col in df.columns if 'label' not in col.lower()]
        if len(non_label_cols) < 80:
            logger.error(f"Too few features: {len(non_label_cols)} (expected ~83)")
            return False
        
        # Check for missing values
        missing_pct = df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100
        if missing_pct > 10:
            logger.warning(f"High missing value rate: {missing_pct:.2f}%")
        
        logger.info("Dataset validation passed ✓")
        return True


class UNSWDataLoader(BaseDataLoader):
    """
    Loader for UNSW-NB15 dataset.
    
    Source: https://www.unsw.adfa.edu.au/unsw-canberra-cyber/cybersecurity-datasets/
    
    Dataset contains:
    - 2,540,044 records
    - 49 features
    - 9 attack types + normal traffic
    - File size: ~900 MB
    """
    
    DATASET_NAME = "UNSW-NB15"
    REMOTE_URL = "https://www.unsw.adfa.edu.au/unsw-canberra-cyber/cybersecurity-datasets/"
    EXPECTED_SIZE = 9e8  # 900 MB
    
    KNOWN_ATTACKS = [
        'Normal',
        'Generic',
        'Exploits',
        'Fuzzers',
        'DoS',
        'Reconnaissance',
        'Analysis',
        'Backdoor',
        'Shellcode',
        'Worms'
    ]
    
    def download(self, force: bool = False) -> str:
        """
        Download UNSW-NB15 dataset.
        
        Note: This is a manual download dataset.
        
        Args:
            force: Force re-download (ignored for manual datasets)
            
        Returns:
            Path to dataset file
            
        Raises:
            FileNotFoundError: If dataset not found locally
        """
        filepath = self.data_dir / "UNSW-NB15.csv"
        
        if filepath.exists():
            logger.info(f"Dataset already exists: {filepath}")
            return str(filepath)
        
        logger.error(f"UNSW-NB15 dataset not found at {filepath}")
        logger.info("=" * 70)
        logger.info("Please download UNSW-NB15 manually from:")
        logger.info(self.REMOTE_URL)
        logger.info(f"And save to: {filepath}")
        logger.info("=" * 70)
        raise FileNotFoundError(
            f"UNSW-NB15 dataset not found. Please download manually from "
            f"{self.REMOTE_URL} and place at {filepath}"
        )
    
    def load(self, filepath: Optional[str] = None) -> pd.DataFrame:
        """
        Load UNSW-NB15 dataset.
        
        Args:
            filepath: Path to dataset (if None, searches default location)
            
        Returns:
            DataFrame with network traffic data
        """
        if filepath is None:
            filepath = self.data_dir / "UNSW-NB15.csv"
        
        if not self._verify_file(str(filepath)):
            raise FileNotFoundError(f"Dataset file not found: {filepath}")
        
        logger.info(f"Loading UNSW-NB15 from {filepath}...")
        
        df = pd.read_csv(
            filepath,
            low_memory=False,
            skipinitialspace=True
        )
        
        # Clean column names
        df.columns = df.columns.str.strip()
        
        logger.info(f"Loaded {len(df)} records with {len(df.columns)} features")
        
        return df
    
    def validate(self, df: pd.DataFrame) -> bool:
        """
        Validate UNSW-NB15 dataset integrity.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            True if valid
        """
        # Check minimum records
        if len(df) < 1e6:
            logger.warning(f"Dataset too small: {len(df)} records (expected > 1M)")
        
        # Check for label column
        label_cols = [col for col in df.columns if 'label' in col.lower() or 'attack' in col.lower()]
        if not label_cols:
            logger.error("No label column found in dataset")
            return False
        
        # Check feature columns
        non_label_cols = [col for col in df.columns 
                         if 'label' not in col.lower() and 'attack' not in col.lower()]
        if len(non_label_cols) < 40:
            logger.error(f"Too few features: {len(non_label_cols)} (expected ~49)")
            return False
        
        # Check for missing values
        missing_pct = df.isnull().sum().sum() / (len(df) * len(df.columns)) * 100
        if missing_pct > 10:
            logger.warning(f"High missing value rate: {missing_pct:.2f}%")
        
        logger.info("Dataset validation passed ✓")
        return True


class DatasetManager:
    """
    Manages loading, validation, and merging of multiple datasets.
    
    Features:
    - Automatic dataset discovery
    - Validation and quality checks
    - Feature alignment and merging
    - Train/val/test splitting
    - Balanced sampling
    """
    
    def __init__(self, data_dir: str = "./data/raw", cache_dir: str = "./data/processed"):
        """
        Initialize dataset manager.
        
        Args:
            data_dir: Directory with raw datasets
            cache_dir: Directory to save processed data
        """
        self.data_dir = Path(data_dir)
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.cicids_loader = CICIDSDataLoader(data_dir)
        self.unsw_loader = UNSWDataLoader(data_dir)
        
        self.cicids_df: Optional[pd.DataFrame] = None
        self.unsw_df: Optional[pd.DataFrame] = None
        self.merged_df: Optional[pd.DataFrame] = None
    
    def load_all(self) -> pd.DataFrame:
        """
        Load and merge all available datasets.
        
        Returns:
            Merged DataFrame with unified schema
        """
        logger.info("Loading all datasets...")
        
        # Try to load CICIDS2017
        try:
            self.cicids_df = self.cicids_loader.load()
            if not self.cicids_loader.validate(self.cicids_df):
                logger.warning("CICIDS2017 validation failed, but continuing...")
        except FileNotFoundError as e:
            logger.warning(f"CICIDS2017 not available: {e}")
        
        # Try to load UNSW-NB15
        try:
            self.unsw_df = self.unsw_loader.load()
            if not self.unsw_loader.validate(self.unsw_df):
                logger.warning("UNSW-NB15 validation failed, but continuing...")
        except FileNotFoundError as e:
            logger.warning(f"UNSW-NB15 not available: {e}")
        
        if self.cicids_df is None and self.unsw_df is None:
            raise FileNotFoundError(
                "No datasets found. Please download CICIDS2017 and/or UNSW-NB15"
            )
        
        # Merge if both available
        if self.cicids_df is not None and self.unsw_df is not None:
            self.merged_df = self._merge_datasets()
        elif self.cicids_df is not None:
            self.merged_df = self.cicids_df.copy()
        else:
            self.merged_df = self.unsw_df.copy()
        
        logger.info(f"Successfully loaded {len(self.merged_df)} total records")
        return self.merged_df
    
    def _merge_datasets(self) -> pd.DataFrame:
        """
        Merge CICIDS2017 and UNSW-NB15 with unified schema.
        
        Returns:
            Merged DataFrame
        """
        logger.info("Merging datasets...")
        
        # Find common features (numeric columns, excluding labels)
        cicids_cols = set(self.cicids_df.columns)
        unsw_cols = set(self.unsw_df.columns)
        
        # Identify label columns
        cicids_labels = [c for c in cicids_cols if 'label' in c.lower()]
        unsw_labels = [c for c in unsw_cols if 'label' in c.lower() or 'attack' in c.lower()]
        
        # Get feature columns (numeric)
        cicids_features = [c for c in cicids_cols 
                          if c not in cicids_labels and 
                          self.cicids_df[c].dtype in [np.float64, np.int64]]
        unsw_features = [c for c in unsw_cols 
                        if c not in unsw_labels and 
                        self.unsw_df[c].dtype in [np.float64, np.int64]]
        
        # Find overlap
        common_features = list(set(cicids_features) & set(unsw_features))
        logger.info(f"Found {len(common_features)} common features between datasets")
        
        # Select and standardize
        cicids_subset = self.cicids_df[[*common_features, cicids_labels[0]]].copy()
        unsw_subset = self.unsw_df[[*common_features, unsw_labels[0]]].copy()
        
        # Rename labels to standard format
        cicids_subset.rename({cicids_labels[0]: 'label'}, axis=1, inplace=True)
        unsw_subset.rename({unsw_labels[0]: 'label'}, axis=1, inplace=True)
        
        # Add dataset identifier
        cicids_subset['dataset'] = 'CICIDS2017'
        unsw_subset['dataset'] = 'UNSW-NB15'
        
        # Concatenate
        merged = pd.concat([cicids_subset, unsw_subset], ignore_index=True)
        logger.info(f"Merged dataset: {len(merged)} records, {len(merged.columns)} features")
        
        return merged
    
    def get_statistics(self) -> Dict:
        """
        Get dataset statistics.
        
        Returns:
            Dictionary with statistics
        """
        if self.merged_df is None:
            self.load_all()
        
        stats = {
            'total_records': len(self.merged_df),
            'total_features': len(self.merged_df.columns),
            'missing_values': self.merged_df.isnull().sum().to_dict(),
            'memory_usage_mb': self.merged_df.memory_usage(deep=True).sum() / 1e6,
        }
        
        return stats
    
    def get_data_splits(self, 
                       test_size: float = 0.2,
                       val_size: float = 0.1,
                       random_state: int = 42,
                       stratify: bool = True) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Create train/val/test splits with optional stratification.
        
        Args:
            test_size: Proportion for test set (0.2 = 20%)
            val_size: Proportion for validation set (0.1 = 10%)
            random_state: Random seed for reproducibility
            stratify: Stratify by label to maintain class distribution
            
        Returns:
            (X_train, X_val, X_test) DataFrames
        """
        from sklearn.model_selection import train_test_split
        
        if self.merged_df is None:
            self.load_all()
        
        np.random.seed(random_state)
        
        # First split: train+val vs test
        if stratify and 'label' in self.merged_df.columns:
            train_val, test = train_test_split(
                self.merged_df,
                test_size=test_size,
                random_state=random_state,
                stratify=self.merged_df['label']
            )
        else:
            train_val, test = train_test_split(
                self.merged_df,
                test_size=test_size,
                random_state=random_state
            )
        
        # Second split: train vs val
        val_ratio = val_size / (1 - test_size)  # Adjust for remaining data
        if stratify and 'label' in train_val.columns:
            train, val = train_test_split(
                train_val,
                test_size=val_ratio,
                random_state=random_state,
                stratify=train_val['label']
            )
        else:
            train, val = train_test_split(
                train_val,
                test_size=val_ratio,
                random_state=random_state
            )
        
        logger.info(f"Data splits created:")
        logger.info(f"  Train: {len(train)} ({len(train)/len(self.merged_df)*100:.1f}%)")
        logger.info(f"  Val:   {len(val)} ({len(val)/len(self.merged_df)*100:.1f}%)")
        logger.info(f"  Test:  {len(test)} ({len(test)/len(self.merged_df)*100:.1f}%)")
        
        return train, val, test
    
    def save_splits(self, train: pd.DataFrame, val: pd.DataFrame, test: pd.DataFrame):
        """
        Save data splits to disk.
        
        Args:
            train: Training set
            val: Validation set
            test: Test set
        """
        train.to_csv(self.cache_dir / "train.csv", index=False)
        val.to_csv(self.cache_dir / "val.csv", index=False)
        test.to_csv(self.cache_dir / "test.csv", index=False)
        
        logger.info(f"Data splits saved to {self.cache_dir}")
    
    def load_splits(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Load previously saved data splits.
        
        Returns:
            (train, val, test) DataFrames
        """
        train = pd.read_csv(self.cache_dir / "train.csv")
        val = pd.read_csv(self.cache_dir / "val.csv")
        test = pd.read_csv(self.cache_dir / "test.csv")
        
        logger.info(f"Loaded data splits from {self.cache_dir}")
        return train, val, test


# Example usage and testing
if __name__ == "__main__":
    # Create manager
    manager = DatasetManager(
        data_dir="./data/raw",
        cache_dir="./data/processed"
    )
    
    # Load datasets
    try:
        df = manager.load_all()
        print(f"\nDataset shape: {df.shape}")
        print(f"Columns: {df.columns.tolist()}")
        
        # Get statistics
        stats = manager.get_statistics()
        print(f"\nStatistics:")
        for key, value in stats.items():
            if isinstance(value, (int, float)):
                print(f"  {key}: {value}")
        
        # Create splits
        train, val, test = manager.get_data_splits(
            test_size=0.2,
            val_size=0.1,
            stratify=True
        )
        
        # Save splits
        manager.save_splits(train, val, test)
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nPlease download the datasets first:")
        print(f"  CICIDS2017: {CICIDSDataLoader.REMOTE_URL}")
        print(f"  UNSW-NB15: {UNSWDataLoader.REMOTE_URL}")
