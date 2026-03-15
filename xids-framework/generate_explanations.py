#!/usr/bin/env python3
"""
SHAP Explainability Analysis for X-IDS Framework

Generate feature importance explanations for model predictions using SHAP.
Produces feature importance reports and visualizations for each alert.

Usage:
    python generate_explanations.py                  # Generate SHAP for TCN
    python generate_explanations.py --model vae      # For VAE
    python generate_explanations.py --samples 1000   # Use 1000 samples
    python generate_explanations.py --plot           # Generate visualizations
"""

import argparse
import logging
import json
from pathlib import Path
from typing import Dict, List
import numpy as np
import pandas as pd
from datetime import datetime
import shap

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('explanations.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add project to path
import sys
sys.path.insert(0, str(Path(__file__).parent))


def load_model_and_data(model_type: str, data_path: str, num_samples: int = 100):
    """Load trained model and sample data for explanation."""
    logger.info(f"Loading {model_type} model and data...")
    
    # Load data
    df = pd.read_csv(data_path)
    X = df.drop('Label', axis=1).values[:num_samples]
    y = df['Label'].values[:num_samples]
    feature_names = list(df.drop('Label', axis=1).columns)
    
    logger.info(f"Loaded {len(X)} samples with {len(feature_names)} features")
    
    # Load model
    model_path = Path('models') / f'trained_{model_type}_model.h5'
    if not model_path.exists():
        logger.warning(f"Model not found: {model_path}")
        return None, None, None, None
    
    try:
        from tensorflow.keras.models import load_model
        model = load_model(str(model_path))
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return None, None, None, None
    
    return model, X, y, feature_names


def generate_shap_explanations(
    model,
    X: np.ndarray,
    feature_names: List[str],
    model_type: str,
    num_background: int = 50
) -> Dict:
    """Generate SHAP explanations for model predictions."""
    
    logger.info(f"\nGenerating SHAP explanations for {model_type}...")
    logger.info(f"Using {num_background} samples for background data")
    
    try:
        # Create background data (subset for efficiency)
        background = shap.sample(X, min(num_background, len(X)), random_state=42)
        
        # Initialize SHAP explainer
        logger.info("Initializing KernelExplainer...")
        explainer = shap.KernelExplainer(model.predict, background)
        
        # Calculate SHAP values for sample predictions
        logger.info("Computing SHAP values...")
        shap_values = explainer.shap_values(X)
        
        # Get model predictions
        predictions = model.predict(X, verbose=0)
        pred_classes = np.argmax(predictions, axis=1) if len(predictions.shape) > 1 else predictions.flatten()
        
        # Aggregate feature importance
        if isinstance(shap_values, list):
            # Multiple outputs - take first class
            shap_vals = shap_values[0]
        else:
            shap_vals = shap_values
        
        # Calculate mean absolute SHAP values (global feature importance)
        mean_abs_shap = np.abs(shap_vals).mean(axis=0)
        feature_importance = {
            feature_names[i]: float(mean_abs_shap[i])
            for i in range(len(feature_names))
        }
        
        # Sort by importance
        sorted_importance = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
        
        logger.info("✅ Top 10 Most Important Features:")
        for i, (feature, importance) in enumerate(sorted_importance[:10], 1):
            logger.info(f"   {i}. {feature}: {importance:.4f}")
        
        # Create explanation records
        explanations = []
        for idx in range(len(X)):
            sample_shap = shap_vals[idx]
            top_features = sorted(
                [(feature_names[i], float(sample_shap[i])) for i in range(len(feature_names))],
                key=lambda x: abs(x[1]),
                reverse=True
            )[:5]  # Top 5 features
            
            explanations.append({
                'sample_id': idx,
                'prediction': int(pred_classes[idx]) if isinstance(pred_classes[idx], np.integer) else pred_classes[idx],
                'confidence': float(predictions[idx].max()) if len(predictions.shape) > 1 else float(predictions[idx]),
                'top_features': [{'feature': f, 'contribution': c} for f, c in top_features]
            })
        
        result = {
            'model_type': model_type,
            'num_samples': len(X),
            'num_features': len(feature_names),
            'global_feature_importance': dict(sorted_importance),
            'explanations': explanations,
            'timestamp': datetime.now().isoformat()
        }
        
        return result
    
    except Exception as e:
        logger.error(f"❌ Failed to generate SHAP explanations: {e}", exc_info=True)
        return {
            'model_type': model_type,
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


def save_explanations_csv(explanations: Dict, output_path: Path) -> None:
    """Save explanations as CSV for easy inspection."""
    logger.info(f"Saving explanations to {output_path}...")
    
    rows = []
    for exp in explanations.get('explanations', []):
        for feature_obj in exp.get('top_features', []):
            rows.append({
                'sample_id': exp['sample_id'],
                'prediction': exp['prediction'],
                'confidence': exp['confidence'],
                'feature': feature_obj['feature'],
                'contribution': feature_obj['contribution']
            })
    
    if rows:
        df = pd.DataFrame(rows)
        df.to_csv(output_path, index=False)
        logger.info(f"✅ Saved {len(df)} explanation records to {output_path}")
    else:
        logger.warning("No explanations to save")


def main():
    parser = argparse.ArgumentParser(
        description='Generate SHAP explanations for X-IDS models',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Generate SHAP explanations for TCN
  python generate_explanations.py
  
  # Generate for VAE with 500 samples
  python generate_explanations.py --model vae --samples 500
  
  # Generate with visualization
  python generate_explanations.py --plot
        '''
    )
    
    parser.add_argument(
        '--model',
        choices=['tcn', 'vae', 'rf'],
        default='tcn',
        help='Model to explain (default: tcn)'
    )
    parser.add_argument(
        '--samples',
        type=int,
        default=100,
        help='Number of samples for explanation (default: 100)'
    )
    parser.add_argument(
        '--data-path',
        type=str,
        default='./data/cicids2017_preprocessed.csv',
        help='Data path for explanations'
    )
    parser.add_argument(
        '--background-samples',
        type=int,
        default=50,
        help='Background samples for SHAP (default: 50)'
    )
    parser.add_argument(
        '--plot',
        action='store_true',
        help='Generate SHAP visualizations'
    )
    
    args = parser.parse_args()
    
    logger.info("="*70)
    logger.info("X-IDS SHAP Explainability Analysis")
    logger.info("="*70)
    logger.info(f"Model: {args.model}")
    logger.info(f"Samples: {args.samples}")
    
    # Load model and data
    model, X, y, feature_names = load_model_and_data(args.model, args.data_path, args.samples)
    
    if model is None:
        logger.error("Failed to load model")
        return
    
    # Generate SHAP explanations
    explanations = generate_shap_explanations(
        model, X, feature_names, args.model,
        num_background=args.background_samples
    )
    
    # Save results
    results_dir = Path('results')
    results_dir.mkdir(exist_ok=True)
    
    # Save JSON
    json_path = results_dir / f'{args.model}_shap_explanations.json'
    with open(json_path, 'w') as f:
        json.dump(explanations, f, indent=2)
    logger.info(f"✅ Saved explanations to {json_path}")
    
    # Save CSV
    csv_path = results_dir / f'{args.model}_shap_explanations.csv'
    save_explanations_csv(explanations, csv_path)
    
    logger.info(f"\n{'='*70}")
    logger.info("Explanation generation complete!")
    logger.info(f"{'='*70}")


if __name__ == '__main__':
    main()
