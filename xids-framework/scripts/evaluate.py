#!/usr/bin/env python3
"""
Model Evaluation Script for X-IDS Framework

Comprehensive evaluation of trained models:
- Confusion matrices
- Precision-recall curves
- ROC-AUC analysis
- F1-score comparison
- Latency profiling
- False positive analysis

Usage:
    python evaluate_models.py                    # Evaluate all models
    python evaluate_models.py --models tcn vae   # Evaluate specific models
    python evaluate_models.py --detailed         # Generate detailed reports
    python evaluate_models.py --plot             # Generate visualizations
"""

import argparse
import logging
import json
import pickle
from pathlib import Path
from typing import Dict, Tuple
import numpy as np
import pandas as pd
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('evaluation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add project to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from sklearn.metrics import (
    confusion_matrix, precision_score, recall_score, f1_score,
    roc_auc_score, precision_recall_curve, roc_curve, auc
)


def load_model_and_data(model_type: str, data_path: str, label_col: str = 'Label'):
    """Load trained model and test data."""
    logger.info(f"Loading {model_type} model and data...")
    
    # Load test data
    df = pd.read_csv(data_path)
    X_test = df.drop(label_col, axis=1).values
    y_test = df[label_col].values
    feature_names = list(df.drop(label_col, axis=1).columns)
    
    logger.info(f"Test set: {X_test.shape}")
    logger.info(f"Class distribution: {pd.Series(y_test).value_counts().to_dict()}")
    
    # Load model based on type
    if model_type == 'rf':
        model_path = Path('models') / f'trained_{model_type}_model.pkl'
        if not model_path.exists():
            logger.warning(f"Model not found: {model_path}")
            return None, None, None, None
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
    else:
        model_path = Path('models') / f'trained_{model_type}_model.h5'
        if not model_path.exists():
            logger.warning(f"Model not found: {model_path}")
            return None, None, None, None
        
        try:
            from tensorflow.keras.models import load_model
            model = load_model(str(model_path), compile=False)
            # Compile with default settings
            model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
        except Exception as e:
            logger.warning(f"Could not load model with compile=False, trying without loading: {e}")
            model = None
    
    return model, X_test, y_test, feature_names


def evaluate_model(
    model,
    X_test: np.ndarray,
    y_test: np.ndarray,
    model_type: str
) -> Dict:
    """Evaluate single model."""
    
    logger.info(f"\nEvaluating {model_type.upper()}...")
    
    try:
        # Get predictions
        if hasattr(model, 'predict'):
            # Check if it's a neural network model (keras)
            if hasattr(model, 'predict') and not isinstance(model, type(None)):
                try:
                    # Try with verbose for keras models
                    y_pred_proba = model.predict(X_test, verbose=0)
                except TypeError:
                    # Fallback for sklearn models
                    y_pred_proba = model.predict(X_test)
            else:
                y_pred_proba = model.predict(X_test)
            
            if len(y_pred_proba.shape) > 1 and y_pred_proba.shape[1] > 1:
                y_pred = np.argmax(y_pred_proba, axis=1)
            else:
                y_pred = (y_pred_proba > 0.5).astype(int).flatten()
        else:
            y_pred = model.predict(X_test)
            y_pred_proba = None
        
        # Convert string labels to numeric if needed
        unique_labels = np.unique(y_test)
        if isinstance(unique_labels[0], str):
            label_map = {label: i for i, label in enumerate(unique_labels)}
            y_test_numeric = np.array([label_map[label] for label in y_test])
            y_pred_numeric = np.array([label_map.get(label, 0) for label in y_pred])
        else:
            y_test_numeric = y_test
            y_pred_numeric = y_pred
        
        # Compute metrics
        cm = confusion_matrix(y_test_numeric, y_pred_numeric)
        precision = precision_score(y_test_numeric, y_pred_numeric, average='weighted', zero_division=0)
        recall = recall_score(y_test_numeric, y_pred_numeric, average='weighted', zero_division=0)
        f1 = f1_score(y_test_numeric, y_pred_numeric, average='weighted', zero_division=0)
        
        # ROC-AUC for binary classification
        try:
            if len(unique_labels) == 2:
                roc_auc = roc_auc_score(y_test_numeric, y_pred_proba[:, 1] if y_pred_proba is not None else y_pred_numeric)
            else:
                roc_auc = roc_auc_score(y_test_numeric, y_pred_proba if y_pred_proba is not None else y_pred_numeric, multi_class='ovr', zero_division=0)
        except:
            roc_auc = None
        
        # Confusion matrix analysis
        tn, fp, fn, tp = cm.ravel() if cm.size == 4 else (0, 0, 0, 0)
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0
        
        metrics = {
            'model_type': model_type,
            'accuracy': float((y_test_numeric == y_pred_numeric).mean()),
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1),
            'roc_auc': float(roc_auc) if roc_auc else None,
            'false_positive_rate': float(fpr),
            'false_negative_rate': float(fnr),
            'confusion_matrix': cm.tolist(),
            'true_negatives': int(tn) if tn else 0,
            'false_positives': int(fp) if fp else 0,
            'false_negatives': int(fn) if fn else 0,
            'true_positives': int(tp) if tp else 0,
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"✅ {model_type.upper()} Metrics:")
        logger.info(f"   Accuracy: {metrics['accuracy']:.4f}")
        logger.info(f"   Precision: {metrics['precision']:.4f}")
        logger.info(f"   Recall: {metrics['recall']:.4f}")
        logger.info(f"   F1-Score: {metrics['f1_score']:.4f}")
        if metrics['roc_auc']:
            logger.info(f"   ROC-AUC: {metrics['roc_auc']:.4f}")
        logger.info(f"   FPR: {metrics['false_positive_rate']:.4f}")
        logger.info(f"   FNR: {metrics['false_negative_rate']:.4f}")
        
        return metrics
    
    except Exception as e:
        logger.error(f"❌ Evaluation failed for {model_type}: {e}", exc_info=True)
        return {
            'model_type': model_type,
            'status': 'failed',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }


def benchmark_model(model, X_test: np.ndarray, model_type: str, num_samples: int = 100) -> Dict:
    """Benchmark model latency and throughput."""
    
    logger.info(f"Benchmarking {model_type} latency...")
    
    try:
        if model is None:
            return {'model_type': model_type, 'status': 'skipped'}
        
        import time
        # Sample data
        X_sample = X_test[:min(num_samples, len(X_test))]
        
        # Measure latency
        latencies = []
        for x in X_sample:
            start = time.time()
            if hasattr(model, 'predict'):
                try:
                    # Try with verbose for keras
                    _ = model.predict(x.reshape(1, -1), verbose=0)
                except TypeError:
                    # Fallback for sklearn
                    _ = model.predict(x.reshape(1, -1))
            else:
                _ = model.predict(x.reshape(1, -1))
            latencies.append(time.time() - start)
        
        latencies = np.array(latencies)
        
        metrics = {
            'model_type': model_type,
            'mean_latency_ms': float(np.mean(latencies) * 1000),
            'median_latency_ms': float(np.median(latencies) * 1000),
            'p95_latency_ms': float(np.percentile(latencies, 95) * 1000),
            'p99_latency_ms': float(np.percentile(latencies, 99) * 1000),
            'throughput_samples_per_sec': float(1.0 / np.mean(latencies)) if np.mean(latencies) > 0 else 0,
        }
        
        logger.info(f"✅ {model_type.upper()} Latency:")
        logger.info(f"   Mean: {metrics['mean_latency_ms']:.2f} ms")
        logger.info(f"   P95: {metrics['p95_latency_ms']:.2f} ms")
        logger.info(f"   Throughput: {metrics['throughput_samples_per_sec']:.0f} samples/sec")
        
        return metrics
    
    except Exception as e:
        logger.error(f"❌ Benchmarking failed for {model_type}: {e}", exc_info=True)
        return {
            'model_type': model_type,
            'status': 'failed',
            'error': str(e)
        }


def main():
    parser = argparse.ArgumentParser(
        description='Evaluate trained X-IDS models',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Evaluate all models
  python evaluate_models.py
  
  # Evaluate specific models with detailed output
  python evaluate_models.py --models tcn vae --detailed
  
  # Generate plots
  python evaluate_models.py --plot
        '''
    )
    
    parser.add_argument(
        '--models',
        nargs='+',
        choices=['tcn', 'vae', 'rf'],
        default=['tcn', 'vae', 'rf'],
        help='Models to evaluate (default: all)'
    )
    parser.add_argument(
        '--data-path',
        type=str,
        default='./data/cicids2017_preprocessed.csv',
        help='Test data path (default: CICIDS2017)'
    )
    parser.add_argument(
        '--detailed',
        action='store_true',
        help='Generate detailed reports'
    )
    parser.add_argument(
        '--plot',
        action='store_true',
        help='Generate visualizations'
    )
    parser.add_argument(
        '--benchmark',
        action='store_true',
        default=True,
        help='Run latency benchmarking'
    )
    
    args = parser.parse_args()
    
    logger.info("="*70)
    logger.info("X-IDS Model Evaluation Pipeline")
    logger.info("="*70)
    logger.info(f"Models to evaluate: {args.models}")
    logger.info(f"Test data: {args.data_path}")
    
    # Evaluation results
    evaluation_results = {
        'metrics': [],
        'benchmarks': [],
        'summary': {},
        'timestamp': datetime.now().isoformat()
    }
    
    # Evaluate each model
    for model_type in args.models:
        logger.info(f"\n{'#'*70}")
        logger.info(f"# Evaluating {model_type.upper()}")
        logger.info(f"{'#'*70}")
        
        # Load model and data
        model, X_test, y_test, feature_names = load_model_and_data(model_type, args.data_path)
        
        if model is None or X_test is None:
            logger.warning(f"Skipping {model_type} - model or data not available")
            continue
        
        # Evaluate
        metrics = evaluate_model(model, X_test, y_test, model_type)
        evaluation_results['metrics'].append(metrics)
        
        # Benchmark latency
        if args.benchmark:
            benchmark_metrics = benchmark_model(model, X_test, model_type)
            evaluation_results['benchmarks'].append(benchmark_metrics)
    
    # Compute summary comparison
    if evaluation_results['metrics']:
        logger.info(f"\n{'='*70}")
        logger.info("Model Comparison Summary")
        logger.info(f"{'='*70}")
        
        comparison_df = pd.DataFrame(evaluation_results['metrics'])
        logger.info(f"\n{comparison_df[['model_type', 'accuracy', 'precision', 'recall', 'f1_score']].to_string()}")
        
        evaluation_results['summary'] = {
            'best_f1_model': comparison_df.loc[comparison_df['f1_score'].idxmax(), 'model_type'] if 'f1_score' in comparison_df.columns else None,
            'best_accuracy_model': comparison_df.loc[comparison_df['accuracy'].idxmax(), 'model_type'] if 'accuracy' in comparison_df.columns else None,
        }
    
    # Save results
    results_path = Path('results/evaluation_report.json')
    results_path.parent.mkdir(parents=True, exist_ok=True)
    with open(results_path, 'w') as f:
        json.dump(evaluation_results, f, indent=2)
    logger.info(f"\n✅ Evaluation report saved to {results_path}")
    
    logger.info(f"\n{'='*70}")
    logger.info("Next steps:")
    logger.info("  1. Run: python generate_explanations.py")
    logger.info("  2. Run: python test_inference.py")
    logger.info("  3. Run: docker build -t x-ids:latest .")
    logger.info(f"{'='*70}")


if __name__ == '__main__':
    main()
