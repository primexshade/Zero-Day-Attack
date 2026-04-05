# X-IDS Production Deployment & Testing Guide

## Table of Contents
1. [Security Hardening](#security-hardening)
2. [HTTPS/TLS Setup](#httpstls-setup)
3. [Load Testing](#load-testing)
4. [SIEM Integration](#siem-integration)
5. [Deployment Strategies](#deployment-strategies)
6. [Monitoring & Alerts](#monitoring--alerts)

---

## Security Hardening

### Authentication (JWT)
X-IDS uses JWT tokens for API authentication with role-based access control.

#### Setup
```bash
# Generate secret key (use strong random string in production)
export JWT_SECRET=$(openssl rand -hex 32)

# Generate token for user
curl -X POST http://localhost:8000/auth/login \
  -d '{"username":"analyst","password":"secure_password"}'
```

#### API Usage
```bash
# Get token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -d '{"username":"analyst","password":"password"}' \
  | jq -r '.access_token')

# Use token in requests
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/predict \
  -d '{"features":[...]}'
```

#### Roles
- **admin**: Full access to all endpoints and configurations
- **analyst**: Can view alerts, predictions, and explanations
- **viewer**: Read-only access to dashboards and reports

### Rate Limiting
Default: 100 requests/second per client

```python
from inference.security import RateLimiter

limiter = RateLimiter(requests_per_second=100)
if limiter.is_allowed('client_ip'):
    # Process request
    pass
else:
    # Return 429 Too Many Requests
    pass
```

### Input Validation
Automatic input validation and sanitization

```python
from inference.security import InputValidator

# Validate IPs, domains, emails, UUIDs
InputValidator.validate_ip('192.168.1.1')
InputValidator.validate_domain('example.com')
InputValidator.validate_email('user@example.com')

# Sanitize user input
clean_input = InputValidator.sanitize_string(user_input)

# Validate feature arrays
InputValidator.validate_json_features(features, max_features=1000)
```

---

## HTTPS/TLS Setup

### Development Setup (Self-Signed)
```bash
cd xids-framework

# Generate self-signed certificate
python inference/tls.py

# Verify certificate
openssl x509 -in certs/server.crt -noout -text
```

### Production Setup (Let's Encrypt)
```bash
# Install certbot
pip install certbot

# Get certificate
certbot certonly --standalone -d your-domain.com

# Copy certificates to app
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem certs/server.crt
cp /etc/letsencrypt/live/your-domain.com/privkey.pem certs/server.key
```

### Running with HTTPS

#### Flask
```python
from inference.tls import TLSManager
from flask import Flask

app = Flask(__name__)
ssl_context = TLSManager.get_ssl_context()
app.run(ssl_context=ssl_context, host='0.0.0.0', port=443)
```

#### Gunicorn (Recommended)
```bash
gunicorn xids-framework.api:app \
  --certfile=certs/server.crt \
  --keyfile=certs/server.key \
  --ssl-version=TLSv1_2 \
  --bind 0.0.0.0:443 \
  --workers 4
```

#### Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY xids-framework ./xids-framework
COPY certs/ ./certs/
EXPOSE 443
CMD ["gunicorn", "xids-framework.api:app", \
     "--certfile=/app/certs/server.crt", \
     "--keyfile=/app/certs/server.key", \
     "--ssl-version=TLSv1_2", \
     "--bind=0.0.0.0:443", \
     "--workers=4"]
```

### Certificate Monitoring
```bash
# Check expiry date
python -c "from inference.tls import TLSManager; TLSManager.check_certificate_expiry()"

# Auto-renew with Let's Encrypt
0 0 1 * * certbot renew --quiet
```

---

## Load Testing

### Setup
```bash
# Install locust
pip install locust

# Run load test
locust -f xids-framework/tests/locustfile.py \
  --host=http://localhost:8000 \
  -u 100 \
  -r 10 \
  --run-time=5m
```

### Test Scenarios

#### 1. Baseline Load (10 users)
```bash
locust -f xids-framework/tests/locustfile.py \
  --host=http://localhost:8000 \
  -u 10 -r 1 --run-time=2m
```

**Expected Results:**
- Response time: <100ms (50th percentile)
- Throughput: >100 req/sec
- Error rate: <1%

#### 2. Peak Load (100 users)
```bash
locust -f xids-framework/tests/locustfile.py \
  --host=http://localhost:8000 \
  -u 100 -r 20 --run-time=5m
```

**Expected Results:**
- Response time: <200ms (95th percentile)
- Throughput: >500 req/sec
- Error rate: <2%

#### 3. Stress Test (1000 users)
```bash
locust -f xids-framework/tests/locustfile.py \
  --host=http://localhost:8000 \
  -u 1000 -r 50 --run-time=10m
```

**Expected Results:**
- Response time: <500ms (99th percentile)
- Throughput: >1000 req/sec
- Error rate: <5%

### Performance Metrics
- **Latency Target**: <100ms for predictions, <500ms with explanations
- **Throughput Target**: >1000 predictions/sec per instance
- **Memory Target**: <2GB per process
- **CPU Target**: <80% utilization under peak load

---

## SIEM Integration

### Elasticsearch Setup

#### Installation
```bash
# Using Docker
docker run -d \
  -e "ES_JAVA_OPTS=-Xms512m -Xmx512m" \
  -e "discovery.type=single-node" \
  -p 9200:9200 \
  docker.elastic.co/elasticsearch/elasticsearch:8.0.0

# Verify
curl http://localhost:9200
```

#### Configuration
```bash
# Set API key environment variable
export ES_API_KEY="your-api-key"
export ES_CA_CERTS="/path/to/ca.crt"
```

#### Send Alerts
```python
from xids-framework.tests.test_siem import ElasticsearchSIEMClient

client = ElasticsearchSIEMClient()
alert = {
    'timestamp': '2024-01-15T10:30:00Z',
    'alert_id': 'alert-123',
    'source_ip': '192.168.1.100',
    'attack_type': 'SQL Injection',
    'confidence': 0.96
}
client.index_alert(alert)
```

### Splunk Setup

#### Installation
```bash
# Using Docker
docker run -d \
  -e "SPLUNK_START_ARGS=--accept-license" \
  -e "SPLUNK_PASSWORD=ChangeMeNow" \
  -p 8000:8000 \
  -p 8088:8088 \
  splunk/splunk:latest

# Access UI: http://localhost:8000
```

#### Configuration
```bash
# Generate HEC token in Splunk UI
# Settings > Data Inputs > HTTP Event Collector > New Token

export SPLUNK_HEC_TOKEN="your-token"
export SPLUNK_HOST="localhost"
export SPLUNK_PORT="8088"
```

#### Send Alerts
```python
from xids-framework.tests.test_siem import SplunkSIEMClient

client = SplunkSIEMClient()
alert = {
    'timestamp': '2024-01-15T10:30:00Z',
    'alert_id': 'alert-123',
    'source_ip': '192.168.1.100',
    'attack_type': 'SQL Injection'
}
client.send_alert(alert)
```

### Test SIEM Integration
```bash
# Run SIEM tests
pytest xids-framework/tests/test_siem.py -v

# Run with real instances
ELASTICSEARCH_HOST=localhost:9200 \
  SPLUNK_HOST=localhost \
  pytest xids-framework/tests/test_siem.py::TestElasticsearchSIEM -v
```

---

## Deployment Strategies

### Docker Compose (Development)
```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "443:443"
    environment:
      - JWT_SECRET=your-secret-key
      - KAFKA_BOOTSTRAP_SERVERS=kafka:9092
      - ES_HOST=elasticsearch:9200
    volumes:
      - ./certs:/app/certs
    depends_on:
      - kafka
      - elasticsearch
  
  kafka:
    image: confluentinc/cp-kafka:7.0.0
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
  
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
    ports:
      - "9200:9200"
    environment:
      - discovery.type=single-node
```

### Kubernetes (Production)
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: xids-api
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: api
        image: xids:latest
        ports:
        - containerPort: 443
        env:
        - name: JWT_SECRET
          valueFrom:
            secretKeyRef:
              name: xids-secrets
              key: jwt-secret
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 2000m
            memory: 4Gi
        livenessProbe:
          httpGet:
            path: /health
            port: 443
            scheme: HTTPS
          initialDelaySeconds: 30
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: xids-api
spec:
  type: LoadBalancer
  ports:
  - port: 443
    targetPort: 443
  selector:
    app: xids-api
```

---

## Monitoring & Alerts

### Health Checks
```bash
# API health
curl https://localhost:443/health

# Database connectivity
curl https://localhost:443/health/db

# Kafka connectivity
curl https://localhost:443/health/kafka
```

### Prometheus Metrics
```python
from prometheus_client import Counter, Histogram

prediction_counter = Counter('xids_predictions_total', 'Total predictions')
prediction_latency = Histogram('xids_prediction_latency_seconds', 'Prediction latency')
alert_counter = Counter('xids_alerts_total', 'Total alerts')
```

### Alerting Rules
```yaml
groups:
- name: xids
  rules:
  - alert: HighErrorRate
    expr: rate(xids_errors_total[5m]) > 0.05
    for: 5m
    annotations:
      summary: "High error rate detected"
  
  - alert: HighLatency
    expr: xids_prediction_latency_seconds > 0.5
    for: 10m
    annotations:
      summary: "Prediction latency too high"
  
  - alert: CertificateExpiring
    expr: days_until_cert_expiry < 30
    annotations:
      summary: "SSL certificate expiring soon"
```

### Log Aggregation (ELK Stack)
```bash
# Elasticsearch
docker run -d --name elasticsearch \
  -e "discovery.type=single-node" \
  -p 9200:9200 docker.elastic.co/elasticsearch/elasticsearch:8.0.0

# Logstash
docker run -d --name logstash \
  -v $(pwd)/logstash.conf:/usr/share/logstash/pipeline/logstash.conf \
  -p 5000:5000 docker.elastic.co/logstash/logstash:8.0.0

# Kibana
docker run -d --name kibana \
  -p 5601:5601 \
  docker.elastic.co/kibana/kibana:8.0.0
```

---

## Testing Checklist

- [ ] Unit tests passing (19/19)
- [ ] E2E tests passing (6/6)
- [ ] SIEM tests passing (10/10)
- [ ] Load tests passing (baseline, peak, stress)
- [ ] Security scan passing (no vulnerabilities)
- [ ] Certificate valid and not expiring soon
- [ ] Rate limiting working correctly
- [ ] JWT authentication functional
- [ ] HTTPS/TLS enforced
- [ ] Elasticsearch integration working
- [ ] Splunk HEC integration working
- [ ] Kafka streaming functional
- [ ] Health checks passing
- [ ] Monitoring metrics collecting
- [ ] Logs centralized and searchable

---

## Troubleshooting

### SSL Certificate Errors
```bash
# Regenerate self-signed certificate
rm -rf certs/
python inference/tls.py
```

### Rate Limiting Too Strict
```bash
# Adjust rate limit
export RATE_LIMIT_RPS=1000  # requests per second
```

### SIEM Connection Failures
```bash
# Test Elasticsearch connection
curl -H "Authorization: ApiKey $ES_API_KEY" http://localhost:9200

# Test Splunk HEC
curl -H "Authorization: Splunk $SPLUNK_HEC_TOKEN" \
  https://localhost:8088/services/collector
```

### Load Test Failures
```bash
# Check resource usage
docker stats

# Increase workers
export GUNICORN_WORKERS=16

# Enable debug logging
export LOG_LEVEL=DEBUG
```

---

## Additional Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [TLS 1.2+ Configuration](https://wiki.mozilla.org/Security/Server_Side_TLS)
- [Elasticsearch Security](https://www.elastic.co/guide/en/elasticsearch/reference/current/security-api.html)
- [Splunk Best Practices](https://docs.splunk.com/Documentation/Splunk/latest/)

