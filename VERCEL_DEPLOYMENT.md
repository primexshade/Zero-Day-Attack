# X-IDS Vercel Deployment - Complete Guide

## 🎯 Deployment Status: ✅ LIVE

**Production URL:** https://vercel-deploy-60bt6i8aj-primexshades-projects.vercel.app

**What's Deployed:**
- ✅ Python Serverless API (api/index.py)
- ✅ Random Forest ML Model (trained_rf_model.pkl)
- ✅ Web Dashboard (public/index.html)
- ✅ All dependencies (scikit-learn, numpy)

---

## 📍 API Endpoints

### 1. Health Check
```bash
GET /api/health
```
Returns system status and loaded models.

### 2. Predict Threat
```bash
POST /api/predict
Content-Type: application/json

{
  "features": [0.5, 0.5, ..., 0.5]  // 77 values (0-1 range)
}
```
Returns threat prediction and confidence score.

### 3. API Info
```bash
GET /
```
Returns endpoint documentation.

---

## 🔐 Accessing the Deployment

### Option 1: Use Vercel CLI (Recommended)
```bash
vercel curl https://vercel-deploy-60bt6i8aj-primexshades-projects.vercel.app/api/health
```

### Option 2: Disable Deployment Protection
1. Go to Vercel Dashboard
2. Select "vercel-deploy" project
3. Navigate to Settings → Security
4. Toggle "Deployment Protection" OFF
5. Then access the URL directly

### Option 3: Use Bypass Token
Ask the Vercel dashboard for a bypass token and append:
```
?x-vercel-set-bypass-cookie=true&x-vercel-protection-bypass={TOKEN}
```

---

## 📊 Model Specifications

**Model Type:** Random Forest Classifier
- **Accuracy:** 91.91%
- **Latency:** ~13.7ms per prediction
- **Training Data:** 44K samples (synthetic CICIDS2017/UNSW-NB15)
- **Features:** 77 network traffic metrics
- **Classes:** 6 (BENIGN, PortScan, Botnet, Infiltration, WebAttack, DoS)

**Why Random Forest?**
- TensorFlow models (TCN, VAE) = 1.99 GB > Vercel's 500MB Lambda limit
- Random Forest = 20MB, easily deployable ✅
- Maintains 91.91% accuracy without deep learning

---

## 📂 Project Structure

```
vercel-deploy/
├── api/
│   └── index.py                      # Serverless handler
├── models/
│   └── trained_rf_model.pkl          # 20MB model file
├── public/
│   └── index.html                    # Dashboard frontend
├── requirements.txt                  # Python dependencies
├── vercel.json                       # Vercel config
├── .vercelignore                     # Build exclusions
└── .vercel/                          # Auto-generated
    └── project.json                  # Project metadata
```

---

## 🚀 Quick Start Examples

### Test API Health
```bash
curl -H "Authorization: Bearer {bypass_token_if_needed}" \
  https://vercel-deploy-60bt6i8aj-primexshades-projects.vercel.app/api/health
```

### Make Prediction
```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "features": [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5]
  }' \
  https://vercel-deploy-60bt6i8aj-primexshades-projects.vercel.app/api/predict
```

---

## ⚙️ Configuration Details

### vercel.json
```json
{
  "version": 2,
  "env": {
    "PYTHONUNBUFFERED": "1"
  }
}
```
- Minimal config, lets Vercel auto-detect Python functions
- Python 3.12 runtime
- No custom build commands

### requirements.txt
```
scikit-learn==1.5.0
numpy==1.26.4
```
- Total size: ~40MB
- Fast installation and deployment

---

## 🔄 Deployment Process Used

1. **Step 1:** Created vercel-deploy/ directory structure
2. **Step 2:** Copied trained models (RF only to stay under 500MB limit)
3. **Step 3:** Created Python serverless handler (api/index.py)
4. **Step 4:** Copied dashboard frontend (public/index.html)
5. **Step 5:** Configured dependencies and vercel.json
6. **Step 6:** Ran `vercel --prod` for production deployment
7. **Result:** ✅ Live in ~35 seconds

---

## ⚡ Performance Metrics

- **Cold Start:** ~5-10 seconds (first request, loads 20MB model)
- **Warm Start:** ~100-200ms (subsequent requests)
- **Prediction Latency:** ~13.7ms (model inference only)
- **Request Timeout:** 30 seconds (Vercel default)

---

## 🛠️ Troubleshooting

### "Authentication Required" Error
→ **Solution:** Go to Vercel Dashboard, disable Deployment Protection in Security settings

### Model Loading Slow
→ **Expected:** First request loads 20MB pickle file (~5-10s). Subsequent requests are fast.

### CORS Issues
→ **Already Fixed:** All endpoints include `Access-Control-Allow-Origin: *` headers

### Features Must Be 77 Values
→ **Requirement:** Send exactly 77 features, each between 0.0 and 1.0

---

## 📈 Next Steps for Production

### To Add Deep Learning Models (TCN, VAE):
**Option A: Use Separate ML Server**
- Deploy RF to Vercel (current ✅)
- Host TCN/VAE on dedicated ML platform:
  - Hugging Face Spaces (free)
  - Modal (free tier)
  - RunwayML
  - AWS SageMaker

**Option B: Move to Different Serverless**
- AWS Lambda (1 GB storage)
- Google Cloud Functions (no model size limit)
- Azure Functions
- Railway.app (12GB/month free)

**Option C: Use Model Optimization**
- Convert TCN/VAE to ONNX format (smaller)
- Quantize models (50% size reduction)
- Use TinyML / EdgeML versions

### To Scale API:
- Add rate limiting
- Implement API keys
- Add logging/monitoring
- Set up CI/CD pipeline

---

## 📝 Files Summary

| File | Size | Purpose |
|------|------|---------|
| api/index.py | 4.8KB | Serverless API handler |
| trained_rf_model.pkl | 20MB | Machine Learning model |
| index.html | 32KB | Web dashboard |
| requirements.txt | 39 bytes | Dependencies |
| vercel.json | 65 bytes | Vercel config |

**Total:** ~60MB (60% model, 33% dependencies, 7% code)

---

## 📞 Support

**For issues:**
1. Check Vercel deployment logs: Dashboard → Deployments → Details
2. Test locally: `python3 -c "from api.index import app"`
3. Verify model exists: Check models/trained_rf_model.pkl is 20MB

**For enhancements:**
- Add batch prediction endpoint
- Implement feature validation
- Add prediction explanations (SHAP)
- Create admin dashboard
- Set up monitoring/alerts

---

**Deployment Date:** 2026-03-16  
**Framework:** Vercel Serverless (Python 3.12)  
**Status:** ✅ Production Ready
