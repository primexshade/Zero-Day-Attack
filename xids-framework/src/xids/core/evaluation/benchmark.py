"""
Comprehensive benchmarking suite for X-IDS models.

Provides performance evaluation including:
- Latency measurement (inference speed)
- Throughput testing (samples per second)
- Resource usage (memory, CPU)
- Model comparison reports
- Batch size optimization
- Accuracy metrics across dataset sizes

Classes:
    ModelBenchmark: Core benchmarking framework
    BenchmarkReport: Structured results and visualization
"""

import numpy as np
import time
import psutil
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Callable
import json
import logging
from dataclasses import dataclass, asdict
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    """Result of a single benchmark run."""
    model_name: str
    batch_size: int
    latency_ms: float
    throughput_samples_per_sec: float
    memory_mb: float
    cpu_percent: float
    accuracy: Optional[float] = None
    f1_score: Optional[float] = None


class ModelBenchmark:
    """
    Comprehensive benchmarking for X-IDS models.
    
    Measures:
    - Inference latency (ms per batch)
    - Throughput (samples/second)
    - Memory usage (MB)
    - CPU utilization (%)
    - Model accuracy
    - F1-score
    
    Attributes:
        results: List of BenchmarkResult objects
        config: Benchmark configuration
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize benchmarker.
        
        Args:
            config: Benchmark configuration
        """
        self.config = config or {}
        self.results: List[BenchmarkResult] = []
        self.process = psutil.Process(os.getpid())
    
    def benchmark_model(self,
                       model,
                       X_test: np.ndarray,
                       y_test: Optional[np.ndarray] = None,
                       batch_sizes: List[int] = None,
                       warmup_runs: int = 5,
                       num_runs: int = 10) -> List[BenchmarkResult]:
        """
        Benchmark a model across different batch sizes.
        
        Args:
            model: Model instance
            X_test: Test features
            y_test: Test labels (optional)
            batch_sizes: List of batch sizes to test
            warmup_runs: Number of warmup runs to exclude
            num_runs: Number of benchmark runs per batch size
            
        Returns:
            List of BenchmarkResult objects
        """
        if batch_sizes is None:
            batch_sizes = [1, 8, 16, 32, 64, 128]
        
        logger.info(f"Benchmarking {model.__class__.__name__}...")
        logger.info(f"Test set size: {len(X_test)} samples")
        logger.info(f"Batch sizes: {batch_sizes}")
        
        results = []
        
        for batch_size in batch_sizes:
            if batch_size > len(X_test):
                logger.warning(f"Batch size {batch_size} larger than test set, skipping")
                continue
            
            logger.info(f"Testing batch size: {batch_size}")
            
            # Prepare batches
            batches = self._create_batches(X_test, batch_size)
            
            # Warmup
            for _ in range(warmup_runs):
                _ = model.predict(batches[0])
            
            # Benchmark
            latencies = []
            memory_usage = []
            cpu_usage = []
            
            for batch in batches[:num_runs]:
                # Memory before
                self.process.memory_info()
                
                # Time prediction
                start_time = time.perf_counter()
                predictions = model.predict(batch)
                end_time = time.perf_counter()
                
                latency_ms = (end_time - start_time) * 1000
                latencies.append(latency_ms)
                
                # Resource usage
                memory_info = self.process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                memory_usage.append(memory_mb)
                
                try:
                    cpu_pct = self.process.cpu_percent(interval=0.1)
                except:
                    cpu_pct = 0
                cpu_usage.append(cpu_pct)
            
            # Compute statistics
            mean_latency = np.mean(latencies)
            throughput = (batch_size * 1000) / mean_latency  # samples/sec
            mean_memory = np.mean(memory_usage)
            mean_cpu = np.mean(cpu_usage)
            
            # Compute accuracy if labels provided
            accuracy = None
            f1_score = None
            
            if y_test is not None:
                all_predictions = []
                for batch in batches:
                    all_predictions.extend(model.predict(batch))
                
                all_predictions = np.array(all_predictions).flatten()
                if all_predictions.max() <= 1:
                    all_predictions = (all_predictions > 0.5).astype(int)
                
                accuracy = (all_predictions[:len(y_test)] == y_test).mean()
                
                # Simple F1-score
                tp = ((all_predictions[:len(y_test)] == 1) & (y_test == 1)).sum()
                fp = ((all_predictions[:len(y_test)] == 1) & (y_test == 0)).sum()
                fn = ((all_predictions[:len(y_test)] == 0) & (y_test == 1)).sum()
                
                precision = tp / (tp + fp) if (tp + fp) > 0 else 0
                recall = tp / (tp + fn) if (tp + fn) > 0 else 0
                f1_score = 2 * (precision * recall) / (precision + recall) \
                           if (precision + recall) > 0 else 0
            
            result = BenchmarkResult(
                model_name=model.__class__.__name__,
                batch_size=batch_size,
                latency_ms=mean_latency,
                throughput_samples_per_sec=throughput,
                memory_mb=mean_memory,
                cpu_percent=mean_cpu,
                accuracy=accuracy,
                f1_score=f1_score
            )
            
            results.append(result)
            self.results.append(result)
            
            logger.info(f"  Latency: {mean_latency:.2f}ms")
            logger.info(f"  Throughput: {throughput:.0f} samples/sec")
            logger.info(f"  Memory: {mean_memory:.1f} MB")
            logger.info(f"  CPU: {mean_cpu:.1f}%")
            if accuracy is not None:
                logger.info(f"  Accuracy: {accuracy:.4f}")
                logger.info(f"  F1-score: {f1_score:.4f}")
        
        return results
    
    def benchmark_multiple_models(self,
                                 models: Dict[str, object],
                                 X_test: np.ndarray,
                                 y_test: Optional[np.ndarray] = None,
                                 **kwargs) -> pd.DataFrame:
        """
        Benchmark multiple models and return comparison.
        
        Args:
            models: Dictionary mapping model names to model instances
            X_test: Test features
            y_test: Test labels
            **kwargs: Additional arguments for benchmark_model
            
        Returns:
            DataFrame with comparison results
        """
        logger.info(f"Benchmarking {len(models)} models...")
        
        all_results = []
        for name, model in models.items():
            results = self.benchmark_model(model, X_test, y_test, **kwargs)
            all_results.extend(results)
        
        return self._results_to_dataframe(all_results)
    
    def benchmark_dataset_sizes(self,
                               model,
                               X_test: np.ndarray,
                               y_test: Optional[np.ndarray] = None,
                               size_fractions: List[float] = None) -> pd.DataFrame:
        """
        Benchmark model on different dataset sizes to measure scalability.
        
        Args:
            model: Model instance
            X_test: Test features
            y_test: Test labels
            size_fractions: Fractions of test set to use [0.1, 0.5, 1.0]
            
        Returns:
            DataFrame with scalability results
        """
        if size_fractions is None:
            size_fractions = [0.1, 0.25, 0.5, 0.75, 1.0]
        
        logger.info("Benchmarking dataset scalability...")
        
        results = []
        for fraction in size_fractions:
            size = int(len(X_test) * fraction)
            X_subset = X_test[:size]
            y_subset = y_test[:size] if y_test is not None else None
            
            logger.info(f"Testing with {fraction*100:.0f}% of data ({size} samples)...")
            
            batch_results = self.benchmark_model(
                model, X_subset, y_subset,
                batch_sizes=[32],
                warmup_runs=2,
                num_runs=5
            )
            results.extend(batch_results)
        
        return self._results_to_dataframe(results)
    
    def _create_batches(self, X: np.ndarray, batch_size: int) -> List[np.ndarray]:
        """Create batches from data."""
        batches = []
        for i in range(0, len(X), batch_size):
            batches.append(X[i:i+batch_size])
        return batches
    
    def _results_to_dataframe(self, results: List[BenchmarkResult]) -> pd.DataFrame:
        """Convert results to DataFrame."""
        data = [asdict(r) for r in results]
        return pd.DataFrame(data)
    
    def generate_report(self, output_path: str = None) -> str:
        """
        Generate human-readable benchmark report.
        
        Args:
            output_path: Path to save report (optional)
            
        Returns:
            Report as string
        """
        if not self.results:
            return "No benchmark results available"
        
        df = self._results_to_dataframe(self.results)
        
        report = "=" * 80 + "\n"
        report += "MODEL BENCHMARK REPORT\n"
        report += "=" * 80 + "\n\n"
        
        # Summary by model
        for model_name in df['model_name'].unique():
            model_df = df[df['model_name'] == model_name]
            
            report += f"\n{model_name}\n"
            report += "-" * 40 + "\n"
            
            # Best batch size
            best_idx = model_df['throughput_samples_per_sec'].idxmax()
            best_result = model_df.loc[best_idx]
            
            report += f"Best Configuration (Batch Size: {best_result['batch_size']}):\n"
            report += f"  Latency: {best_result['latency_ms']:.2f}ms\n"
            report += f"  Throughput: {best_result['throughput_samples_per_sec']:.0f} samples/sec\n"
            report += f"  Memory: {best_result['memory_mb']:.1f} MB\n"
            report += f"  CPU: {best_result['cpu_percent']:.1f}%\n"
            
            if best_result['accuracy'] is not None:
                report += f"  Accuracy: {best_result['accuracy']:.4f}\n"
                report += f"  F1-Score: {best_result['f1_score']:.4f}\n"
            
            # Batch size comparison
            report += f"\nBatch Size Scaling:\n"
            for _, row in model_df.iterrows():
                report += f"  Size {row['batch_size']:3d}: " \
                         f"{row['latency_ms']:6.2f}ms | " \
                         f"{row['throughput_samples_per_sec']:7.0f} samples/sec\n"
        
        # Model comparison
        report += "\n" + "=" * 80 + "\n"
        report += "MODEL COMPARISON\n"
        report += "=" * 80 + "\n\n"
        
        # Best result per model
        best_per_model = df.loc[df.groupby('model_name')['throughput_samples_per_sec'].idxmax()]
        
        report += f"{'Model':<20} {'Latency':<12} {'Throughput':<15} {'Memory':<10}\n"
        report += "-" * 60 + "\n"
        
        for _, row in best_per_model.iterrows():
            report += f"{row['model_name']:<20} " \
                     f"{row['latency_ms']:>8.2f}ms {row['throughput_samples_per_sec']:>10.0f}/s " \
                     f"{row['memory_mb']:>8.1f}MB\n"
        
        report += "\n" + "=" * 80 + "\n"
        
        if output_path:
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w') as f:
                f.write(report)
            logger.info(f"Report saved to {output_path}")
        
        return report
    
    def save_results(self, filepath: str) -> None:
        """Save benchmark results to JSON."""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        
        data = [asdict(r) for r in self.results]
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Results saved to {filepath}")
    
    def load_results(self, filepath: str) -> None:
        """Load benchmark results from JSON."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.results = [BenchmarkResult(**item) for item in data]
        logger.info(f"Loaded {len(self.results)} results from {filepath}")


# Convenience function
def benchmark_models(models: Dict[str, object],
                    X_test: np.ndarray,
                    y_test: Optional[np.ndarray] = None,
                    config: Dict = None) -> pd.DataFrame:
    """
    Convenience function to quickly benchmark multiple models.
    
    Args:
        models: Dictionary of model name -> model instance
        X_test: Test features
        y_test: Test labels
        config: Configuration dictionary
        
    Returns:
        DataFrame with benchmark results
    """
    benchmarker = ModelBenchmark(config)
    return benchmarker.benchmark_multiple_models(models, X_test, y_test)
