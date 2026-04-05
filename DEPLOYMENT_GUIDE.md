# X-IDS Deployment Guide

## Status
✅ **Code pushed to GitHub (Deployment branch)**  
✅ **Dependency conflicts resolved**  
✅ **PR ready to merge**  
✅ **All 114 tests passing locally**

---

## Option 1: Deploy on GitHub Codespaces (Free & Recommended)

### Step 1: Open in Codespaces
1. Go to: https://github.com/primexshade/Zero-Day-Attack
2. Click "Code" → "Codespaces" → "Create codespace on Deployment"
3. Wait for Codespaces to initialize

### Step 2: Deploy with Docker Compose
```bash
# Navigate to project
cd xids-framework

# Build and start all services
docker-compose up --build

# Services will be available at:
# - API: localhost:8000
# - Dashboard: localhost:8080
# - Kafka: localhost:9092
# - Elasticsearch: localhost:9200
```

### Step 3: Verify Deployment
```bash
# In another Codespaces terminal
curl http://localhost:8000/health  # Should return 200 OK

# Run tests
pytest tests/ -v

# Run load tests (optional)
pytest tests/performance/benchmark.py -v
```

---

## Option 2: Deploy Locally (Docker Required)

```bash
# Clone the repository
git clone https://github.com/primexshade/Zero-Day-Attack.git
cd Zero-Day-Attack/xids-framework

# Build and start
docker-compose up --build

# Access services
# API: http://localhost:8000
# Dashboard: http://localhost:8080
```

---

## Option 3: Deploy on Free Cloud VM (AWS/GCP/Azure)

### Prerequisites
- Free-tier VM (AWS EC2, Google Cloud, Azure)
- SSH access to VM
- Docker and Docker Compose installed

### Steps
```bash
# SSH into VM
ssh user@vm-ip

# Clone repo
git clone https://github.com/primexshade/Zero-Day-Attack.git
cd Zero-Day-Attack/xids-framework

# Start services
docker-compose up -d --build

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

---

## Architecture Overview

```
X-IDS Framework
├── Core (Models, Pipeline, Evaluation)
├── API (FastAPI + Uvicorn)
├── Streaming (Kafka Producer/Consumer)
├── Integrations (SIEM: Elasticsearch, Splunk)
├── Security (Auth, TLS)
├── Dashboard (Metrics, Alerts, WebSocket)
└── Tests (Unit, Integration, Performance)
```

---

## Key Services

| Service | Port | Purpose |
|---------|------|---------|
| API | 8000 | Model predictions & management |
| Dashboard | 8080 | Real-time metrics & alerts |
| Kafka | 9092 | Stream processing |
| Elasticsearch | 9200 | SIEM integration |

---

## Testing

```bash
# Run all tests
pytest tests/ -v --cov=src

# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Performance/Load tests
pytest tests/performance/ -v
```

---

## Environment Configuration

Edit `configs/default.yaml` or `configs/production.yaml`:

```yaml
api:
  host: 0.0.0.0
  port: 8000
  debug: false

security:
  jwt_secret: your-secret-key
  tls_enabled: true

streaming:
  kafka_brokers:
    - localhost:9092

integrations:
  siem:
    elasticsearch_host: localhost:9200
    splunk_host: splunk.example.com
```

---

## Troubleshooting

### Dependencies won't install
- Ensure `requirements.txt` has compatible versions (✅ Fixed)
- Run: `pip install --upgrade pip`

### Ports already in use
- Change ports in `docker-compose.yml`
- Or kill existing processes: `lsof -i :8000`

### Docker not running
- Start Docker daemon: `docker daemon`
- Or use Docker Desktop (Mac/Windows)

---

## Next Steps

1. **Merge PR**: Once CI/CD checks all pass, merge Deployment → main
2. **Create Release**: Tag the release (v1.0.0)
3. **Monitor**: Set up Grafana dashboards and alerting
4. **Scale**: Use Kubernetes for production scaling

---

## Support

- **Docs**: See `/xids-framework/docs/`
- **API Docs**: `http://localhost:8000/docs` (Swagger UI)
- **Issues**: https://github.com/primexshade/Zero-Day-Attack/issues

---

**Deployment Ready!** 🚀
