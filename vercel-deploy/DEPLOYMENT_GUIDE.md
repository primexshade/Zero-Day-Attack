# 🚀 X-IDS Vercel Deployment Guide

## Quick Deploy (3 Steps)

### Step 1: Install Vercel CLI
```bash
npm i -g vercel
```

### Step 2: Deploy from directory
```bash
cd vercel-deploy
vercel
```

### Step 3: Follow prompts
```
? Set up and deploy ".../vercel-deploy"? [Y/n] y
? Which scope? (choose your Vercel account)
? Link to existing project? [y/N] N
? What's your project's name? xids-framework
? In which directory is your code? ./
```

---

## After Deployment

### 1. Update Frontend API Endpoint
Open `public/index.html` and replace:
```javascript
const API_URL = "https://your-deployment-name.vercel.app/api";
```

With your actual Vercel deployment URL

### 2. Test API Health
```bash
curl https://your-deployment-name.vercel.app/api/health
```

### 3. Test Prediction
```bash
curl -X POST https://your-deployment-name.vercel.app/api/predict \
  -H "Content-Type: application/json" \
  -d '{"features": [0.1, 0.2, 0.3, ..., 0.9]}'
```

---

## What Gets Deployed

### Frontend (Static)
- `/public/index.html` - Complete X-IDS dashboard
- All CSS and JavaScript included
- Zero dependencies, instant load

### Backend (Serverless Functions)
- `/api/predict.py` - Single prediction endpoint
- `/api/batch.py` - Batch processing endpoint  
- `/api/health.py` - Health check endpoint

### Models (Bundled)
- `Random Forest` (19.62 MB)
- `Temporal CNN` (276 KB)
- `Variational Autoencoder` (227 KB)

**Total deployment: ~20.5 MB**

---

## Features Available

✅ Quick Test (no data needed)
✅ Manual Features (enter 77 values)
✅ Upload File (CSV/JSON batch)
✅ Ensemble Mode (93-94% accuracy)
✅ Real-time metrics
✅ Recent alerts tracking
✅ Threat distribution chart

---

## Vercel Limitations

⚠️ **Cold Start:** First request takes 10-30s (loads models)
⚠️ **Warm Start:** Subsequent requests <2s
⚠️ **Timeout:** Max 30s per request (enough for batch)
⚠️ **Memory:** 1024 MB per function
⚠️ **File Size:** 250 MB limit per deployment

---

## Troubleshooting

### Models Not Loading
Check logs:
```bash
vercel logs [deployment-url]
```

### API Returns 503
Models are loading (cold start). Wait 30s and retry.

### CORS Errors
Should be fixed in vercel.json headers. If not, contact Vercel support.

### Frontend Can't Connect
Make sure API_URL in index.html matches your deployment domain.

---

## Monitoring

After deployment, monitor from Vercel dashboard:
- https://vercel.com/dashboard
- View logs, analytics, deployments
- Check API response times and errors

---

## Rollback

If deployment has issues:
```bash
vercel rollback
```

---

## Scaling

For production use:
1. Consider dedicated backend (Railway, Render, AWS Lambda)
2. Host models separately (S3 or Cloudinary)
3. Use CDN for static assets
4. Implement request queuing

---

## Next Steps

After successful deployment:
1. ✅ Open your Vercel URL in browser
2. ✅ Click "🔴 Test Critical" to verify
3. ✅ Try uploading sample data
4. ✅ Share URL with team!

**Your X-IDS is now on the internet! 🌍**
