"""Pytest configuration and fixtures for X-IDS tests."""

import pytest
import numpy as np
import pandas as pd
import tempfile
from pathlib import Path


@pytest.fixture(scope="session")
def temp_dir():
    """Create temporary directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_dataset():
    """Create a sample dataset for testing."""
    np.random.seed(42)
    
    n_samples = 500
    n_features = 20
    
    X = pd.DataFrame(
        np.random.randn(n_samples, n_features),
        columns=[f'feature_{i}' for i in range(n_features)]
    )
    
    # Create binary labels with slight imbalance
    y = np.concatenate([
        np.zeros(400, dtype=int),
        np.ones(100, dtype=int)
    ])
    
    # Shuffle
    indices = np.random.permutation(len(X))
    X = X.iloc[indices].reset_index(drop=True)
    y = y[indices]
    
    return X, y


@pytest.fixture
def training_config():
    """Default training configuration for tests."""
    return {
        "training": {
            "num_epochs": 5,
            "batch_size": 32,
            "learning_rate": 0.001,
            "early_stopping_patience": 3,
            "verbose": 0
        },
        "preprocessing": {
            "handle_missing": True,
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
        "tcn": {
            "window_size": 30,
            "filters": [64, 128, 256],
            "kernel_size": 3,
            "dropout": 0.2
        },
        "autoencoder": {
            "encoder_dims": [50, 32, 16],
            "latent_dim": 16,
            "dropout": 0.2
        },
        "random_forest": {
            "n_estimators": 100,
            "max_depth": 20
        },
        "explainability": {
            "shap_background_samples": 50,
            "lime_num_samples": 1000
        }
    }


@pytest.fixture
def sklearn_model():
    """Create a pre-trained sklearn model for testing."""
    from sklearn.ensemble import RandomForestClassifier
    
    np.random.seed(42)
    X = np.random.randn(100, 20)
    y = np.random.choice([0, 1], 100)
    
    model = RandomForestClassifier(
        n_estimators=5,
        random_state=42,
        n_jobs=1
    )
    model.fit(X, y)
    
    return model


def pytest_addoption(parser):
    """Add custom command-line options."""
    parser.addoption(
        "--slow",
        action="store_true",
        default=False,
        help="run slow tests"
    )
    parser.addoption(
        "--gpu",
        action="store_true",
        default=False,
        help="run GPU tests"
    )


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers",
        "gpu: marks tests requiring GPU (deselect with '-m \"not gpu\"')"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection based on markers."""
    if not config.getoption("--slow"):
        skip_slow = pytest.mark.skip(reason="need --slow option to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)
    
    if not config.getoption("--gpu"):
        skip_gpu = pytest.mark.skip(reason="need --gpu option to run")
        for item in items:
            if "gpu" in item.keywords:
                item.add_marker(skip_gpu)


# Import for easier fixture access in tests
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
