"""
End-to-End Integration Tests for X-IDS Framework

Tests the complete workflow:
1. Data generation/loading
2. Preprocessing
3. Imbalance handling
4. Model training
5. Inference
6. Evaluation
7. Explainability

Run with: pytest tests/test_e2e.py -v
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import time


class TestEndToEndWorkflow:
    """End-to-end workflow tests"""
    
    @pytest.fixture
    def config(self):
        """Full configuration for E2E test"""
        return {
            "preprocessing": {
                "handle_missing": True,
                "missing_strategy": "mean",
                "normalize": True,
                "normalization_method": "minmax",
                "encoding_method": "label"
            },
            "imbalance": {
                "method": "smote",
                "smote": {
                    "sampling_strategy": 0.5,
                    "k_neighbors": 5
                },
                "random_state": 42
            },
            "training": {
                "num_epochs": 3,  # Short for testing
                "batch_size": 32,
                "learning_rate": 0.001,
                "early_stopping_patience": 2,
                "verbose": 0
            },
            "random_forest": {
                "n_estimators": 10,  # Small for testing
                "max_depth": 10,
                "random_state": 42
            },
            "explainability": {
                "shap": {
                    "background_samples": 50
                },
                "lime": {
                    "num_samples": 100
                }
            }
        }
    
    @pytest.fixture
    def synthetic_data(self):
        """Generate synthetic network traffic data"""
        np.random.seed(42)
        
        n_samples = 500
        n_features = 20
        
        # Generate features
        X = pd.DataFrame(
            np.random.randn(n_samples, n_features),
            columns=[f'feature_{i}' for i in range(n_features)]
        )
        
        # Add some categorical features
        X['protocol'] = np.random.choice(['TCP', 'UDP', 'ICMP'], n_samples)
        X['flag'] = np.random.choice(['SYN', 'ACK', 'FIN', 'RST'], n_samples)
        
        # Create binary labels with imbalance (80% benign, 20% attack)
        y = np.concatenate([
            np.zeros(400, dtype=int),  # Benign
            np.ones(100, dtype=int)     # Attack
        ])
        
        # Shuffle
        indices = np.random.permutation(len(X))
        X = X.iloc[indices].reset_index(drop=True)
        y = y[indices]
        
        return X, y
    
    def test_complete_ml_pipeline(self, synthetic_data, config):
        """
        Test complete ML pipeline from raw data to predictions
        
        Steps:
        1. Load data
        2. Preprocess
        3. Handle imbalance
        4. Train model
        5. Evaluate
        6. Generate predictions
        """
        X, y = synthetic_data
        
        # Stratified split to maintain class distribution
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        print(f"\n📊 Data loaded: {len(X_train)} train, {len(X_test)} test samples")
        print(f"   Train class distribution: {np.bincount(y_train)}")
        print(f"   Test class distribution: {np.bincount(y_test)}")
        
        # Step 1: Preprocessing
        from xids.pipeline.preprocessing import DataPreprocessor
        
        preprocessor = DataPreprocessor(config=config)
        X_train_prep, feature_names = preprocessor.fit_transform(X_train)
        X_test_prep, _ = preprocessor.transform(X_test)
        
        assert X_train_prep.shape[0] == len(X_train)
        assert X_test_prep.shape[0] == len(X_test)
        print(f"✅ Preprocessing complete: {X_train_prep.shape[1]} features")
        
        # Step 2: Imbalance Handling
        from xids.pipeline.imbalance_handling import ImbalanceHandler
        
        handler = ImbalanceHandler(config=config)
        X_train_balanced, y_train_balanced = handler.fit_resample(X_train_prep, y_train)
        
        assert len(X_train_balanced) >= len(X_train_prep)
        print(f"✅ Imbalance handled: {len(X_train_balanced)} samples after SMOTE")
        
        # Step 3: Train Model
        from sklearn.ensemble import RandomForestClassifier
        from xids.training.trainer import ModelTrainer
        
        model = RandomForestClassifier(
            n_estimators=config['random_forest']['n_estimators'],
            max_depth=config['random_forest']['max_depth'],
            random_state=config['random_forest']['random_state']
        )
        
        trainer = ModelTrainer(model, config=config)
        history = trainer.train(
            X_train_balanced, y_train_balanced,
            model_type='rf'
        )
        
        assert 'train_accuracy' in history
        print(f"✅ Model trained: {history['train_accuracy'][0]:.4f} train accuracy")
        
        # Step 4: Inference
        y_pred = model.predict(X_test_prep)
        y_pred_proba = model.predict_proba(X_test_prep)[:, 1]
        
        assert len(y_pred) == len(y_test)
        print(f"✅ Inference complete: {len(y_pred)} predictions")
        
        # Step 5: Evaluation
        from xids.evaluation.metrics import EvaluationMetrics
        
        metrics = EvaluationMetrics.compute_metrics(y_test, y_pred, y_pred_proba)
        
        assert 'accuracy' in metrics
        assert 'f1_score' in metrics
        assert 'precision' in metrics
        assert 'recall' in metrics
        assert 'roc_auc' in metrics
        
        print(f"✅ Evaluation complete:")
        print(f"   Accuracy: {metrics['accuracy']:.4f}")
        print(f"   F1-Score: {metrics['f1_score']:.4f}")
        print(f"   Precision: {metrics['precision']:.4f}")
        print(f"   Recall: {metrics['recall']:.4f}")
        print(f"   ROC-AUC: {metrics['roc_auc']:.4f}")
        
        # Validate performance thresholds (very relaxed for small test data)
        assert metrics['accuracy'] > 0.5, f"Model accuracy too low: {metrics['accuracy']}"
        # F1 may be low with small test set and imbalanced data
        print(f"✅ Pipeline validation complete")
    
    def test_complete_pipeline_with_explainability(self, synthetic_data, config):
        """
        Test complete pipeline including explainability
        
        Steps:
        1-5: Same as above
        6. Generate SHAP explanations
        7. Validate explanation quality
        """
        X, y = synthetic_data
        
        # Stratified split
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Preprocessing
        from xids.pipeline.preprocessing import DataPreprocessor
        preprocessor = DataPreprocessor(config=config)
        X_train_prep, feature_names = preprocessor.fit_transform(X_train)
        X_test_prep, _ = preprocessor.transform(X_test)
        
        # Imbalance handling
        from xids.pipeline.imbalance_handling import ImbalanceHandler
        handler = ImbalanceHandler(config=config)
        X_train_balanced, y_train_balanced = handler.fit_resample(X_train_prep, y_train)
        
        # Train model
        from sklearn.ensemble import RandomForestClassifier
        model = RandomForestClassifier(
            n_estimators=config['random_forest']['n_estimators'],
            random_state=42,
            n_jobs=1
        )
        model.fit(X_train_balanced, y_train_balanced)
        
        print(f"\n🔍 Testing explainability...")
        
        # Test SHAP Explainability
        from xids.explainability.shap_explainer import SHAPExplainer
        
        shap_explainer = SHAPExplainer(model=model)
        
        # Fit explainer with background data
        background_samples = X_train_prep[:50]
        shap_explainer.fit(background_samples)
        
        # Explain a single instance
        start_time = time.time()
        explanation = shap_explainer.explain_instance(X_test_prep[0:1])
        shap_latency = (time.time() - start_time) * 1000
        
        assert explanation is not None
        assert 'shap_values' in explanation
        assert 'base_value' in explanation
        
        print(f"✅ SHAP explanation generated in {shap_latency:.2f}ms")
        assert shap_latency < 1000, f"SHAP too slow: {shap_latency}ms > 1000ms"
        
        # Test LIME Explainability
        from xids.explainability.lime_explainer import LIMEExplainer
        
        lime_explainer = LIMEExplainer(model=model, config=config)
        lime_explainer.fit(X_train_prep[:100], feature_names=feature_names)
        
        start_time = time.time()
        lime_explanation = lime_explainer.explain_instance(X_test_prep[0], num_features=10)
        lime_latency = (time.time() - start_time) * 1000
        
        assert lime_explanation is not None
        assert 'feature_weights' in lime_explanation
        assert 'intercept' in lime_explanation
        
        print(f"✅ LIME explanation generated in {lime_latency:.2f}ms")
        assert lime_latency < 2000, f"LIME too slow: {lime_latency}ms > 2000ms"
    
    def test_benchmarking_pipeline(self, synthetic_data, config):
        """
        Test benchmarking and performance measurement
        """
        X, y = synthetic_data
        
        # Prepare data with stratified split
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Quick preprocessing
        from xids.pipeline.preprocessing import DataPreprocessor
        preprocessor = DataPreprocessor(config=config)
        X_train_prep, _ = preprocessor.fit_transform(X_train)
        X_test_prep, _ = preprocessor.transform(X_test)
        
        # Train simple model
        from sklearn.ensemble import RandomForestClassifier
        model = RandomForestClassifier(n_estimators=5, random_state=42)
        model.fit(X_train_prep, y_train)
        
        print(f"\n⚡ Running benchmarks...")
        
        # Benchmark
        from xids.evaluation.benchmark import ModelBenchmark
        
        benchmarker = ModelBenchmark(config=config)
        results = benchmarker.benchmark_model(
            model,
            X_test_prep,
            y_test,
            batch_sizes=[16, 32],
            warmup_runs=2,
            num_runs=3
        )
        
        assert len(results) > 0
        
        for result in results:
            print(f"  Batch {result.batch_size}: "
                  f"{result.latency_ms:.2f}ms, "
                  f"{result.throughput_samples_per_sec:.0f} samples/sec")
            
            assert result.latency_ms > 0
            assert result.throughput_samples_per_sec > 0
            assert result.accuracy is not None
        
        # Generate report
        report = benchmarker.generate_report()
        assert "BENCHMARK REPORT" in report
        print(f"✅ Benchmark report generated")
    
    @pytest.mark.slow
    def test_model_persistence(self, synthetic_data, config):
        """Test model saving and loading"""
        import pickle
        
        X, y = synthetic_data
        
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Preprocess
        from xids.pipeline.preprocessing import DataPreprocessor
        preprocessor = DataPreprocessor(config=config)
        X_train_prep, _ = preprocessor.fit_transform(X_train)
        X_test_prep, _ = preprocessor.transform(X_test)
        
        # Train model
        from sklearn.ensemble import RandomForestClassifier
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X_train_prep, y_train)
        
        # Get original predictions
        pred_before = model.predict(X_test_prep)
        
        # Save model
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pkl') as f:
            pickle.dump(model, f)
            model_path = f.name
        
        # Load model
        with open(model_path, 'rb') as f:
            loaded_model = pickle.load(f)
        
        # Get predictions from loaded model
        pred_after = loaded_model.predict(X_test_prep)
        
        # Verify predictions match
        assert np.array_equal(pred_before, pred_after)
        print(f"✅ Model persistence verified")
        
        # Cleanup
        Path(model_path).unlink()


class TestDataPipelineEdgeCases:
    """Test edge cases in data pipeline"""
    
    def test_missing_values_handling(self):
        """Test preprocessing with missing values"""
        # Create data with missing values
        np.random.seed(42)
        X = pd.DataFrame({
            'f1': [1.0, 2.0, np.nan, 4.0, 5.0],
            'f2': [np.nan, 2.0, 3.0, 4.0, 5.0],
            'f3': [1.0, 2.0, 3.0, np.nan, 5.0]
        })
        
        from xids.pipeline.preprocessing import DataPreprocessor
        config = {
            "preprocessing": {
                "handle_missing": True,
                "missing_strategy": "mean",
                "normalize": True,
                "normalization_method": "minmax"
            }
        }
        
        preprocessor = DataPreprocessor(config=config)
        X_prep, _ = preprocessor.fit_transform(X)
        
        # Verify no NaN values after preprocessing
        assert not np.isnan(X_prep).any()
        print("✅ Missing values handled correctly")
    
    def test_extreme_imbalance(self):
        """Test imbalance handling with extreme ratios"""
        np.random.seed(42)
        
        # Create extremely imbalanced data (95% class 0, 5% class 1)
        X = np.random.randn(1000, 10)
        y = np.concatenate([np.zeros(950), np.ones(50)]).astype(int)
        
        from xids.pipeline.imbalance_handling import ImbalanceHandler
        config = {
            "imbalance": {
                "method": "smote",
                "smote": {"sampling_strategy": 0.5}
            }
        }
        
        handler = ImbalanceHandler(config=config)
        X_resampled, y_resampled = handler.fit_resample(X, y)
        
        # Check that minority class increased
        minority_before = (y == 1).sum()
        minority_after = (y_resampled == 1).sum()
        
        assert minority_after > minority_before
        print(f"✅ Extreme imbalance handled: {minority_before} → {minority_after} minority samples")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
