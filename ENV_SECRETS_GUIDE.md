# Complete .env Secrets Generation Guide

## 🔐 How to Generate Each Secret

### 1. **JWT_SECRET** (Authentication Key)
**Purpose**: Secure token signing for API authentication

**How to Generate**:
```bash
# Method 1: Using Python
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Method 2: Using OpenSSL
openssl rand -hex 32

# Method 3: Using Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

**Example Output**:
```
JWT_SECRET=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8c9d0
```

**Security**: Use 32+ characters, random, change quarterly

---

### 2. **ELASTICSEARCH_PASSWORD**
**Purpose**: Password for Elasticsearch service authentication

**How to Generate**:
```bash
# Method 1: Using OpenSSL
openssl rand -base64 24

# Method 2: Using Python
python3 -c "import secrets; print(secrets.token_urlsafe(24))"
```

**Example Output**:
```
ELASTICSEARCH_PASSWORD=aBcDeFgHiJkLmNoPqRsT1234
```

**Security**: 
- At least 12 characters
- Mix upper/lowercase + numbers
- Change every 6 months

---

### 3. **REDIS_PASSWORD** (Optional)
**Purpose**: Redis server authentication password

**How to Generate**:
```bash
openssl rand -base64 16
```

**Example Output**:
```
REDIS_PASSWORD=xYz9876AbCdEfGhI
```

**Security**: Leave empty if Redis is only on internal network

---

### 4. **DATABASE_PASSWORD** (For PostgreSQL)
**Purpose**: PostgreSQL database authentication

**How to Generate**:
```bash
# Strong database password
python3 -c "import secrets; print(secrets.token_urlsafe(20))"
```

**Example Output**:
```
DATABASE_PASSWORD=KmP9nXq2rWsT3uVwXyZ
```

**Security**: 
- 20+ characters
- Don't use special characters except: -_@
- Change on deployment

---

### 5. **SPLUNK_TOKEN** (For SIEM Integration)
**Purpose**: Splunk HTTP Event Collector authentication

**How to Get**:
1. Login to your Splunk instance: `https://your-splunk:8000`
2. Go to: **Settings → Data Inputs → HTTP Event Collector**
3. Click: **New Token**
4. Set name: "X-IDS"
5. Copy the token

**Example Output**:
```
SPLUNK_TOKEN=a1b2c3d4-e5f6-47a8-b9c0-d1e2f3a4b5c6
```

**Security**: 
- Regenerate every 90 days
- Don't share publicly
- Use dedicated token (not global)

---

### 6. **TLS_CERT_PATH & TLS_KEY_PATH**
**Purpose**: SSL/TLS certificate for HTTPS

**How to Generate**:
```bash
# Generate self-signed certificate (for development)
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Generate certificate signing request (CSR) for production
openssl req -newkey rsa:4096 -keyout key.pem -out cert.csr -nodes

# Sign with CA in production
```

**Create Directories**:
```bash
mkdir -p /etc/xids/certs
chmod 700 /etc/xids/certs
cp cert.pem /etc/xids/certs/
cp key.pem /etc/xids/certs/
chmod 600 /etc/xids/certs/key.pem
```

**Example Output**:
```
TLS_CERT_PATH=/etc/xids/certs/cert.pem
TLS_KEY_PATH=/etc/xids/certs/key.pem
```

**Security**: 
- Keep key.pem private (600 permissions)
- Use Let's Encrypt for production
- Renew certificates every 90 days

---

### 7. **PGADMIN_DEFAULT_PASSWORD** (For Database Management)
**Purpose**: pgAdmin web interface password

**How to Generate**:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(16))"
```

**Example Output**:
```
PGADMIN_DEFAULT_PASSWORD=PgA1dM2iN3tR4aT5
```

**Security**: Change after first login

---

### 8. **GRAFANA_ADMIN_PASSWORD**
**Purpose**: Grafana dashboard authentication

**How to Generate**:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(16))"
```

**Example Output**:
```
GRAFANA_ADMIN_PASSWORD=Gr4fN@p0Ss123456
```

**Security**: 
- Change default password immediately
- Use strong password
- Enable 2FA if available

---

### 9. **PROMETHEUS_TOKEN** (For Metrics)
**Purpose**: Prometheus API token (if authentication enabled)

**How to Generate**:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Example Output**:
```
PROMETHEUS_TOKEN=m9k8l7j6i5h4g3f2e1d0c9b8a7f6e5d4c3b2a1
```

**Security**: Optional, needed if authentication is enabled

---

### 10. **KAFKA_SASL_PASSWORD** (If SASL enabled)
**Purpose**: Kafka authentication password

**How to Generate**:
```bash
openssl rand -base64 24
```

**Example Output**:
```
KAFKA_SASL_PASSWORD=KfkS4sL9pSsW0rD1tEsT
```

**Security**: Only needed if SASL authentication is enabled

---

## ✅ Complete .env File Template

```bash
# ============================================
# API CONFIGURATION
# ============================================
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
LOG_LEVEL=INFO
ENVIRONMENT=production

# ============================================
# SECURITY SECRETS
# ============================================
JWT_SECRET=<generate-with-python-step-1>
TLS_ENABLED=true
TLS_CERT_PATH=/etc/xids/certs/cert.pem
TLS_KEY_PATH=/etc/xids/certs/key.pem

# ============================================
# DATA PATHS
# ============================================
MODEL_DIR=/data/models
LOG_DIR=/data/logs
DATA_DIR=/data

# ============================================
# KAFKA CONFIGURATION
# ============================================
KAFKA_BROKER=kafka:9092
KAFKA_TOPIC=intrusion-detection
KAFKA_GROUP_ID=xids-consumer
KAFKA_AUTO_OFFSET_RESET=earliest
KAFKA_SASL_ENABLED=false
KAFKA_SASL_PASSWORD=<generate-if-sasl-enabled>

# ============================================
# REDIS CONFIGURATION
# ============================================
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=<generate-with-openssl-step-3>

# ============================================
# ELASTICSEARCH CONFIGURATION
# ============================================
ELASTICSEARCH_HOST=elasticsearch
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_USERNAME=elastic
ELASTICSEARCH_PASSWORD=<generate-with-openssl-step-2>
ELASTICSEARCH_INDEX=xids-alerts

# ============================================
# SPLUNK CONFIGURATION (OPTIONAL)
# ============================================
SPLUNK_HOST=your-splunk.example.com
SPLUNK_PORT=8088
SPLUNK_TOKEN=<get-from-splunk-ui-step-5>
SPLUNK_ENABLED=false

# ============================================
# DATABASE CONFIGURATION (OPTIONAL)
# ============================================
DATABASE_URL=postgresql://xids:<password>@postgres:5432/x_ids
DATABASE_PASSWORD=<generate-with-python-step-4>
DATABASE_ENABLED=false

# ============================================
# PGADMIN CONFIGURATION (OPTIONAL)
# ============================================
PGADMIN_DEFAULT_EMAIL=admin@x-ids.local
PGADMIN_DEFAULT_PASSWORD=<generate-with-python-step-7>

# ============================================
# PROMETHEUS CONFIGURATION
# ============================================
PROMETHEUS_HOST=prometheus
PROMETHEUS_PORT=9090
PROMETHEUS_TOKEN=<generate-with-python-step-9>

# ============================================
# GRAFANA CONFIGURATION
# ============================================
GRAFANA_ADMIN_PASSWORD=<generate-with-python-step-8>
GF_SECURITY_ADMIN_USER=admin
GF_USERS_ALLOW_SIGN_UP=false

# ============================================
# TRAINING CONFIGURATION
# ============================================
TRAINING_EPOCHS=50
TRAINING_BATCH_SIZE=32
TRAINING_TEST_SIZE=0.2
TRAINING_RANDOM_STATE=42

# ============================================
# MODEL CONFIGURATION
# ============================================
MODEL_TYPE=ensemble
ENSEMBLE_MODELS=autoencoder,tcn,random_forest
ENSEMBLE_WEIGHTS=0.33,0.33,0.34

# ============================================
# SIEM INTEGRATION
# ============================================
SIEM_TYPE=elasticsearch
SIEM_HOST=elasticsearch
SIEM_PORT=9200

# ============================================
# FEATURE FLAGS
# ============================================
FEATURE_KAFKA_STREAMING=true
FEATURE_ELASTICSEARCH_STORAGE=true
FEATURE_PROMETHEUS_METRICS=true
FEATURE_JWT_AUTH=true
FEATURE_TLS=true

# ============================================
# RATE LIMITING
# ============================================
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# ============================================
# MONITORING
# ============================================
MONITORING_ENABLED=true
METRICS_PORT=9090

# ============================================
# COMPANY INFORMATION
# ============================================
COMPANY=Your-Company-Name
PROJECT_NAME=X-IDS
```

---

## 🛠️ Quick Generation Script

Save as `generate_secrets.sh`:

```bash
#!/bin/bash

echo "Generating X-IDS Secrets..."
echo ""

echo "1. JWT_SECRET:"
JWT_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
echo "JWT_SECRET=$JWT_SECRET"
echo ""

echo "2. ELASTICSEARCH_PASSWORD:"
ES_PASS=$(openssl rand -base64 24)
echo "ELASTICSEARCH_PASSWORD=$ES_PASS"
echo ""

echo "3. REDIS_PASSWORD:"
REDIS_PASS=$(openssl rand -base64 16)
echo "REDIS_PASSWORD=$REDIS_PASS"
echo ""

echo "4. DATABASE_PASSWORD:"
DB_PASS=$(python3 -c "import secrets; print(secrets.token_urlsafe(20))")
echo "DATABASE_PASSWORD=$DB_PASS"
echo ""

echo "5. PGADMIN_DEFAULT_PASSWORD:"
PG_PASS=$(python3 -c "import secrets; print(secrets.token_urlsafe(16))")
echo "PGADMIN_DEFAULT_PASSWORD=$PG_PASS"
echo ""

echo "6. GRAFANA_ADMIN_PASSWORD:"
GRAF_PASS=$(python3 -c "import secrets; print(secrets.token_urlsafe(16))")
echo "GRAFANA_ADMIN_PASSWORD=$GRAF_PASS"
echo ""

echo "7. PROMETHEUS_TOKEN:"
PROM_TOKEN=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
echo "PROMETHEUS_TOKEN=$PROM_TOKEN"
echo ""

echo "All secrets generated! Copy them to your .env file"
```

Run it:
```bash
bash generate_secrets.sh
```

---

## 🔒 Security Best Practices

1. **Never commit .env to Git**
   ```bash
   echo ".env" >> .gitignore
   git add .gitignore
   ```

2. **Restrict file permissions**
   ```bash
   chmod 600 .env
   ```

3. **Use secret management in production**
   - AWS Secrets Manager
   - HashiCorp Vault
   - GitHub Secrets
   - Azure Key Vault

4. **Rotate secrets regularly**
   - JWT_SECRET: Every 90 days
   - Passwords: Every 6 months
   - Tokens: Every 90 days

5. **Never log secrets**
   - Mask in logs
   - Don't print in debug mode
   - Use secret scanning tools

---

## ✅ Verification

After creating `.env`, verify:

```bash
# Check file permissions
ls -la .env
# Should show: -rw------- (600)

# Check for sensitive data in git
git grep -i password
# Should show: Nothing

# Test environment loading
source .env
echo $JWT_SECRET
# Should show: Your secret (not empty)
```

---

**Ready to deploy!** 🚀
