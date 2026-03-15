# Getting Started with X-IDS

This guide helps you quickly get started with the X-IDS framework.

## Installation

### Prerequisites
- Python 3.8+
- pip or conda
- Git

### Step 1: Clone & Install

```bash
cd xids-framework
pip install -r requirements.txt
```

### Step 2: Verify Installation

```python
import xids
from xids.models import TemporalConvNetwork, VariationalAutoencoder, RandomForestBaseline
from xids.pipeline import DataPreprocessor, ImbalanceHandler
from xids.explainability import SHAPExplainer, LIMEExplainer
from xids.evaluation import EvaluationMetrics

print("✓ X-IDS installed successfully!")
```

---

## Quick Example: Using TCN Model

```python
import numpy as np
from xids.models import TemporalConvNetwork

# Initialize model with config
config = {
    "tcn": {
        "input_shape": [None, 50],
        "num_filters": 64,
        "num_layers": 3,
        "dropout": 0.3
    },
    "training": {
        "batch_size": 32,
        "num_epochs": 50,
        "learning_rate": 0.001
    }
}

# Create model instance
model = TemporalConvNetwork(config=config)

# Build architecture
model.build()

# Generate dummy data
X_train = np.random.randn(1000, 30, 50)  # 1000 samples, 30 timesteps, 50 features
y_train = np.random.randint(0, 2, 1000)  # Binary labels

# Train model
history = model.train(X_train, y_train, epochs=10)

# Make predictions
X_test = np.random.randn(100, 30, 50)
predictions = model.predict(X_test)

print(f"Predictions shape: {predictions.shape}")
print(f"Sample prediction: {predictions[0][0]:.4f}")  # Probability of attack
```

---

## Data Preprocessing Example

```python
import numpy as np
from xids.pipeline import DataPreprocessor, ImbalanceHandler

# Initialize preprocessor
config = {
    "preprocessing": {
        "normalize": True,
        "normalization_method": "minmax",
        "handle_missing": True,
        "missing_strategy": "mean"
    }
}

preprocessor = DataPreprocessor(config=config)

# Fit on training data
X_train_raw = np.random.randn(1000, 50)
preprocessor.fit(X_train_raw)

# Transform data
X_train_processed = preprocessor.transform(X_train_raw)

print(f"Original range: [{X_train_raw.min():.2f}, {X_train_raw.max():.2f}]")
print(f"Processed range: [{X_train_processed.min():.2f}, {X_train_processed.max():.2f}]")

# Apply SMOTE for class imbalance
imbalance_config = {
    "imbalance": {
        "method": "smote",
        "random_state": 42,
        "smote": {"k_neighbors": 5, "sampling_strategy": 0.3}
    }
}

handler = ImbalanceHandler(config=imbalance_config)
y_train = np.array([1]*50 + [0]*950)  # 5% attack class

X_balanced, y_balanced = handler.fit_resample(X_train_processed, y_train)

print(f"Original imbalance ratio: {np.sum(y_train==1) / len(y_train):.2%}")
print(f"Balanced imbalance ratio: {np.sum(y_balanced==1) / len(y_balanced):.2%}")
```

---

## Explainability Example

```python
import numpy as np
from xids.models import TemporalConvNetwork
from xids.explainability import SHAPExplainer, LIMEExplainer

# Assume model is trained
model = TemporalConvNetwork()
model.build()
model.train(X_train, y_train)  # From previous example

# Prepare background data for SHAP
X_background = np.random.randn(100, 30, 50)

# Initialize SHAP explainer
shap_config = {
    "explainability": {
        "shap": {
            "explainer_type": "kernel",
            "background_samples": 100,
            "num_samples": 2048
        }
    }
}

shap_explainer = SHAPExplainer(model, config=shap_config)
shap_explainer.fit(X_background)

# Explain an instance
x_instance = np.random.randn(30, 50)
shap_explanation = shap_explainer.explain_instance(x_instance)

print(f"Prediction: {shap_explanation['prediction']:.4f}")
print(f"Base value: {shap_explanation['base_value']}")
print(f"Elapsed time: {shap_explanation['elapsed_time_ms']:.0f}ms")

# Get global feature importance
feature_importance = shap_explainer.get_feature_importance(X_test)
print(f"\nTop 5 important features:")
for i, (feat, imp) in enumerate(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]):
    print(f"  {i+1}. {feat}: {imp:.4f}")

# Initialize LIME explainer
lime_config = {
    "explainability": {
        "lime": {
            "num_samples": 1000,
            "kernel_width": 0.25
        }
    }
}

lime_explainer = LIMEExplainer(model, config=lime_config)
lime_explainer.fit(X_background, feature_names=[f"feature_{i}" for i in range(50)])

# Explain instance with LIME
lime_explanation = lime_explainer.explain_instance(x_instance[0], num_features=10)

print(f"\nLIME Explanation:")
print(f"Prediction: {lime_explanation['prediction']:.4f}")
print(f"Top features: {lime_explanation['feature_weights']}")
print(f"Elapsed time: {lime_explanation['elapsed_time_ms']:.0f}ms")
```

---

## Evaluation Example

```python
import numpy as np
from xids.models import TemporalConvNetwork, RandomForestBaseline
from xids.evaluation import EvaluationMetrics, EvaluationReport

# Train models
tcn = TemporalConvNetwork(config)
tcn.build()
tcn.train(X_train, y_train)

rf = RandomForestBaseline(config)
rf.build()
rf.train(X_train.reshape(X_train.shape[0], -1), y_train)  # Reshape for RF

# Evaluate on test set
tcn_predictions = tcn.predict(X_test)
tcn_predictions_binary = (tcn_predictions > 0.5).astype(int).flatten()

rf_predictions = rf.predict(X_test.reshape(X_test.shape[0], -1))
rf_predictions_binary = (rf_predictions > 0.5).astype(int)

# Compute metrics
tcn_metrics = EvaluationMetrics.compute_metrics(y_test, tcn_predictions_binary, tcn_predictions.flatten())
rf_metrics = EvaluationMetrics.compute_metrics(y_test, rf_predictions_binary, rf_predictions)

# Generate comparison report
report = EvaluationReport()
report.add_model_results("TCN", tcn_metrics, 
                         EvaluationMetrics.confusion_matrix(y_test, tcn_predictions_binary))
report.add_model_results("Random Forest", rf_metrics,
                         EvaluationMetrics.confusion_matrix(y_test, rf_predictions_binary))

print(report.generate_comparison())
```

---

## Configuration Management

Edit `training/config.yaml` to customize:

```yaml
# Model Architecture
tcn:
  num_filters: 128        # Increase for more capacity
  num_layers: 5           # More layers = deeper model
  dropout: 0.4            # Increase to prevent overfitting

# Training
training:
  batch_size: 64          # Larger batches = faster training
  num_epochs: 200         # More epochs for convergence
  learning_rate: 0.0005   # Lower LR for finer adjustments

# Imbalance Handling
imbalance:
  method: "combined"      # "smote", "adasyn", or "combined"
  sampling_strategy: 0.5  # 50% of majority class
```

---

## Production Usage

### 1. Save Trained Model

```python
model.save("models/tcn-v1.0.h5")
```

### 2. Load for Inference

```python
from xids.models import TemporalConvNetwork

model = TemporalConvNetwork()
model.load("models/tcn-v1.0.h5")

# Make predictions
predictions = model.predict(X_new)
```

### 3. REST API (FastAPI)

```python
from fastapi import FastAPI
from xids.inference import Predictor

app = FastAPI()
predictor = Predictor(model_path="models/tcn-v1.0.h5")

@app.post("/predict")
async def predict(packet: dict):
    prediction = predictor.predict(packet)
    return {"confidence": float(prediction)}

@app.post("/explain")
async def explain(packet: dict):
    explanation = predictor.explain_with_shap(packet)
    return explanation
```

---

## Common Tasks

### Monitor Training Progress

```python
history = model.train(X_train, y_train, X_val, y_val)

import matplotlib.pyplot as plt
plt.plot(history['accuracy'])
plt.plot(history['val_accuracy'])
plt.legend(['train', 'validation'])
plt.show()
```

### Handle Missing Features

```python
from xids.pipeline import DataPreprocessor

config = {
    "preprocessing": {
        "handle_missing": True,
        "missing_strategy": "median"  # or "mean", "drop"
    }
}

preprocessor = DataPreprocessor(config)
X_clean = preprocessor.fit_transform(X_raw)
```

### Compare Models Side-by-Side

```python
models = {
    "TCN": TemporalConvNetwork(config),
    "VAE": VariationalAutoencoder(config),
    "RF": RandomForestBaseline(config)
}

for name, model in models.items():
    model.build()
    model.train(X_train, y_train)
    metrics = model.evaluate(X_test, y_test)
    print(f"{name}: F1={metrics['f1_score']:.4f}")
```

---

## Troubleshooting

### "Model not built" Error
```python
# Always build before training
model = TemporalConvNetwork()
model.build()  # ← Required
model.train(X_train, y_train)
```

### Out of Memory
```python
# Reduce batch size
config['training']['batch_size'] = 16  # Instead of 32

# Reduce model complexity
config['tcn']['num_filters'] = 32      # Instead of 64
```

### Slow Predictions
```python
# Use batch processing
predictions = model.predict(X_batch)  # ~28ms for 32 samples

# Not one at a time
# predictions = model.predict(X[i])   # ✗ Slower
```

---

## Next Steps

1. **Read Documentation**:
   - `docs/PROPOSAL.md` - Full technical specification
   - `docs/ARCHITECTURE.md` - System design details

2. **Prepare Data**:
   - Download CICIDS2017 and UNSW-NB15
   - Implement custom data loaders

3. **Train Models**:
   - Use `training/trainer.py` for unified training
   - Experiment with hyperparameters

4. **Deploy**:
   - Create Docker image
   - Deploy to Kubernetes
   - Integrate with SIEM

---

## API Reference Quick Links

- **Models**: `xids.models.BaseModel`, `TemporalConvNetwork`, `VariationalAutoencoder`, `RandomForestBaseline`
- **Pipeline**: `xids.pipeline.DataPreprocessor`, `ImbalanceHandler`
- **Explainability**: `xids.explainability.SHAPExplainer`, `LIMEExplainer`
- **Evaluation**: `xids.evaluation.EvaluationMetrics`, `EvaluationReport`

---

## Getting Help

- Check docstrings: `help(TemporalConvNetwork)`
- Review examples in this guide
- Read architecture docs: `docs/ARCHITECTURE.md`
- Open GitHub issues for bugs/features

---

**Happy threat hunting! 🛡️**
