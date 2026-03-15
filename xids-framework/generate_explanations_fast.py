#!/usr/bin/env python3
"""
Fast Explainability Analysis for X-IDS

Generate feature importance using:
- Model-based feature importance (RF permutation)
- Gradient-based explanations (neural networks)
- Statistical analysis of decision boundaries
"""

import argparse
import logging
import json
import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.preprocessing import LabelEncoder
from datetime import datetime
import tensorflow as tf

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_model_and_data(model_type: str, test_data_path: str = './data/cicids2017_preprocessed.csv'):
    """Load trained model and test data."""
    logger.info(f"Loading {model_type} model and test data...")
    
    # Load test data
    df = pd.read_csv(test_data_path)
    X_test = df.drop('Label', axis=1).values
    y_test = df['Label'].values
    feature_names = list(df.drop('Label', axis=1).columns)
    
    logger.info(f"Test set shape: {X_test.shape}")
    logger.info(f"Features: {len(feature_names)}")
    
    # Load model
    if model_type == 'rf':
        model_path = Path('models') / 'trained_rf_model.pkl'
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
    else:
        model_path = Path('models') / f'trained_{model_type}_model.h5'
        model = tf.keras.models.load_model(str(model_path), compile=False)
    
    return model, X_test, y_test, feature_names


def get_rf_feature_importance(model, feature_names):
    """Extract feature importance from Random Forest model."""
    logger.info("Extracting RF feature importance...")
    
    # Get importance from fitted forest
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]
    
    # Create feature importance dict
    importance_dict = {
        feature_names[i]: float(importances[i])
        for i in indices[:20]  # Top 20 features
    }
    
    return importance_dict, indices


def get_gradient_based_importance(model, X_test: np.ndarray, feature_names: list, num_samples: int = 100):
    """Compute gradient-based feature importance for neural networks."""
    logger.info("Computing gradient-based importance...")
    
    # Sample data
    X_sample = X_test[:min(num_samples, len(X_test))].astype(np.float32)
    
    # Compute gradients
    importance_scores = np.zeros(X_sample.shape[1])
    
    for i, x in enumerate(X_sample):
        x_tensor = tf.Variable(x.reshape(1, -1), dtype=tf.float32)
        
        with tf.GradientTape() as tape:
            predictions = model(x_tensor)
        
        # Get gradients w.r.t. input
        gradients = tape.gradient(predictions, x_tensor)
        
        if gradients is not None:
            # Use absolute gradients
            importance_scores += np.abs(gradients.numpy().flatten())
        
        if (i + 1) % 20 == 0:
            logger.info(f"  Processed {i+1}/{num_samples} samples...")
    
    # Normalize
    importance_scores = importance_scores / len(X_sample)
    indices = np.argsort(importance_scores)[::-1]
    
    # Create feature importance dict
    importance_dict = {
        feature_names[i]: float(importance_scores[i])
        for i in indices[:20]  # Top 20 features
    }
    
    return importance_dict, indices


def analyze_decision_boundaries(model, X_test: np.ndarray, y_test: np.ndarray, 
                                feature_names: list, model_type: str, num_samples: int = 100):
    """Analyze decision boundaries for important features."""
    logger.info("Analyzing decision boundaries...")
    
    X_sample = X_test[:min(num_samples, len(X_test))]
    y_sample = y_test[:min(num_samples, len(y_test))]
    
    # Get predictions
    if model_type == 'rf':
        predictions = model.predict(X_sample)
    else:
        predictions = np.argmax(model.predict(X_sample, verbose=0), axis=1)
    
    # Analyze per-feature statistics
    feature_stats = {}
    
    # Identify attack vs benign indices
    attack_mask = (predictions != 0)  # Assuming label 0 is benign
    benign_mask = (predictions == 0)
    
    for i, feature in enumerate(feature_names[:20]):  # Analyze top 20
        X_benign = X_sample[benign_mask, i]
        X_attack = X_sample[attack_mask, i]
        
        if len(X_benign) > 0 and len(X_attack) > 0:
            feature_stats[feature] = {
                'benign_mean': float(np.mean(X_benign)),
                'benign_std': float(np.std(X_benign)),
                'attack_mean': float(np.mean(X_attack)),
                'attack_std': float(np.std(X_attack)),
                'separability': float(abs(np.mean(X_attack) - np.mean(X_benign)) / (np.std(X_attack) + np.std(X_benign) + 1e-6))
            }
    
    return feature_stats


def generate_explanations_report(model, X_test: np.ndarray, y_test: np.ndarray,
                                 feature_names: list, model_type: str, output_dir: str = './results'):
    """Generate comprehensive explainability report."""
    
    logger.info(f"Generating explanations for {model_type}...")
    Path(output_dir).mkdir(exist_ok=True)
    
    report = {
        'model_type': model_type,
        'timestamp': datetime.now().isoformat(),
        'sample_size': len(X_test),
        'num_features': len(feature_names)
    }
    
    # Get feature importance
    if model_type == 'rf':
        importance_dict, indices = get_rf_feature_importance(model, feature_names)
    else:
        importance_dict, indices = get_gradient_based_importance(model, X_test, feature_names, num_samples=100)
    
    report['top_20_features'] = importance_dict
    
    # Analyze decision boundaries
    decision_boundaries = analyze_decision_boundaries(model, X_test, y_test, feature_names, model_type)
    report['decision_boundary_analysis'] = decision_boundaries
    
    # Save report
    report_path = Path(output_dir) / f'{model_type}_explanations.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"✅ Explanations saved to {report_path}")
    
    # Print summary
    logger.info(f"\n{'='*70}")
    logger.info(f"Feature Importance Summary ({model_type.upper()})")
    logger.info(f"{'='*70}")
    for i, (feature, importance) in enumerate(list(importance_dict.items())[:10], 1):
        logger.info(f"{i:2d}. {feature:30s} : {importance:.4f}")
    
    logger.info(f"\n{'='*70}")
    logger.info(f"Decision Boundary Analysis (Top 5 Separable Features)")
    logger.info(f"{'='*70}")
    
    # Sort by separability
    sorted_boundaries = sorted(decision_boundaries.items(), 
                              key=lambda x: x[1].get('separability', 0), 
                              reverse=True)[:5]
    
    for i, (feature, stats) in enumerate(sorted_boundaries, 1):
        sep = stats['separability']
        logger.info(f"{i}. {feature:30s}")
        logger.info(f"   Benign mean: {stats['benign_mean']:.4f} ± {stats['benign_std']:.4f}")
        logger.info(f"   Attack mean: {stats['attack_mean']:.4f} ± {stats['attack_std']:.4f}")
        logger.info(f"   Separability score: {sep:.4f}")
    
    return report


def main():
    parser = argparse.ArgumentParser(description='Generate explainability analysis for X-IDS models')
    parser.add_argument('--model', type=str, choices=['tcn', 'vae', 'rf'], 
                       help='Model to explain (default: all)', nargs='+')
    parser.add_argument('--test-data', type=str, default='./data/cicids2017_preprocessed.csv',
                       help='Test data path')
    parser.add_argument('--output-dir', type=str, default='./results',
                       help='Output directory for explanations')
    
    args = parser.parse_args()
    
    models_to_explain = args.model if args.model else ['tcn', 'vae', 'rf']
    
    logger.info("="*70)
    logger.info("X-IDS Explainability Analysis")
    logger.info("="*70)
    logger.info(f"Models to explain: {models_to_explain}")
    logger.info(f"Test data: {args.test_data}\n")
    
    # Load data once
    model, X_test, y_test, feature_names = load_model_and_data(models_to_explain[0], args.test_data)
    
    for model_type in models_to_explain:
        try:
            # Load model
            model, X_test, y_test, feature_names = load_model_and_data(model_type, args.test_data)
            
            # Generate explanations
            report = generate_explanations_report(model, X_test, y_test, feature_names, 
                                                  model_type, args.output_dir)
            
        except Exception as e:
            logger.error(f"❌ Failed to generate explanations for {model_type}: {e}", exc_info=True)
    
    logger.info("\n" + "="*70)
    logger.info("Explanations Complete!")
    logger.info(f"Check results/ directory for detailed reports")
    logger.info("="*70)


if __name__ == '__main__':
    main()
