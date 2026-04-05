"""
Comprehensive test suite for X-IDS framework.

Includes unit tests for:
- Data loading and preprocessing
- Model training and inference
- Imbalance handling
- Explainability (SHAP, LIME)
- Evaluation metrics

Run with: pytest tests/
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import logging

logger = logging.getLogger(__name__)


class TestDataPreprocessor:
    """Test data preprocessing module."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing."""
        np.random.seed(42)
        X = pd.DataFrame({
            'feature_1': np.random.randn(100),
            'feature_2': np.random.randn(100),
            'feature_3': np.random.randn(100),
            'category': np.random.choice(['A', 'B', 'C'], 100)
        })
        y = np.random.choice([0, 1], 100)
        return X, y
    
    @pytest.fixture
    def preprocessor_config(self):
        """Configuration for preprocessor."""
        return {
            "preprocessing": {
                "handle_missing": True,
                "missing_strategy": "mean",
                "normalize": True,
                "normalization_method": "minmax",
                "encoding_method": "label",
                "feature_engineering": False
            }
        }
    
    def test_preprocessor_initialization(self, preprocessor_config):
        """Test preprocessor can be initialized."""
        from xids.pipeline.preprocessing import DataPreprocessor
        
        preprocessor = DataPreprocessor(config=preprocessor_config)
        assert preprocessor is not None
        assert preprocessor.config == preprocessor_config
    
    def test_fit_transform(self, sample_data, preprocessor_config):
        """Test fit_transform method."""
        from xids.pipeline.preprocessing import DataPreprocessor
        
        X, y = sample_data
        preprocessor = DataPreprocessor(config=preprocessor_config)
        
        X_transformed, feature_names = preprocessor.fit_transform(X)
        
        assert X_transformed.shape[0] == X.shape[0]
        assert len(feature_names) > 0
        assert preprocessor._is_fitted
    
    def test_inverse_transform(self, sample_data, preprocessor_config):
        """Test inverse transform."""
        from xids.pipeline.preprocessing import DataPreprocessor
        
        X, y = sample_data
        preprocessor = DataPreprocessor(config=preprocessor_config)
        
        X_transformed, _ = preprocessor.fit_transform(X)
        X_reconstructed = preprocessor.inverse_transform(X_transformed)
        
        assert X_reconstructed.shape == X_transformed.shape


class TestImbalanceHandler:
    """Test imbalance handling module."""
    
    @pytest.fixture
    def imbalanced_data(self):
        """Create imbalanced dataset."""
        np.random.seed(42)
        X = np.random.randn(1000, 20)
        # 80% class 0, 20% class 1
        y = np.concatenate([
            np.zeros(800, dtype=int),
            np.ones(200, dtype=int)
        ])
        indices = np.random.permutation(len(X))
        return X[indices], y[indices]
    
    @pytest.fixture
    def imbalance_config(self):
        """Configuration for imbalance handler."""
        return {
            "imbalance": {
                "method": "smote",
                "smote": {"sampling_strategy": 0.5},
                "random_state": 42
            }
        }
    
    def test_handler_initialization(self, imbalance_config):
        """Test imbalance handler initialization."""
        from xids.pipeline.imbalance_handling import ImbalanceHandler
        
        handler = ImbalanceHandler(config=imbalance_config)
        assert handler is not None
    
    def test_compute_class_weights(self, imbalanced_data):
        """Test class weight computation."""
        from xids.pipeline.imbalance_handling import ImbalanceHandler
        
        X, y = imbalanced_data
        weights = ImbalanceHandler.compute_class_weights(y)
        
        assert len(weights) == len(np.unique(y))
        assert all(w > 0 for w in weights.values())
        # Minority class should have higher weight
        assert weights[1] > weights[0]
    
    def test_smote_resampling(self, imbalanced_data, imbalance_config):
        """Test SMOTE resampling."""
        from xids.pipeline.imbalance_handling import ImbalanceHandler
        
        X, y = imbalanced_data
        handler = ImbalanceHandler(config=imbalance_config)
        
        X_resampled, y_resampled = handler.fit_resample(X, y)
        
        assert X_resampled.shape[0] > X.shape[0]  # More samples after resampling
        assert len(np.unique(y_resampled)) == len(np.unique(y))  # Same classes


class TestEvaluationMetrics:
    """Test evaluation metrics."""
    
    @pytest.fixture
    def predictions(self):
        """Create sample predictions and labels."""
        np.random.seed(42)
        y_true = np.array([0, 1, 1, 0, 1, 0, 1, 1, 0, 0])
        y_pred = np.array([0, 1, 1, 0, 0, 0, 1, 1, 1, 0])
        return y_true, y_pred
    
    def test_metrics_initialization(self):
        """Test metrics can be initialized."""
        from xids.evaluation.metrics import EvaluationMetrics
        
        metrics = EvaluationMetrics()
        assert metrics is not None
    
    def test_compute_metrics(self, predictions):
        """Test metric computation."""
        from xids.evaluation.metrics import EvaluationMetrics
        
        y_true, y_pred = predictions
        metrics = EvaluationMetrics()
        
        result = metrics.compute_metrics(y_true, y_pred)
        
        assert 'accuracy' in result
        assert 'precision' in result
        assert 'recall' in result
        assert 'f1_score' in result
        assert 0 <= result['accuracy'] <= 1
        assert 0 <= result['f1_score'] <= 1


class TestExplainability:
    """Test explainability modules."""
    
    @pytest.fixture
    def sample_model_and_data(self):
        """Create simple model and data for testing."""
        from sklearn.ensemble import RandomForestClassifier
        
        np.random.seed(42)
        X_train = np.random.randn(100, 10)
        y_train = np.random.choice([0, 1], 100)
        
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X_train, y_train)
        
        X_test = np.random.randn(10, 10)
        
        return model, X_train, X_test
    
    def test_shap_explainer_initialization(self, sample_model_and_data):
        """Test SHAP explainer initialization."""
        from xids.explainability.shap_explainer import SHAPExplainer
        
        model, X_train, X_test = sample_model_and_data
        explainer = SHAPExplainer(model=model)
        assert explainer is not None
        assert explainer.model is not None
    
    def test_lime_explainer_initialization(self, sample_model_and_data):
        """Test LIME explainer initialization."""
        from xids.explainability.lime_explainer import LIMEExplainer
        
        model, X_train, X_test = sample_model_and_data
        explainer = LIMEExplainer(model=model)
        assert explainer is not None
        assert explainer.model is not None


class TestDataLoaders:
    """Test data loading modules."""
    
    def test_dataloader_initialization(self):
        """Test dataloaders can be initialized."""
        from xids.pipeline.dataloaders import CICIDSDataLoader, UNSWDataLoader
        
        cicids = CICIDSDataLoader()
        unsw = UNSWDataLoader()
        
        assert cicids is not None
        assert unsw is not None
    
    def test_dataset_manager_initialization(self):
        """Test dataset manager initialization."""
        from xids.pipeline.dataloaders import DatasetManager
        
        manager = DatasetManager()
        assert manager is not None


class TestModelTrainer:
    """Test model training framework."""
    
    def test_trainer_initialization(self):
        """Test trainer can be initialized."""
        from xids.training.trainer import ModelTrainer, EarlyStoppingCallback
        
        # Create dummy model
        class DummyModel:
            def fit(self, X, y): pass
            def predict(self, X): return np.zeros(len(X))
        
        model = DummyModel()
        trainer = ModelTrainer(model)
        
        assert trainer is not None
    
    def test_early_stopping_callback(self):
        """Test early stopping callback."""
        from xids.training.trainer import EarlyStoppingCallback
        
        callback = EarlyStoppingCallback(
            monitor='val_loss',
            patience=5,
            mode='min'
        )
        
        assert callback is not None
        assert not callback.stopped


class TestBenchmarking:
    """Test benchmarking module."""
    
    @pytest.fixture
    def dummy_model(self):
        """Create dummy model for benchmarking."""
        from sklearn.ensemble import RandomForestClassifier
        
        np.random.seed(42)
        X = np.random.randn(100, 10)
        y = np.random.choice([0, 1], 100)
        
        model = RandomForestClassifier(n_estimators=5, random_state=42)
        model.fit(X, y)
        
        return model
    
    def test_benchmark_initialization(self):
        """Test benchmarker can be initialized."""
        from xids.evaluation.benchmark import ModelBenchmark
        
        benchmarker = ModelBenchmark()
        assert benchmarker is not None
    
    def test_benchmark_model(self, dummy_model):
        """Test benchmarking a model."""
        from xids.evaluation.benchmark import ModelBenchmark
        
        np.random.seed(42)
        X_test = np.random.randn(50, 10)
        
        benchmarker = ModelBenchmark()
        results = benchmarker.benchmark_model(
            dummy_model,
            X_test,
            batch_sizes=[16],
            warmup_runs=1,
            num_runs=2
        )
        
        assert len(results) > 0
        assert results[0].latency_ms > 0
        assert results[0].throughput_samples_per_sec > 0


class TestIntegration:
    """Integration tests for the full pipeline."""
    
    def test_full_pipeline(self):
        """Test full preprocessing to evaluation pipeline."""
        from xids.pipeline.preprocessing import DataPreprocessor
        from xids.pipeline.imbalance_handling import ImbalanceHandler
        from xids.evaluation.metrics import EvaluationMetrics
        from sklearn.ensemble import RandomForestClassifier
        
        np.random.seed(42)
        
        # Create data
        X = pd.DataFrame({
            'f1': np.random.randn(200),
            'f2': np.random.randn(200),
        })
        y = np.concatenate([np.zeros(150), np.ones(50)]).astype(int)
        
        # Preprocess
        prep_config = {
            "preprocessing": {
                "handle_missing": True,
                "normalize": True,
                "normalization_method": "minmax"
            }
        }
        preprocessor = DataPreprocessor(config=prep_config)
        X_processed, _ = preprocessor.fit_transform(X)
        
        # Handle imbalance
        imbalance_config = {
            "imbalance": {
                "method": "smote",
                "smote": {"sampling_strategy": 0.5}
            }
        }
        handler = ImbalanceHandler(config=imbalance_config)
        X_balanced, y_balanced = handler.fit_resample(X_processed, y)
        
        # Train
        model = RandomForestClassifier(n_estimators=5, random_state=42)
        model.fit(X_balanced, y_balanced)
        
        # Evaluate
        y_pred = model.predict(X_processed)
        metrics = EvaluationMetrics()
        results = metrics.compute_metrics(y, y_pred)
        
        assert 'accuracy' in results
        assert 'f1_score' in results


# Markers for different test categories
@pytest.mark.slow
def test_large_dataset():
    """Test with large dataset (marked as slow)."""
    pass


@pytest.mark.gpu
def test_gpu_available():
    """Test GPU availability (marked as gpu)."""
    pass


# Pytest configuration for markers
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "slow: marks tests as slow")
    config.addinivalue_line("markers", "gpu: marks tests requiring GPU")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
