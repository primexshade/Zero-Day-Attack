# X-IDS Deployment Process

## ✅ Pre-Deployment Status
- **Codebase**: Production-ready, cleaned of unnecessary files
- **Tests**: All 114 tests passing
- **Dependencies**: Fixed (lime, matplotlib compatible versions)
- **CI/CD**: GitHub Actions configured
- **Docker**: Multi-container setup ready

---

## 📋 Repository Structure
```
X-IDS/
├── xids-framework/          # Main application
│   ├── src/xids/           # Production code
│   │   ├── api/            # FastAPI application
│   │   ├── core/           # Models, training, evaluation
│   │   ├── streaming/      # Kafka integration
│   │   ├── integrations/   # SIEM (Elasticsearch, Splunk)
│   │   ├── security/       # Auth, TLS
│   │   └── utils/          # Utilities
│   ├── tests/              # Test suite
│   ├── configs/            # Configuration files
│   ├── requirements.txt    # Dependencies
│   ├── pyproject.toml      # Package metadata
│   └── Makefile            # Build commands
├── docker-compose.yml      # Multi-container orchestration
├── .github/workflows/      # CI/CD pipelines
└── DEPLOYMENT_GUIDE.md    # This file
```

---

## 🚀 Deployment Methods

### **Option 1: GitHub Codespaces (Recommended - FREE)**

#### Step 1: Open in Codespaces
```bash
# Go to: https://github.com/primexshade/Zero-Day-Attack
# Click: Code → Codespaces → Create codespace on main
```

#### Step 2: Deploy with Docker Compose
```bash
cd xids-framework
docker-compose up --build -d
```

#### Step 3: Verify Services
```bash
# Check running containers
docker-compose ps

# Test API health
curl http://localhost:8000/health

# View logs
docker-compose logs -f api
```

#### Services Available
| Service | URL | Purpose |
|---------|-----|---------|
| API | http://localhost:8000 | Model predictions |
| API Docs | http://localhost:8000/docs | Swagger UI |
| Dashboard | http://localhost:8080 | Metrics & alerts |
| Kafka | localhost:9092 | Stream processing |
| Elasticsearch | localhost:9200 | SIEM integration |

---

### **Option 2: Local Machine (Docker Required)**

#### Step 1: Clone Repository
```bash
git clone https://github.com/primexshade/Zero-Day-Attack.git
cd Zero-Day-Attack
```

#### Step 2: Install Docker
- **Mac**: https://www.docker.com/products/docker-desktop
- **Linux**: `sudo apt install docker.io docker-compose`
- **Windows**: https://www.docker.com/products/docker-desktop

#### Step 3: Start Services
```bash
cd xids-framework
docker-compose up --build
```

#### Step 4: Access Services
- API: http://localhost:8000
- Dashboard: http://localhost:8080
- API Docs: http://localhost:8000/docs

---

### **Option 3: Free Cloud VM (AWS/GCP/Azure)**

#### Prerequisites
- Free-tier VM (t2.micro on AWS, e2-small on GCP, etc.)
- Ubuntu OS
- SSH access

#### Step 1: Connect to VM
```bash
ssh -i your-key.pem user@vm-ip
```

#### Step 2: Install Docker
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

#### Step 3: Deploy Application
```bash
git clone https://github.com/primexshade/Zero-Day-Attack.git
cd Zero-Day-Attack/xids-framework
docker-compose up -d --build
```

#### Step 4: Access Services
```bash
# From your local machine
ssh -L 8000:localhost:8000 user@vm-ip  # Port forward API
ssh -L 8080:localhost:8080 user@vm-ip  # Port forward Dashboard
```

---

## 🧪 Testing

### Run All Tests
```bash
cd xids-framework
pytest tests/ -v --cov=src
```

### Unit Tests Only
```bash
pytest tests/unit/ -v
```

### Integration Tests
```bash
pytest tests/integration/ -v
```

### Load/Performance Tests
```bash
pytest tests/performance/ -v
```

---

## ⚙️ Configuration

Edit `xids-framework/configs/default.yaml`:

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
    - kafka:9092

integrations:
  siem:
    elasticsearch_host: elasticsearch:9200
```

For production, edit `configs/production.yaml`.

---

## 📊 API Endpoints

### Health Check
```bash
curl http://localhost:8000/health
# Response: {"status":"healthy","timestamp":"..."}
```

### Make Prediction
```bash
curl -X POST http://localhost:8000/api/predictions \
  -H "Content-Type: application/json" \
  -d '{"features":[...], "model":"ensemble"}'
```

### Get Model Info
```bash
curl http://localhost:8000/api/models
```

Full API docs: http://localhost:8000/docs

---

## 🔧 Troubleshooting

### Port Already in Use
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yml
```

### Dependencies Won't Install
```bash
# Clear pip cache
pip cache purge

# Reinstall
pip install -r requirements.txt --no-cache-dir
```

### Docker Daemon Not Running
```bash
# macOS
open /Applications/Docker.app

# Linux
sudo systemctl start docker
```

### Containers Won't Start
```bash
# Check logs
docker-compose logs api

# Rebuild from scratch
docker-compose down -v
docker-compose up --build
```

---

## 📈 Monitoring

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api

# Last 100 lines
docker-compose logs --tail=100 api
```

### Resource Usage
```bash
docker stats
```

### Health Status
```bash
curl http://localhost:8000/health
curl http://localhost:8080/health
```

---

## 🛑 Shutdown

### Stop Services
```bash
docker-compose down
```

### Stop & Remove Volumes
```bash
docker-compose down -v
```

---

## 📝 Environment Variables

Create `.env` file in `xids-framework/`:

```
JWT_SECRET=your-secret-key
SIEM_HOST=elasticsearch
KAFKA_BROKERS=kafka:9092
DEBUG=false
```

---

## 🔐 Security

- TLS/HTTPS enabled by default
- JWT authentication on API
- Security headers configured
- Input validation on all endpoints

Set `TLS_CERT_PATH` and `TLS_KEY_PATH` for custom certificates.

---

## 📞 Support

- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Architecture**: See `/xids-framework/docs/architecture/`
- **Issues**: https://github.com/primexshade/Zero-Day-Attack/issues

---

## ✨ Quick Start (Copy-Paste)

```bash
# Clone
git clone https://github.com/primexshade/Zero-Day-Attack.git
cd Zero-Day-Attack

# Deploy
cd xids-framework
docker-compose up --build

# Test
curl http://localhost:8000/health

# Stop
docker-compose down
```

---

**Deployment Ready!** 🎉
