# X-IDS Project Architecture

## Directory Structure

```
xids-framework/
├── src/xids/
│   ├── core/              # Core ML functionality
│   │   ├── models/        # Model implementations
│   │   ├── pipeline/      # Data processing
│   │   ├── training/      # Training logic
│   │   ├── evaluation/    # Metrics and benchmarking
│   │   └── explainability/# SHAP and LIME
│   │
│   ├── api/               # REST API layer
│   │   ├── routes/        # API endpoints
│   │   ├── middleware/    # Request/response handling
│   │   ├── schemas/       # Pydantic models
│   │   └── app.py         # FastAPI app factory
│   │
│   ├── streaming/         # Real-time processing
│   │   ├── kafka/         # Kafka integration
│   │   └── processors/    # Stream processors
│   │
│   ├── integrations/      # External services
│   │   ├── siem/          # SIEM connectors
│   │   └── alerting/      # Alert channels
│   │
│   ├── security/          # Security utilities
│   │   ├── auth.py        # JWT authentication
│   │   ├── tls.py         # TLS/SSL
│   │   └── validation.py  # Input validation
│   │
│   └── utils/             # Shared utilities
│       ├── config.py      # Configuration loading
│       ├── logging.py     # Logging setup
│       └── metrics.py     # Prometheus metrics
│
├── tests/
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── performance/       # Load and benchmark tests
│
├── scripts/               # Entry point scripts
│   ├── train.py
│   ├── evaluate.py
│   └── serve.py
│
├── configs/               # Configuration files
│   ├── default.yaml
│   ├── production.yaml
│   └── development.yaml
│
├── docs/                  # Documentation
│   ├── api/               # API documentation
│   ├── architecture/      # Architecture docs
│   └── research/          # Research papers
│
├── dashboard/             # Frontend dashboard
├── data/                  # Datasets and models
├── docker/                # Docker files
├── k8s/                   # Kubernetes manifests
│
├── pyproject.toml         # Python project config
├── requirements.txt       # Dependencies
├── Makefile              # Build automation
└── README.md             # Project overview
```

## Key Components

### 1. Core Module (`src/xids/core/`)
Core ML functionality with clear separation:
- **models/**: TCN, VAE, RF, Ensemble implementations
- **pipeline/**: Data preprocessing, imbalance handling, loading
- **training/**: Training logic with callbacks
- **evaluation/**: Metrics and benchmarking
- **explainability/**: SHAP and LIME explainers

### 2. API Module (`src/xids/api/`)
Modular REST API with clean structure:
- **routes/**: Separate route files for different endpoints
  - `health.py`: Health checks and system metrics
  - `predictions.py`: Inference endpoints
  - `alerts.py`: Alert management
  - `metrics.py`: Model metrics
- **middleware/**: Security headers, rate limiting, logging
- **schemas/**: Request/response validation
- **app.py**: FastAPI app factory

### 3. Streaming Module (`src/xids/streaming/`)
Real-time data processing:
- **kafka/**: Kafka producer/consumer
- **processors/**: Threat detection, alert generation

### 4. Integrations (`src/xids/integrations/`)
External service connections:
- **siem/**: Elasticsearch and Splunk connectors
- **alerting/**: Slack, PagerDuty, email

### 5. Security Module (`src/xids/security/`)
Security utilities:
- JWT authentication and token management
- TLS/SSL configuration
- Input validation and sanitization

## Development Workflow

### 1. Setup
```bash
make install-dev
```

### 2. Development
```bash
# Run API with auto-reload
make serve

# Run tests
make test

# Format code
make format
```

### 3. Testing
```bash
# Unit tests
make test-unit

# Integration tests
make test-integration

# Performance tests
make test-performance

# With coverage
make test-cov
```

### 4. Deployment
```bash
# Build Docker image
make docker-build

# Run with Docker
make docker-run

# Run production API
make serve-prod
```

## Configuration

Configuration files in `configs/`:
- `default.yaml`: Default settings
- `production.yaml`: Production overrides
- `development.yaml`: Development settings

Environment variables override YAML settings.

## Module Dependencies

```
api/
  ├── routes/ → schemas/
  ├── middleware/ → security/
  └── app.py → routes/, middleware/

core/
  ├── training/ → models/, pipeline/
  ├── evaluation/ → models/
  └── explainability/ → models/

streaming/
  ├── kafka/ → core/
  └── processors/ → core/

integrations/
  └── siem/ → api/
```

## Adding New Features

### Adding a new API route:
1. Create route file in `src/xids/api/routes/`
2. Define schemas in `src/xids/api/schemas/`
3. Add middleware if needed in `src/xids/api/middleware/`
4. Include router in `app.py`

### Adding a new model:
1. Create implementation in `src/xids/core/models/`
2. Inherit from `BaseModel`
3. Implement required methods
4. Add tests in `tests/unit/core/`

### Adding integration:
1. Create connector in `src/xids/integrations/`
2. Implement base interface
3. Add configuration in `configs/`
4. Add tests in `tests/integration/`

## Performance Considerations

- Batch predictions available at `/api/v1/predictions/batch-predict`
- Rate limiting configured in security middleware
- Async I/O throughout FastAPI
- Connection pooling for databases and caches
- Model versioning and caching supported

## Monitoring and Observability

- Prometheus metrics at `/metrics`
- Request logging middleware
- Error tracking integration ready
- Health checks at `/health` and `/ready`

## Testing Strategy

- Unit tests for models and utilities
- Integration tests for full pipelines
- Performance benchmarks in Locust
- E2E tests for complete workflows

## Future Enhancements

- [ ] GraphQL API support
- [ ] WebSocket streaming predictions
- [ ] Model versioning with MLflow
- [ ] Distributed training with Ray
- [ ] GNN support for flow-level analysis
- [ ] Federated learning integration
- [ ] GPU acceleration with TensorRT
