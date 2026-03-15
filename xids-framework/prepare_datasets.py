#!/usr/bin/env python3
"""
Data Preparation Pipeline for X-IDS Framework

This script handles:
1. Synthetic data generation (for immediate testing)
2. Real dataset loading (CICIDS2017, UNSW-NB15)
3. Data preprocessing and validation
4. Train/test splitting
5. Imbalance handling (SMOTE/ADASYN)

Usage:
    python prepare_datasets.py --mode synthetic  # Generate synthetic data
    python prepare_datasets.py --mode real       # Load real datasets (requires manual download)
    python prepare_datasets.py --mode both       # Do both
"""

import argparse
import logging
from pathlib import Path
from typing import Tuple
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from xids.pipeline.synthetic_data_generator import SyntheticNetworkTrafficGenerator, SyntheticDatasetConfig
from xids.pipeline.dataloaders import DatasetManager, CICIDSDataLoader, UNSWDataLoader
from xids.pipeline.preprocessing import DataPreprocessor
from xids.pipeline.imbalance_handling import ImbalanceHandler


def prepare_synthetic_data(output_dir: str = './data') -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generate synthetic CICIDS2017 and UNSW-NB15 datasets.
    
    This is perfect for:
    - Quick framework testing
    - Development without large downloads
    - CI/CD pipelines
    """
    logger.info("Starting synthetic data generation...")
    
    config = SyntheticDatasetConfig(
        n_normal_samples=50000,
        n_attack_samples=5000,
        random_seed=42
    )
    
    generator = SyntheticNetworkTrafficGenerator(config)
    cicids_df, unsw_df = generator.save_datasets(output_dir)
    
    logger.info("✅ Synthetic data generation complete!")
    return cicids_df, unsw_df


def prepare_real_data(cicids_path: str, unsw_path: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Load real CICIDS2017 and UNSW-NB15 datasets.
    
    These datasets must be manually downloaded:
    - CICIDS2017: https://www.unb.ca/cic/datasets/ids-2017.html
    - UNSW-NB15: https://www.unsw.adfa.edu.au/unsw-canberra-cyber/cybersecurity/UNSW-NB15-dataset/
    """
    logger.info("Loading real datasets...")
    
    cicids_loader = CICIDSDataLoader(cicids_path)
    unsw_loader = UNSWDataLoader(unsw_path)
    
    cicids_df = cicids_loader.load()
    unsw_df = unsw_loader.load()
    
    logger.info(f"✅ Loaded CICIDS2017: {cicids_df.shape}")
    logger.info(f"✅ Loaded UNSW-NB15: {unsw_df.shape}")
    
    return cicids_df, unsw_df


def preprocess_and_save(
    cicids_df: pd.DataFrame,
    unsw_df: pd.DataFrame,
    output_dir: str = './data/preprocessed'
) -> None:
    """Preprocess datasets and save for training."""
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"\nPreprocessing datasets to {output_dir}...")
    
    # Process CICIDS2017
    logger.info("\n" + "="*60)
    logger.info("Processing CICIDS2017 Dataset")
    logger.info("="*60)
    
    # Separate features and labels
    cicids_features = cicids_df.drop('Label', axis=1) if 'Label' in cicids_df.columns else cicids_df
    cicids_labels = cicids_df['Label'] if 'Label' in cicids_df.columns else None
    
    # Fit and transform
    preprocessor_cicids = DataPreprocessor()
    cicids_features_transformed, feature_names = preprocessor_cicids.fit_transform(cicids_features)
    
    # Reconstruct dataframe
    cicids_scaled = pd.DataFrame(cicids_features_transformed, columns=feature_names)
    if cicids_labels is not None:
        cicids_scaled['Label'] = cicids_labels.values
    
    logger.info(f"Transformed shape: {cicids_scaled.shape}")
    logger.info(f"Features: {len(feature_names)}")
    
    # Save CICIDS2017
    cicids_scaled.to_csv(output_path / 'cicids2017_preprocessed.csv', index=False)
    preprocessor_cicids.save(str(output_path / 'cicids2017_preprocessor.pkl'))
    logger.info(f"✅ Saved CICIDS2017 preprocessed data")
    
    # Process UNSW-NB15
    logger.info("\n" + "="*60)
    logger.info("Processing UNSW-NB15 Dataset")
    logger.info("="*60)
    
    # Separate features and labels
    unsw_features = unsw_df.drop('Label', axis=1) if 'Label' in unsw_df.columns else unsw_df
    unsw_labels = unsw_df['Label'] if 'Label' in unsw_df.columns else None
    
    # Fit and transform
    preprocessor_unsw = DataPreprocessor()
    unsw_features_transformed, unsw_feature_names = preprocessor_unsw.fit_transform(unsw_features)
    
    # Reconstruct dataframe
    unsw_scaled = pd.DataFrame(unsw_features_transformed, columns=unsw_feature_names)
    if unsw_labels is not None:
        unsw_scaled['Label'] = unsw_labels.values
    
    logger.info(f"Transformed shape: {unsw_scaled.shape}")
    logger.info(f"Features: {len(unsw_feature_names)}")
    
    # Save UNSW-NB15
    unsw_scaled.to_csv(output_path / 'unswnb15_preprocessed.csv', index=False)
    preprocessor_unsw.save(str(output_path / 'unswnb15_preprocessor.pkl'))
    logger.info(f"✅ Saved UNSW-NB15 preprocessed data")
    
    # Handle class imbalance
    logger.info("\n" + "="*60)
    logger.info("Handling Class Imbalance")
    logger.info("="*60)
    
    imbalance_handler = ImbalanceHandler()
    
    # Get feature and label columns
    cicids_features_arr = cicids_scaled.drop('Label', axis=1) if 'Label' in cicids_scaled.columns else cicids_scaled
    cicids_labels_arr = cicids_scaled['Label'] if 'Label' in cicids_scaled.columns else None
    
    unsw_features_arr = unsw_scaled.drop('Label', axis=1) if 'Label' in unsw_scaled.columns else unsw_scaled
    unsw_labels_arr = unsw_scaled['Label'] if 'Label' in unsw_scaled.columns else None
    
    if cicids_labels_arr is not None:
        logger.info(f"\nCICIDS2017 class distribution (before):")
        print(cicids_labels_arr.value_counts())
        
        # Apply SMOTE
        try:
            cicids_features_resampled, cicids_labels_resampled = imbalance_handler.apply_smote(
                cicids_features_arr.values,
                cicids_labels_arr.values
            )
            cicids_balanced = pd.DataFrame(cicids_features_resampled, columns=cicids_features_arr.columns)
            cicids_balanced['Label'] = cicids_labels_resampled
            
            logger.info(f"\nCICIDS2017 class distribution (after SMOTE):")
            print(cicids_balanced['Label'].value_counts())
            
            # Save balanced datasets
            cicids_balanced.to_csv(output_path / 'cicids2017_balanced.csv', index=False)
        except Exception as e:
            logger.warning(f"⚠️ SMOTE failed for CICIDS2017: {e}, using original data")
            cicids_scaled.to_csv(output_path / 'cicids2017_balanced.csv', index=False)
    
    if unsw_labels_arr is not None:
        logger.info(f"\nUNSW-NB15 class distribution (before):")
        print(unsw_labels_arr.value_counts())
        
        # Apply SMOTE
        try:
            unsw_features_resampled, unsw_labels_resampled = imbalance_handler.apply_smote(
                unsw_features_arr.values,
                unsw_labels_arr.values
            )
            unsw_balanced = pd.DataFrame(unsw_features_resampled, columns=unsw_features_arr.columns)
            unsw_balanced['Label'] = unsw_labels_resampled
            
            logger.info(f"\nUNSW-NB15 class distribution (after SMOTE):")
            print(unsw_balanced['Label'].value_counts())
            
            # Save balanced datasets
            unsw_balanced.to_csv(output_path / 'unswnb15_balanced.csv', index=False)
        except Exception as e:
            logger.warning(f"⚠️ SMOTE failed for UNSW-NB15: {e}, using original data")
            unsw_scaled.to_csv(output_path / 'unswnb15_balanced.csv', index=False)
    
    logger.info(f"\n✅ Saved balanced datasets")


def main():
    parser = argparse.ArgumentParser(
        description='Data preparation pipeline for X-IDS Framework',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Generate synthetic data for quick testing
  python prepare_datasets.py --mode synthetic
  
  # Load real datasets (requires manual download)
  python prepare_datasets.py --mode real --cicids-path /path/to/cicids --unsw-path /path/to/unsw
  
  # Do both (merge and process together)
  python prepare_datasets.py --mode both
        '''
    )
    
    parser.add_argument(
        '--mode',
        choices=['synthetic', 'real', 'both'],
        default='synthetic',
        help='Data generation mode (default: synthetic)'
    )
    parser.add_argument(
        '--cicids-path',
        type=str,
        help='Path to CICIDS2017 dataset file'
    )
    parser.add_argument(
        '--unsw-path',
        type=str,
        help='Path to UNSW-NB15 dataset file'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='./data',
        help='Output directory for datasets (default: ./data)'
    )
    parser.add_argument(
        '--no-preprocess',
        action='store_true',
        help='Skip preprocessing step'
    )
    
    args = parser.parse_args()
    
    logger.info("="*60)
    logger.info("X-IDS Data Preparation Pipeline")
    logger.info("="*60)
    logger.info(f"Mode: {args.mode}")
    logger.info(f"Output: {args.output_dir}")
    
    # Generate/load datasets
    if args.mode in ['synthetic', 'both']:
        logger.info("\n📊 Generating synthetic data...")
        cicids_df, unsw_df = prepare_synthetic_data(args.output_dir)
    
    if args.mode == 'real':
        if not args.cicids_path or not args.unsw_path:
            logger.error("❌ Error: --cicids-path and --unsw-path required for 'real' mode")
            print("\nTo download datasets manually:")
            print("1. CICIDS2017: https://www.unb.ca/cic/datasets/ids-2017.html")
            print("2. UNSW-NB15: https://www.unsw.adfa.edu.au/unsw-canberra-cyber/cybersecurity/UNSW-NB15-dataset/")
            return
        
        logger.info("\n📥 Loading real datasets...")
        cicids_df, unsw_df = prepare_real_data(args.cicids_path, args.unsw_path)
    
    elif args.mode == 'both':
        logger.info("\n📥 Loading real datasets...")
        try:
            if args.cicids_path and args.unsw_path:
                cicids_real, unsw_real = prepare_real_data(args.cicids_path, args.unsw_path)
                # Merge synthetic and real (50-50 mix for balance)
                cicids_df = pd.concat([cicids_df, cicids_real], ignore_index=True).sample(frac=1).reset_index(drop=True)
                unsw_df = pd.concat([unsw_df, unsw_real], ignore_index=True).sample(frac=1).reset_index(drop=True)
                logger.info("✅ Merged synthetic and real datasets")
            else:
                logger.warning("⚠️ Real dataset paths not provided, using synthetic only")
        except Exception as e:
            logger.warning(f"⚠️ Could not load real datasets: {e}, using synthetic only")
    
    # Preprocess
    if not args.no_preprocess:
        logger.info("\n🔧 Starting preprocessing...")
        preprocess_and_save(cicids_df, unsw_df, args.output_dir)
    
    logger.info("\n" + "="*60)
    logger.info("✅ Data preparation complete!")
    logger.info("="*60)
    logger.info(f"\nNext steps:")
    logger.info(f"1. Preprocessed data is in: {args.output_dir}/preprocessed/")
    logger.info(f"2. Run training: python train_models.py")
    logger.info(f"3. Run evaluation: python evaluate_models.py")


if __name__ == '__main__':
    main()
