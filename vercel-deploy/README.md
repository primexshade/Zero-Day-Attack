# X-IDS: Vercel Deployment Package

**Deploy your AI-powered Intrusion Detection System to the cloud in 3 commands!**

---

## ⚡ Quick Deploy

```bash
# 1. Install Vercel CLI (one time)
npm i -g vercel

# 2. Deploy from this directory
cd vercel-deploy
vercel --prod

# 3. Open your live URL in browser
# 🎉 Your X-IDS is now online!
```

---

## 📊 What's Included

### Frontend
- ✅ Complete dashboard (32 KB, zero dependencies)
- ✅ 4 prediction modes (Quick Test, Manual, Upload, Ensemble)
- ✅ Real-time metrics & alerts
- ✅ Dark theme with cybersecurity styling

### Backend (Serverless)
- ✅ `/api/predict` - Single prediction endpoint
- ✅ `/api/batch` - Batch processing endpoint
- ✅ `/api/health` - Health monitoring

### AI Models (Bundled)
- ✅ Random Forest (19.6 MB) - Fast, accurate
- ✅ Temporal CNN (276 KB) - Sequence detection
- ✅ VAE (227 KB) - Anomaly detection
- ✅ Ensemble voting (93-94% accuracy)

---

## 🚀 Deployment Steps

### Prerequisites
1. Node.js installed (`node --version`)
2. Vercel account (free tier works!)
   - Sign up: https://vercel.com
3. Vercel CLI: `npm i -g vercel`

### Deploy

```bash
# Navigate to deployment directory
cd vercel-deploy

# Authenticate with Vercel
vercel login

# Deploy to production
vercel --prod
```

### Configuration
Vercel will ask:
- **Scope**: Choose your account
- **Project name**: `xids-framework` (or custom)
- **Build command**: (Skip, auto-detected)
- **Output directory**: (Skip, auto-detected)

### After Deployment

1. **Get your URL**: Vercel shows it in terminal
   ```
   ✓ Vercel CLI 28.x.x
   ✓ Production: https://xids-framework-abc123.vercel.app
   ```

2. **Update Frontend API Endpoint**
   
   Open `public/index.html` and find line ~15:
   ```javascript
   const API_URL = "https://your-deployment-name.vercel.app/api";
   ```
   
   Replace with your actual Vercel URL

3. **Test the Deployment**
   ```bash
   # Health check
   curl https://your-deployment.vercel.app/api/health
   
   # Or open in browser:
   # https://your-deployment.vercel.app
   ```

---

## 📝 API Endpoints

All endpoints include CORS headers for frontend access.

### Health Check
```bash
GET /api/health

Response:
{
  "status": "healthy",
  "models_loaded": ["rf", "tcn", "vae"],
  "version": "1.0.0",
  "timestamp": "2026-03-15T15:44:27"
}
```

### Single Prediction
```bash
POST /api/predict
Content-Type: application/json

{
  "features": [0.1, 0.2, 0.3, ..., 0.9]  // 77 values, each 0.0-1.0
}

Response:
{
  "prediction": 0,           // 0=BENIGN, 1=PortScan, 2=Botnet, etc.
  "confidence": 92.5,        // 0-100%
  "threat_type": "BENIGN",
  "models": {
    "rf": 0,
    "tcn": 0,
    "vae": 0
  },
  "timestamp": "2026-03-15T15:44:27"
}
```

### Batch Predictions
```bash
POST /api/batch
Content-Type: application/json

{
  "features_list": [
    [0.1, 0.2, ..., 0.9],
    [0.5, 0.6, ..., 0.2],
    [0.9, 0.1, ..., 0.1]
  ]
}

Response:
{
  "total": 3,
  "processed": 3,
  "errors": 0,
  "results": [
    {"packet": 0, "prediction": 0, "confidence": 92.5, "threat_type": "BENIGN"},
    {"packet": 1, "prediction": 2, "confidence": 88.3, "threat_type": "Botnet"},
    {"packet": 2, "prediction": 5, "confidence": 95.1, "threat_type": "DoS"}
  ],
  "timestamp": "2026-03-15T15:44:27"
}
```

---

## ⚡ Performance Expectations

| Scenario | Time | Notes |
|----------|------|-------|
| Cold start | 10-30s | First request, loading models |
| Warm start | <2s | Subsequent requests (models cached) |
| Single prediction | 100-500ms | After models loaded |
| Batch (100 packets) | 3-5s | Linear with batch size |

---

## ⚠️ Vercel Limitations & Solutions

### Cold Start Delay
**Problem**: First request takes 10-30 seconds (loading models)

**Solutions**:
- Add a "warming" endpoint that keeps function alive
- Use Vercel's cron functions (Pro plan)
- For production: consider dedicated backend

### Function Timeout
**Limit**: 30 seconds per request

**Impact**: Batch processing max ~500 packets

**Solution**: Split large batches or use dedicated backend

### File Size
**Limit**: 250 MB per deployment

**Current**: ~20.5 MB (safe!)

### Memory
**Limit**: 1024 MB per function

**Current**: Using ~800 MB when models loaded (safe!)

---

## 🔧 Troubleshooting

### Models Not Loading
Check Vercel logs:
```bash
vercel logs https://your-deployment.vercel.app
```

Common causes:
- Models didn't upload (check models/ directory)
- Python dependencies missing (check requirements.txt)
- File permissions

### API Returns 503 Error
**Cause**: Cold start, function still initializing

**Solution**: Wait 30 seconds and retry

### CORS Errors in Frontend
Already configured in `vercel.json`

If still failing:
- Clear browser cache
- Try incognito mode
- Check API_URL in index.html

### Deployment Fails
Check error message:
```bash
# Re-run with verbose output
vercel --prod --debug
```

Common issues:
- Missing dependencies in requirements.txt
- Python syntax errors
- File path issues

---

## 📊 Monitoring & Debugging

### View Deployment
```bash
# Open Vercel dashboard
vercel dashboard
```

### View Function Logs
```bash
vercel logs [deployment-url] --follow
```

### View Build Logs
```bash
vercel logs [deployment-url] --build
```

### Rollback to Previous
```bash
vercel rollback
```

---

## 🔐 Security Notes

### No Sensitive Data
- No API keys stored in code
- Models are public (shareable)
- Frontend is fully client-side safe

### Recommendations for Production
1. Add authentication to API endpoints
2. Implement rate limiting
3. Use HTTPS (Vercel default)
4. Monitor usage in dashboard

---

## 📈 Scaling Beyond Vercel

For production workloads >100 requests/second:

### Option 1: Railway
```bash
# Deploy to Railway (Python-native)
railway login
railway init
railway up
```

### Option 2: Render
```bash
# Push to Render via Git
git init
git add .
git commit -m "X-IDS deployment"
git push heroku main
```

### Option 3: AWS Lambda
- Better cold start performance
- Unlimited scale
- More configuration needed

---

## 📚 File Structure

```
vercel-deploy/
├── api/
│   ├── predict.py          # Single prediction handler
│   ├── batch.py            # Batch prediction handler
│   └── health.py           # Health check handler
├── models/
│   ├── trained_rf_model.pkl
│   ├── trained_tcn_model.h5
│   └── trained_vae_model.h5
├── public/
│   └── index.html          # Dashboard
├── vercel.json             # Vercel config
├── requirements.txt        # Python dependencies
├── deploy.sh              # Deploy script
└── DEPLOYMENT_GUIDE.md    # This file
```

---

## 🎯 Next Steps

1. ✅ Deploy with `vercel --prod`
2. ✅ Get your Vercel URL
3. ✅ Update API_URL in index.html
4. ✅ Test with `/api/health`
5. ✅ Open dashboard and click "Test Critical"
6. ✅ Share URL with team!

---

## 💡 Tips

- **Share easily**: Vercel URL works on any device
- **Free HTTPS**: Automatic SSL certificate
- **Analytics**: Check Vercel dashboard for stats
- **Custom domain**: Add domain in Vercel settings
- **Environment variables**: Add in Vercel dashboard if needed

---

## ❓ FAQ

**Q: Can I use the free tier?**
A: Yes! Free tier includes 1,000 function invocations/day

**Q: What about the streaming/Kafka features?**
A: Vercel serverless doesn't support persistent connections. Keep those locally.

**Q: Can I deploy multiple versions?**
A: Yes! Each `vercel` command creates a preview. Use `vercel --prod` for production.

**Q: How do I update after deployment?**
A: Push changes locally, then `vercel --prod` again

**Q: Is my data private?**
A: Your data never leaves Vercel's servers. No external API calls made.

---

## 🚀 You're Ready!

Your X-IDS is cloud-ready. Deploy now with:

```bash
cd vercel-deploy
vercel --prod
```

**Questions?** Check the logs:
```bash
vercel logs [deployment-url]
```

Happy threat hunting! 🎯
