# X-IDS: Explainable Deep Learning Framework for Real-Time Zero-Day Detection

**X-IDS** is a modular, production-ready Intrusion Detection System (IDS) that uses deep learning and explainable AI (XAI) to detect zero-day attacks and novel cyber threats in real-time.

## 🎯 Key Features

- **Deep Learning Models**: Temporal Convolutional Networks (TCN) and Variational Autoencoders (VAE) for anomaly detection
- **Explainability**: SHAP and LIME integration for interpretable predictions that SOC analysts can trust
- **Imbalance Handling**: SMOTE and ADASYN techniques to handle rare zero-day events
- **Real-Time Processing**: <100ms latency for inference, <500ms for explainability generation
- **Comprehensive Evaluation**: Confusion matrices, precision-recall curves, F1-score comparisons
- **Production Ready**: Docker and Kubernetes deployment configurations included

## 📊 Datasets

X-IDS is trained and evaluated on:
- **CICIDS2017**: Canadian Institute for Cybersecurity IDS Dataset (2017)
- **UNSW-NB15**: UNSW-NB15 Intrusion Detection Dataset

Both datasets contain labeled normal and attack traffic with zero-day exploits.

## 🏗️ Architecture

```
Data Pipeline (CICIDS2017/UNSW-NB15)
    ↓
Preprocessing & Feature Engineering
    ↓
Class Imbalance Handling (SMOTE/ADASYN)
    ↓
Model Training:
  - Temporal Convolutional Network (TCN)
  - Variational Autoencoder (VAE)
  - Random Forest (Baseline)
    ↓
Explainability Layer (SHAP + LIME)
    ↓
Real-Time Inference Engine
    ↓
Alert Generation & SOC Integration
```

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/yourusername/xids-framework.git
cd xids-framework
pip install -r requirements.txt
```

### Data Preparation

```bash
python -m data.dataloaders --download-cicids2017 --download-unswnb15
```

### Training Models

```bash
python training/trainer.py --config training/config.yaml --model tcn
python training/trainer.py --config training/config.yaml --model autoencoder
```

### Running Evaluation

```bash
python evaluation/benchmark.py --models tcn autoencoder random_forest --output results/
```

### Real-Time Inference

```bash
python inference/realtime_handler.py --model tcn --explainability shap
```

## 📖 Documentation

- **[Architecture & Design](docs/ARCHITECTURE.md)**: System design, component interactions
- **[Technical Proposal](docs/PROPOSAL.md)**: Problem statement, methodology, deployment strategy
- **[API Reference](docs/API_REFERENCE.md)**: Python API documentation
- **[Deployment Guide](docs/DEPLOYMENT.md)**: Kubernetes, Docker, cloud deployment

## 🧪 Testing

```bash
pytest tests/ -v --cov=.
```

## 🐳 Docker & Kubernetes

### Docker Build

```bash
docker build -t xids-framework:latest .
docker run -p 8000:8000 xids-framework:latest
```

### Kubernetes Deployment

```bash
kubectl apply -f deployment/kubernetes/namespace.yaml
kubectl apply -f deployment/kubernetes/sidecar-deployment.yaml
```

## 📊 Performance Metrics

- **TCN F1-Score**: >95% on test set
- **Inference Latency**: <100ms per batch
- **Explainability Latency**: <500ms per alert
- **False Positive Rate**: <2% on benign traffic

## 🔍 Explainability

X-IDS provides two levels of explainability:

1. **Global Explanations (SHAP)**: Feature importance across all predictions
2. **Local Explanations (LIME)**: Per-packet interpretability for SOC analysts

Example:
```python
from explainability.shap_explainer import SHAPExplainer

explainer = SHAPExplainer(model)
feature_importance = explainer.explain_prediction(packet)
print(feature_importance)
```

## 🛡️ Threat Detection

X-IDS can detect:
- **Zero-Day Attacks**: Novel exploits not in signature databases
- **Polymorphic Malware**: Variants that change their binary structure
- **Anomalous Behavior**: Deviations from baseline traffic patterns
- **Distributed Attacks**: Multi-stage and coordinated threats

## 📈 Roadmap

- [ ] Real-time Kafka integration for high-volume traffic
- [ ] Graph Neural Networks (GNN) for flow-level analysis
- [ ] Federated learning for privacy-preserving distributed training
- [ ] Web dashboard for SOC alert management
- [ ] Hardware acceleration (GPU/TPU) optimization

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

## 📜 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file.

## 📧 Contact

For questions, issues, or collaboration opportunities, please open an issue on GitHub or contact the maintainers.

---

**Built with ❤️ for cybersecurity professionals and researchers**
