"""Predictions API routes"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
import time

from fastapi import APIRouter, HTTPException, Query
import numpy as np

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/predictions", tags=["predictions"])

# Global model storage (will be injected from app context)
MODELS = {}
MODEL_STATS = {}


@router.post("/predict")
async def predict(request_data: Dict):
    """
    Make a single prediction
    
    Request:
    {
        "features": [f1, f2, ..., f77],
        "model": "rf",
        "explain": false
    }
    """
    try:
        start_time = time.time()
        
        features = request_data.get("features")
        model_name = request_data.get("model", "rf")
        explain = request_data.get("explain", False)
        
        if not features or len(features) != 77:
            raise HTTPException(status_code=400, detail="Invalid feature count")
        
        if model_name not in MODELS:
            raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found")
        
        # Make prediction
        features_array = np.array(features).reshape(1, -1)
        model = MODELS[model_name]
        prediction = model.predict(features_array)[0]
        confidence = float(model.predict_proba(features_array)[0].max())
        
        latency_ms = (time.time() - start_time) * 1000
        
        response = {
            "prediction": float(prediction),
            "model": model_name,
            "confidence": confidence,
            "latency_ms": latency_ms,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Update statistics
        if model_name not in MODEL_STATS:
            MODEL_STATS[model_name] = {"count": 0, "total_latency": 0}
        
        MODEL_STATS[model_name]["count"] += 1
        MODEL_STATS[model_name]["total_latency"] += latency_ms
        
        return response
        
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-predict")
async def batch_predict(request_data: Dict):
    """
    Make batch predictions
    
    Request:
    {
        "data": [[f1, ..., f77], ...],
        "model": "rf"
    }
    """
    try:
        start_time = time.time()
        
        data = request_data.get("data", [])
        model_name = request_data.get("model", "rf")
        
        if not data or len(data) == 0:
            raise HTTPException(status_code=400, detail="Empty data")
        
        if model_name not in MODELS:
            raise HTTPException(status_code=404, detail=f"Model '{model_name}' not found")
        
        # Make batch predictions
        features_array = np.array(data)
        model = MODELS[model_name]
        predictions = model.predict(features_array)
        
        latency_ms = (time.time() - start_time) * 1000
        
        return {
            "predictions": [float(p) for p in predictions],
            "model": model_name,
            "count": len(predictions),
            "latency_ms": latency_ms,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Batch prediction error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models")
async def get_available_models():
    """Get list of available models"""
    models_info = []
    
    for model_name, model in MODELS.items():
        stats = MODEL_STATS.get(model_name, {})
        models_info.append({
            "name": model_name,
            "type": type(model).__name__,
            "predictions_made": stats.get("count", 0),
            "avg_latency_ms": stats.get("total_latency", 0) / max(stats.get("count", 1), 1)
        })
    
    return {"models": models_info}


@router.get("/model/{model_name}/stats")
async def get_model_stats(model_name: str):
    """Get statistics for a specific model"""
    if model_name not in Model_STATS:
        raise HTTPException(status_code=404, detail=f"No stats for model '{model_name}'")
    
    stats = MODEL_STATS[model_name]
    return {
        "model": model_name,
        "predictions_made": stats.get("count", 0),
        "avg_latency_ms": stats.get("total_latency", 0) / max(stats.get("count", 1), 1),
        "total_latency_ms": stats.get("total_latency", 0)
    }
