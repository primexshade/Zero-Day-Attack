# X-IDS Complete Deployment Plan

## 📋 Pre-Deployment Checklist

✅ Code pushed to main branch  
✅ .env files configured  
✅ docker-compose.yml validated  
✅ All tests passing  
✅ CI/CD pipeline fixed  
✅ Documentation complete  

---

## 🚀 DEPLOYMENT PHASE 1: GitHub Codespaces (Recommended - Free)

### Step 1: Launch GitHub Codespaces
1. Go to: https://github.com/primexshade/Zero-Day-Attack
2. Click **Code** → **Codespaces** → **Create codespace on main**
3. Wait 2-3 minutes for initialization

### Step 2: Verify Environment
```bash
# Check Docker
docker --version

# Check Docker Compose
docker-compose --version

# Check Python
python --version
```

### Step 3: Configure Environment
```bash
# Copy .env to xids-framework
cd xids-framework
cp ../.env .env

# Update critical secrets (if needed)
# nano .env
# Change: JWT_SECRET, ELASTICSEARCH_PASSWORD
```

### Step 4: Start Services
```bash
# Build and start all services
docker-compose up --build

# Wait for startup (~2-3 minutes)
# Look for: "X-IDS API ready at http://0.0.0.0:8000"
```

### Step 5: Verify Deployment
```bash
# In a NEW Codespaces terminal:

# Test API health
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","timestamp":"..."}

# Access Swagger UI
# Open browser: http://localhost:8000/docs

# Check running containers
docker-compose ps
```

### Step 6: Run Tests
```bash
# In same terminal:
pytest tests/unit/ -v

# Run all tests
pytest tests/ -v
```

---

## 🖥️ DEPLOYMENT PHASE 2: Local Machine (Docker Required)

### Prerequisites
- Docker Desktop installed (Mac/Windows) or Docker + Docker Compose (Linux)
- 8GB RAM minimum
- 20GB disk space

### Step 1: Clone Repository
```bash
git clone https://github.com/primexshade/Zero-Day-Attack.git
cd Zero-Day-Attack
```

### Step 2: Setup Environment
```bash
# Copy .env file
cp .env xids-framework/.env

# Edit .env if needed
cd xids-framework
# nano .env  # Change secrets as needed
```

### Step 3: Deploy
```bash
# Build images and start services
docker-compose up --build -d

# Monitor startup
docker-compose logs -f
```

### Step 4: Verify Services
```bash
# Check containers
docker-compose ps

# Test API
curl http://localhost:8000/health

# List available endpoints
curl http://localhost:8000/docs
```

### Step 5: Access Services
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (Swagger)
- **Grafana**: http://localhost:3000 (admin/admin)
- **Kibana**: http://localhost:5601
- **Prometheus**: http://localhost:9090

---

## ☁️ DEPLOYMENT PHASE 3: Cloud VM (Free Tier)

### Option A: AWS EC2 (Free Tier)
```bash
# 1. Create t2.micro instance (free)
# 2. Security Group: Allow ports 8000, 3000, 5601, 9090

# 3. SSH into instance
ssh -i your-key.pem ubuntu@your-instance-ip

# 4. Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# 5. Clone and deploy
git clone https://github.com/primexshade/Zero-Day-Attack.git
cd Zero-Day-Attack/xids-framework
docker-compose up -d --build

# 6. Access from local machine
ssh -L 8000:localhost:8000 ubuntu@your-instance-ip
# Then visit: http://localhost:8000/docs
```

### Option B: Google Cloud Run (Free Tier)
```bash
# 1. Create Cloud Run service
# 2. Deploy container from xids-framework/Dockerfile
# 3. Configure environment variables
# 4. Expose port 8000
```

### Option C: Azure App Service (Free Tier)
```bash
# 1. Create Linux App Service
# 2. Configure container settings
# 3. Set environment variables
# 4. Deploy from GitHub
```

---

## 📊 Service Architecture

```
X-IDS Deployment
├── API Layer (Port 8000)
│   ├── FastAPI Server
│   ├── JWT Authentication
│   └── TLS/HTTPS
├── Streaming Layer (Port 9092)
│   ├── Kafka Broker
│   ├── Zookeeper (2181)
│   └── Message Topics
├── Caching Layer (Port 6379)
│   └── Redis Server
├── Search Layer (Port 9200)
│   ├── Elasticsearch
│   └── Kibana (5601)
└── Monitoring Layer
    ├── Prometheus (9090)
    └── Grafana (3000)
```

---

## 🧪 Post-Deployment Verification

### 1. API Health Check
```bash
curl http://localhost:8000/health
```
**Expected**: `{"status":"healthy"}`

### 2. Available Models
```bash
curl http://localhost:8000/api/v1/models
```

### 3. Make Prediction
```bash
curl -X POST http://localhost:8000/api/v1/predict \
  -H "Content-Type: application/json" \
  -d '{"features":[0.1,0.2,0.3,0.4,0.5],"model":"ensemble"}'
```

### 4. Check Logs
```bash
docker-compose logs api
docker-compose logs elasticsearch
docker-compose logs kafka
```

### 5. Run Test Suite
```bash
pytest tests/ -v
```

### 6. Performance Test
```bash
pytest tests/performance/ -v
```

---

## 🔐 Security Configuration

### Pre-Production Changes Required:

1. **JWT Secret** (in .env)
   ```
   JWT_SECRET=<strong-random-secret>
   ```

2. **Elasticsearch Password**
   ```
   ELASTICSEARCH_PASSWORD=<strong-password>
   ```

3. **Enable TLS**
   ```
   TLS_ENABLED=true
   TLS_CERT_PATH=/etc/xids/certs/cert.pem
   TLS_KEY_PATH=/etc/xids/certs/key.pem
   ```

4. **Database Password** (if using PostgreSQL)
   ```
   DATABASE_URL=postgresql://user:strong-password@host:5432/db
   ```

---

## 📈 Monitoring Setup

### Grafana Dashboards
1. Access: http://localhost:3000
2. Login: admin / admin
3. Add data source: Prometheus (http://prometheus:9090)
4. Import dashboards for:
   - API metrics
   - Kafka throughput
   - System resources

### Elasticsearch/Kibana
1. Access: http://localhost:5601
2. Create index pattern: `xids-alerts*`
3. View alerts and anomalies
4. Create custom visualizations

### Prometheus Alerts
1. Access: http://localhost:9090
2. View collected metrics
3. Configure alert rules
4. Setup notification channels

---

## ⚠️ Troubleshooting

### Issue: Services won't start
```bash
# Check logs
docker-compose logs

# Clean and restart
docker-compose down -v
docker-compose up --build
```

### Issue: Port already in use
```bash
# Find process
lsof -i :8000

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yml
```

### Issue: Out of memory
```bash
# Reduce services (remove non-essential)
# Edit docker-compose.yml

# Or increase Docker memory limit
```

### Issue: Network connectivity
```bash
# Check network
docker network ls
docker network inspect xids-network

# Rebuild network
docker-compose down
docker-compose up --build
```

---

## 📞 Support & Maintenance

### Logs Location
```bash
docker-compose logs -f <service-name>
```

### Scale Services
```bash
docker-compose up -d --scale api=3
```

### Update Code
```bash
git pull origin main
docker-compose up --build -d
```

### Backup Data
```bash
docker-compose exec elasticsearch \
  curl -X PUT http://localhost:9200/_snapshot/backup
```

### Monitor Resource Usage
```bash
docker stats
```

---

## 📋 Environment Variables Reference

| Variable | Default | Purpose |
|----------|---------|---------|
| API_PORT | 8000 | API server port |
| KAFKA_BROKER | kafka:9092 | Kafka connection |
| ELASTICSEARCH_HOST | elasticsearch | Search service |
| REDIS_HOST | redis | Caching service |
| JWT_SECRET | dev-secret | Authentication key |
| TLS_ENABLED | false | HTTPS support |
| ENVIRONMENT | development | Dev/production mode |

---

## ✅ Deployment Completion Checklist

- [ ] Environment configured (.env files)
- [ ] Docker/Docker Compose installed
- [ ] Services started successfully
- [ ] API health check passing
- [ ] All tests passing
- [ ] Grafana dashboard accessible
- [ ] Kibana logs visible
- [ ] Prometheus metrics collected
- [ ] Security settings configured
- [ ] Documentation reviewed

---

## 🎯 Next Steps (Post-Deployment)

1. **Configure Alerts**: Set up alert rules in Prometheus/Grafana
2. **Setup Integrations**: Connect to SIEM (Splunk/Elasticsearch)
3. **Load Testing**: Run performance tests with production data
4. **Monitor**: Setup 24/7 monitoring and logging
5. **Backup**: Configure data backup strategy
6. **Scale**: Add load balancer for multiple API instances
7. **CI/CD**: Setup automated deployments on code changes

---

## 📞 Quick Reference

```bash
# Start deployment
docker-compose up --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Run tests
pytest tests/ -v

# Check health
curl http://localhost:8000/health

# Access Swagger
# Open: http://localhost:8000/docs
```

---

**Deployment Status**: ✅ **READY TO DEPLOY**

**Repository**: https://github.com/primexshade/Zero-Day-Attack

Start with Phase 1 (GitHub Codespaces) for quickest deployment! 🚀
