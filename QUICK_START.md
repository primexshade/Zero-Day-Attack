# X-IDS Quick Start Deployment Guide

## ✅ Fixed Issues
- ✅ Removed obsolete `version` attribute from docker-compose.yml
- ✅ Fixed network references for all services
- ✅ Removed optional services (postgres, pgadmin) causing conflicts
- ✅ Cleaned and validated YAML syntax

---

## 🚀 Deployment in GitHub Codespaces (3 minutes)

### Step 1: Navigate to Project
```bash
cd xids-framework
```

### Step 2: Start All Services
```bash
docker-compose up --build
```

**Expected Output:**
```
✓ zookeeper is running
✓ kafka is running
✓ redis is running
✓ elasticsearch is running
✓ api is running (health: starting)
✓ kibana is running
✓ prometheus is running
✓ grafana is running
```

### Step 3: Access Services

Open in browser or use curl:

```bash
# API Health Check
curl http://localhost:8000/health
# Response: {"status": "healthy", "timestamp": "..."}

# API Documentation (Swagger)
# Visit: http://localhost:8000/docs

# Kibana (Logs)
# Visit: http://localhost:5601

# Prometheus (Metrics)
# Visit: http://localhost:9090

# Grafana (Dashboards)
# Visit: http://localhost:3000
# Login: admin / admin
```

---

## 🧪 Run Tests

```bash
# In a NEW terminal in the same directory
cd xids-framework

# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/unit/core/test_models.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

---

## 📊 Services Explained

| Service | Port | Purpose |
|---------|------|---------|
| **API** | 8000 | Main X-IDS inference API |
| **Zookeeper** | 2181 | Kafka coordination |
| **Kafka** | 9092 | Stream processing |
| **Redis** | 6379 | Caching/sessions |
| **Elasticsearch** | 9200 | SIEM log storage |
| **Kibana** | 5601 | Log visualization |
| **Prometheus** | 9090 | Metrics collection |
| **Grafana** | 3000 | Dashboard visualization |

---

## 🛑 Stop Services

```bash
# Stop all running containers
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

---

## 📝 Make API Calls

### Health Check
```bash
curl http://localhost:8000/health
```

### Get Available Models
```bash
curl http://localhost:8000/api/v1/models
```

### Make Prediction (Example)
```bash
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{
    "features": [0.1, 0.2, 0.3, 0.4, 0.5],
    "model": "ensemble"
  }'
```

Full API docs: http://localhost:8000/docs (Swagger UI)

---

## 🔧 Troubleshooting

### Issue: "port 8000 already in use"
```bash
# Kill existing process
lsof -i :8000 | awk 'NR!=1 {print $2}' | xargs kill -9

# Or change port in docker-compose.yml
# Change: ports: - "8000:8000"
# To:     ports: - "8001:8000"
```

### Issue: "Docker daemon not running"
```bash
# In GitHub Codespaces, Docker should be pre-installed
# If not, check: docker --version

# On local machine:
# macOS: open /Applications/Docker.app
# Linux: sudo systemctl start docker
```

### Issue: "Services not starting"
```bash
# Check logs
docker-compose logs -f api

# Rebuild from scratch
docker-compose down -v
docker-compose up --build
```

### Issue: "Out of memory"
```bash
# Reduce services (remove prometheus/grafana if needed)
# Edit docker-compose.yml and comment out services

# Or increase Docker memory in settings
```

---

## 📚 Project Structure

```
xids-framework/
├── src/xids/
│   ├── api/           # FastAPI application
│   ├── core/          # Models, training, evaluation
│   ├── streaming/     # Kafka integration
│   ├── integrations/  # SIEM (Elasticsearch)
│   ├── security/      # Auth, TLS
│   └── utils/         # Utilities
├── tests/             # Test suite
├── configs/           # Configuration files
├── Dockerfile         # Container image
├── docker-compose.yml # Multi-container setup
├── requirements.txt   # Python dependencies
└── pyproject.toml     # Package metadata
```

---

## ✨ Quick Command Reference

```bash
# Start deployment
docker-compose up --build

# View logs
docker-compose logs -f api

# Run tests
pytest tests/ -v

# Stop all
docker-compose down

# Check health
curl http://localhost:8000/health

# Access Swagger UI
# Open: http://localhost:8000/docs
```

---

## 🎯 Next Steps

1. ✅ Services are running
2. 📊 Access API at http://localhost:8000/docs
3. 🧪 Run tests with `pytest tests/ -v`
4. 📈 Check metrics in Grafana (http://localhost:3000)
5. 🔍 View logs in Kibana (http://localhost:5601)

---

## 📞 Support

- **API Docs**: http://localhost:8000/docs
- **Issues**: https://github.com/primexshade/Zero-Day-Attack/issues
- **Architecture**: See `xids-framework/docs/architecture/`

---

**Deployment Complete!** 🎉
