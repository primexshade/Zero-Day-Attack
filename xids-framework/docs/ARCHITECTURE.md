# X-IDS System Architecture & Design

**Document Version**: 1.0  
**Date**: March 2026

---

## 1. High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      X-IDS Framework                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    Data Sources                              │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │  │
│  │  │  CICIDS2017  │  │ UNSW-NB15    │  │  Live Traffic    │   │  │
│  │  │  (Training)  │  │ (Training)   │  │  (Production)    │   │  │
│  │  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘   │  │
│  └─────────┼──────────────────┼──────────────────┼───────────────┘  │
│            │                  │                  │                   │
│  ┌─────────▼──────────────────▼──────────────────▼───────────────┐  │
│  │            Data Pipeline & Preprocessing                      │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │  │
│  │  │  Data Loader │  │ Preprocessing│  │ Feature Engineer │   │  │
│  │  │  & Validation│  │ (Normalize)  │  │  & Selection     │   │  │
│  │  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘   │  │
│  │         └──────────────────┼──────────────────┘              │  │
│  │                            │                                 │  │
│  │                   ┌────────▼────────┐                       │  │
│  │                   │ Class Imbalance │                       │  │
│  │                   │ (SMOTE/ADASYN)  │                       │  │
│  │                   └────────┬────────┘                       │  │
│  └────────────────────────────┼────────────────────────────────┘  │
│                                │                                   │
│  ┌────────────────────────────▼────────────────────────────────┐  │
│  │            Model Training & Evaluation                       │  │
│  │                                                              │  │
│  │  ┌─────────────────────┐  ┌──────────────────────────────┐  │  │
│  │  │   Deep Learning     │  │   Baseline Comparison        │  │  │
│  │  │                     │  │                              │  │  │
│  │  │  ┌────────────────┐ │  │  ┌────────────────────────┐  │  │  │
│  │  │  │  TCN (Primary) │ │  │  │  Random Forest (SigID) │  │  │  │
│  │  │  └────────────────┘ │  │  └────────────────────────┘  │  │  │
│  │  │                     │  │                              │  │  │
│  │  │  ┌────────────────┐ │  │                              │  │  │
│  │  │  │ VAE (Anomaly)  │ │  │                              │  │  │
│  │  │  └────────────────┘ │  │                              │  │  │
│  │  └─────────┬───────────┘  └──────────────┬───────────────┘  │  │
│  │            │                            │                   │  │
│  │            └────────────┬────────────────┘                   │  │
│  │                         │                                    │  │
│  │                ┌────────▼────────┐                          │  │
│  │                │ Evaluation &    │                          │  │
│  │                │ Benchmarking    │                          │  │
│  │                │ (Metrics, ROC)  │                          │  │
│  │                └────────┬────────┘                          │  │
│  └────────────────────────┼─────────────────────────────────┘  │
│                           │                                    │
│  ┌────────────────────────▼─────────────────────────────────┐  │
│  │           Explainability Layer                           │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  SHAP (Global Feature Importance)                  │  │  │
│  │  │  - Kernel Explainer (~400ms per alert)             │  │  │
│  │  │  - Feature attribution via Shapley values          │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  LIME (Local Interpretability)                      │  │  │
│  │  │  - Per-instance explanation (~150ms)               │  │  │
│  │  │  - Local linear approximation                      │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └────────────────────┬─────────────────────────────────────┘  │
│                       │                                        │
│  ┌────────────────────▼─────────────────────────────────────┐  │
│  │         Real-Time Inference Engine                       │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  Predictor Service                                 │  │  │
│  │  │  - TCN + VAE ensemble                              │  │  │
│  │  │  - Batch processing (batch_size=32)                │  │  │
│  │  │  - <100ms latency per batch                        │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │                                                          │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  Alert Generator                                   │  │  │
│  │  │  - Threshold: 0.7 (70% confidence)                │  │  │
│  │  │  - Severity scoring                                │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └────────────────────┬─────────────────────────────────────┘  │
│                       │                                        │
│  ┌────────────────────▼─────────────────────────────────────┐  │
│  │            Output & Integration Layer                    │  │
│  │                                                          │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │  │
│  │  │ Kafka Stream │  │ SIEM/API     │  │ Logging      │   │  │
│  │  │ (Streaming)  │  │ (REST/GRPC)  │  │ & Archival   │   │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │  │
│  │                                                          │  │
│  │  ┌──────────────────────────────────────────────────┐   │  │
│  │  │ SOC Dashboard                                    │   │  │
│  │  │ - Real-time alerts                              │   │  │
│  │  │ - Explanations & trends                         │   │  │
│  │  │ - Threat intelligence                           │   │  │
│  │  └──────────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Component Architecture

### 2.1 Data Pipeline Module

```
data/
├── dataloaders.py
│   └── Classes:
│       ├── CICIDSLoader: Download, parse CICIDS2017
│       ├── UNSWLoader: Download, parse UNSW-NB15
│       └── LiveTrafficLoader: Real-time packet capture
├── preprocessing.py
│   └── DataPreprocessor: Normalization, feature scaling
└── feature_engineering.py
    └── FeatureExtractor: Derive flow-level features
```

**Data Flow**:
```
Raw Packets/Flows
    ↓
[CICIDSLoader | UNSWLoader | LiveTrafficLoader]
    ↓
Raw DataFrames (missing values, mixed scales)
    ↓
DataPreprocessor (normalize, impute)
    ↓
Processed Features (standardized ranges)
    ↓
[Train/Val/Test Split]
    ↓
Ready for Model Training
```

### 2.2 Model Module

```
models/
├── base_model.py
│   └── BaseModel: Abstract interface
├── tcn_model.py
│   └── TemporalConvNetwork: TCN classifier
├── autoencoder_model.py
│   └── VariationalAutoencoder: VAE anomaly detector
└── baseline_rf.py
    └── RandomForestBaseline: Signature-based baseline
```

**Model Interface**:
```python
class BaseModel(ABC):
    def build() → None              # Construct architecture
    def train() → Dict              # Train with data
    def predict() → np.ndarray      # Inference
    def evaluate() → Dict[str, float]  # Test metrics
    def save() → None               # Persistence
    def load() → None               # Load from disk
```

### 2.3 Explainability Module

```
explainability/
├── shap_explainer.py
│   └── SHAPExplainer: Global feature importance
└── lime_explainer.py
    └── LIMEExplainer: Local instance explanations
```

**Explainability Pipeline**:
```
Alert Prediction
    ├─→ [If pred > θ]
    │       ├─→ SHAP: Which features matter globally?
    │       ├─→ LIME: Which features drove this instance?
    │       └─→ Generate Report (SHAP + LIME)
    └─→ [If pred ≤ θ]
        └─→ Log & Continue
```

### 2.4 Evaluation Module

```
evaluation/
├── metrics.py
│   ├── EvaluationMetrics: Precision, Recall, F1, ROC-AUC
│   └── EvaluationReport: Comparative report generation
└── benchmark.py
    └── BenchmarkRunner: Full model evaluation suite
```

**Evaluation Outputs**:
- Confusion matrices
- Precision-Recall curves
- ROC-AUC curves
- F1-score comparison
- Latency profiling

### 2.5 Training Module

```
training/
├── trainer.py
│   └── Trainer: Unified training orchestrator
├── callbacks.py
│   ├── EarlyStopping
│   └── ReduceLROnPlateau
├── config.yaml
│   └── All hyperparameters & configuration
└── loss_functions.py
    ├── Custom loss functions
    └── Class weighting strategies
```

### 2.6 Inference Module

```
inference/
├── predictor.py
│   └── Predictor: Load models, make predictions
├── realtime_handler.py
│   └── RealtimeHandler: Stream processing pipeline
├── packet_parser.py
│   └── Parse raw network packets
└── alert_generator.py
    └── Generate alerts & notifications
```

---

## 3. Data Flow Diagrams

### 3.1 Training Flow

```
                    ┌─────────────────────┐
                    │  Raw Datasets       │
                    │  (CICIDS2017,       │
                    │   UNSW-NB15)        │
                    └──────────┬──────────┘
                               │
                      ┌────────▼────────┐
                      │  Data Loading   │
                      │  & Validation   │
                      └────────┬────────┘
                               │
                    ┌──────────▼──────────┐
                    │ Preprocessing      │
                    │ - Normalize        │
                    │ - Handle Missing   │
                    │ - Scale Features   │
                    └──────────┬─────────┘
                               │
                    ┌──────────▼──────────┐
                    │ Class Imbalance     │
                    │ - Apply SMOTE       │
                    │ - Apply ADASYN      │
                    └──────────┬─────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
    ┌─────────▼──────┐  ┌─────▼──────┐  ┌────▼──────┐
    │ Train TCN      │  │ Train VAE  │  │ Train RF  │
    │ (70% data)     │  │ (70% data) │  │ (70% data)│
    └────────┬───────┘  └─────┬──────┘  └────┬─────┘
             │                │              │
             └────────┬───────┴──────────────┘
                      │
           ┌──────────▼──────────┐
           │ Validation Loop     │
           │ - Check metrics     │
           │ - Early stopping    │
           └──────────┬──────────┘
                      │
           ┌──────────▼──────────┐
           │ Save Models         │
           │ - Checkpoints       │
           │ - Final artifacts   │
           └──────────┬──────────┘
                      │
           ┌──────────▼──────────────┐
           │ Evaluation (20% test)   │
           │ - Metrics               │
           │ - Confusion Matrix      │
           │ - ROC Curves            │
           └─────────────────────────┘
```

### 3.2 Inference Flow (Production)

```
┌──────────────────────────────────────────┐
│         Network Traffic                  │
│  (Live packets from app)                 │
└────────────┬─────────────────────────────┘
             │
      ┌──────▼──────┐
      │ Packet      │
      │ Capture &   │
      │ Parse       │
      └──────┬──────┘
             │
    ┌────────▼─────────┐
    │ Preprocess       │
    │ - Normalize      │
    │ - Aggregate Flow │
    └────────┬─────────┘
             │
      ┌──────▼──────────────────┐
      │  Model Inference        │
      │  - TCN prediction       │
      │  - VAE anomaly score    │
      │  - Ensemble decision    │
      │  (< 100ms)              │
      └──────┬─────────────────┘
             │
         ┌───▼────┐
         │Alert?  │
         └───┬────┘
             │
         ┌───▼───────────────────┐
         │                       │
         NO                      YES
         │                       │
         │              ┌────────▼────────┐
         │              │ Generate Alert  │
         │              │ - Score         │
         │              │ - Confidence    │
         │              │ - Threat Level  │
         │              └────────┬────────┘
         │                       │
         │              ┌────────▼────────────┐
         │              │ Explanation (< 500ms)
         │              │ - SHAP (400ms)      │
         │              │ - LIME (150ms)      │
         │              └────────┬────────────┘
         │                       │
         │              ┌────────▼────────┐
         │              │ Publish Alert   │
         │              │ - Kafka Topic   │
         │              │ - SIEM Hook     │
         │              │ - Webhook       │
         │              └────────┬────────┘
         │                       │
         └───────┬───────────────┘
                 │
          ┌──────▼──────┐
          │ Log & Store │
          │ - Metrics   │
          │ - Evidence  │
          └─────────────┘
```

---

## 4. Deployment Architecture

### 4.1 Kubernetes Pod Layout

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app-with-xids-sidecar
spec:
  containers:
  
  # Primary Application Container
  - name: app
    image: my-app:latest
    ports:
    - containerPort: 8080
    
  # X-IDS Sidecar Container
  - name: x-ids
    image: x-ids:latest
    ports:
    - containerPort: 9000  # Metrics/Health
    resources:
      requests:
        cpu: "500m"
        memory: "512Mi"
      limits:
        cpu: "1000m"
        memory: "1Gi"
    env:
    - name: X_IDS_MODEL
      value: "/models/tcn-latest.h5"
    - name: X_IDS_THRESHOLD
      value: "0.7"
    volumeMounts:
    - name: models
      mountPath: /models
    - name: config
      mountPath: /etc/x-ids
  
  volumes:
  - name: models
    configMap:
      name: x-ids-models
  - name: config
    configMap:
      name: x-ids-config
```

### 4.2 Kafka Streaming Architecture

```
Kubernetes Cluster
    ├── X-IDS Pods (× N)
    │   ├── Model Inference
    │   ├── Alert Generation
    │   └── Kafka Producer
    │       ↓
    │   Kafka Broker (3 replicas)
    │   Topics:
    │   ├── raw-traffic (input)
    │   ├── alerts (high-severity)
    │   └── metrics (prometheus)
    │       ↓
    ├── Stream Processor (Spark)
    │   ├── Aggregation (5-min windows)
    │   ├── Correlation (detect campaigns)
    │   └── Enrichment (threat intel)
    │       ↓
    ├── SIEM Integration
    │   ├── Splunk
    │   ├── ELK Stack
    │   └── Datadog
    │       ↓
    └── SOC Dashboard
        ├── Real-time alerts
        ├── Explanation viewer
        └── Trend analysis
```

---

## 5. API Interfaces

### 5.1 Predictor API

```python
from xids.inference.predictor import Predictor

# Initialize
predictor = Predictor(model_path="/models/tcn.h5")

# Single prediction
prediction = predictor.predict(packet_features)  # Returns [0-1]

# Batch prediction
predictions = predictor.predict_batch(packet_batch)  # Returns array

# With explanation
result = predictor.predict_with_explanation(
    packet,
    explain_method="shap",  # or "lime"
    return_timing=True
)
# Returns: {
#     'prediction': 0.85,
#     'explanation': {...},
#     'latency_ms': 420
# }
```

### 5.2 REST API (FastAPI)

```python
from fastapi import FastAPI

app = FastAPI()

@app.post("/predict")
async def predict(packet: Packet) -> Prediction:
    """Single packet prediction"""
    return predictor.predict(packet)

@app.post("/predict-batch")
async def predict_batch(packets: List[Packet]) -> List[Prediction]:
    """Batch predictions"""
    return predictor.predict_batch(packets)

@app.post("/explain")
async def explain(
    packet: Packet,
    method: str = "shap"
) -> Explanation:
    """Get explanation for prediction"""
    return explainer.explain(packet, method)

@app.get("/health")
async def health() -> Dict[str, str]:
    """Health check"""
    return {"status": "healthy"}

@app.get("/metrics")
async def metrics() -> Dict[str, float]:
    """Prometheus metrics"""
    return get_metrics()
```

### 5.3 Configuration API

```yaml
# config.yaml
x_ids:
  models:
    primary: tcn          # tcn, autoencoder, rf
    secondary: autoencoder
    ensemble: true
  
  inference:
    batch_size: 32
    threshold: 0.7        # Alert if confidence > 70%
    max_latency_ms: 100
  
  explainability:
    enabled: true
    method: shap          # shap, lime, or both
    latency_budget_ms: 500
  
  output:
    kafka_enabled: true
    kafka_topic: "x-ids-alerts"
    siem_webhook: "https://siem.company.com/webhook"
```

---

## 6. Scaling Considerations

### 6.1 Horizontal Scaling

```
                    ┌─────────────────────┐
                    │  Load Balancer      │
                    │  (Nginx / Envoy)    │
                    └──────┬──────────────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
        ┌─────▼────┐  ┌────▼────┐  ┌──▼──────┐
        │ X-IDS #1 │  │ X-IDS #2│  │ X-IDS #N│
        │ (batch32)│  │(batch32)│  │(batch32)│
        │  8CPU    │  │ 8CPU    │  │ 8CPU    │
        │  16GB    │  │ 16GB    │  │ 16GB    │
        └────┬─────┘  └────┬────┘  └──┬──────┘
             │             │          │
             └─────────────┬──────────┘
                           │
                    ┌──────▼──────┐
                    │  Kafka      │
                    │  Cluster    │
                    │ (3 brokers) │
                    └─────────────┘

Throughput: 32 samples/batch × 3 batches/sec × 10 pods = 960 samples/sec
```

### 6.2 Vertical Scaling (GPU Acceleration)

```
GPU Node:
  ├── NVIDIA A100 (40GB)
  ├── TensorRT optimization
  ├── Batch size: 256 (vs 32 on CPU)
  └── Inference: 25ms (vs 100ms on CPU)

4x Speedup = 4× more alerts/sec with same latency
```

---

## 7. Monitoring & Observability

### 7.1 Key Metrics

```prometheus
# Model Performance
x_ids_predictions_total{model="tcn",class="attack"}
x_ids_precision{threshold="0.7"}
x_ids_recall{threshold="0.7"}
x_ids_f1_score{model="tcn"}

# Latency
x_ids_inference_duration_seconds_bucket{model="tcn"}
x_ids_explanation_duration_seconds_bucket{method="shap"}
x_ids_total_latency_seconds_bucket

# Throughput
x_ids_samples_processed_total
x_ids_alerts_generated_total{severity="high"}
x_ids_false_positives_total

# System Health
x_ids_model_drift_score
x_ids_data_quality_score
```

### 7.2 Alerting Rules

```yaml
groups:
- name: x-ids
  rules:
  - alert: ModelAccuracyDegraded
    expr: x_ids_f1_score < 0.85
    for: 1h
  
  - alert: InferenceLatencyHigh
    expr: x_ids_inference_duration_seconds > 0.15
    for: 5m
  
  - alert: AlertVolumeAnomalous
    expr: abs(rate(x_ids_alerts_total[5m]) - avg(rate(x_ids_alerts_total[5m] offset 7d))) > 10
    for: 10m
```

---

## 8. Disaster Recovery & High Availability

### 8.1 Model Versioning

```
models/
├── current/ → symlink to v2.5
├── v2.5/ (active)
│   ├── tcn.h5
│   ├── vae.h5
│   ├── rf.pkl
│   └── metadata.json
├── v2.4/ (fallback)
│   └── ...
└── v2.3/ (archive)
    └── ...
```

### 8.2 Failover Strategy

```
Primary X-IDS Instance (Pod 1)
    ├── Model Serving
    ├── Health Check (every 5s)
    └── Liveness Probe: OK

[Failure Detected]
    ↓

Kubernetes Auto-Recovery:
    ├── Kill failing pod
    ├── Start new replica
    └── Route traffic to secondary

Secondary X-IDS Instance (Pod 2)
    ├── Takes over (no interruption)
    └── Kafka offset management ensures no alert loss
```

### 8.3 Backup & Recovery

```bash
# Daily model backup to S3
00 02 * * * /scripts/backup-models.sh

# Weekly evaluation report
00 03 * * 0 /scripts/eval-report.sh

# Monthly model retraining
00 04 1 * * /scripts/retrain-models.sh
```

---

## 9. Security Considerations

### 9.1 Model Integrity

```
Model Verification:
  ├── SHA256 hash of .h5 file
  ├── Code signature verification
  ├── Runtime integrity checks (AIDE)
  └── Immutable model storage (K8s ConfigMap)
```

### 9.2 Data Privacy

```
Sensitive Data Handling:
  ├── PII Redaction (IP addresses, hostnames)
  ├── Encryption in transit (TLS 1.3)
  ├── Encryption at rest (AES-256)
  ├── Access control (RBAC)
  └── Audit logging (all model access)
```

### 9.3 Adversarial Robustness

```
Defenses:
  ├── Input validation & sanitization
  ├── Feature bounds checking
  ├── Adversarial training
  ├── Gradient masking
  └── Rate limiting on inference API
```

---

## 10. Documentation Structure

```
docs/
├── ARCHITECTURE.md (this file)
├── PROPOSAL.md (technical proposal)
├── DEPLOYMENT.md (step-by-step guide)
├── API_REFERENCE.md (Python API docs)
├── TROUBLESHOOTING.md (common issues)
└── PERFORMANCE_TUNING.md (optimization tips)
```

---

**For questions or contributions, see README.md in the project root.**
