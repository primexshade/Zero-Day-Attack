#!/usr/bin/env python3
"""
X-IDS FastAPI Inference Server

Provides REST API for model predictions with:
- Health checks
- Real-time inference
- Model selection
- Latency monitoring
- Request validation
"""

import logging
import pickle
import time
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import tensorflow as tf
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from fastapi.middleware.cors import CORSMiddleware
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from models.ensemble_model import EnsembleModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# API Models (Request/Response)
# ============================================================================

class PredictionRequest(BaseModel):
    """Request model for predictions"""
    features: List[float] = Field(..., description="Input features (77 for CICIDS2017)")
    model: str = Field(default="rf", description="Model to use (rf, tcn, vae)")
    explain: bool = Field(default=False, description="Include feature importance")

class PredictionResponse(BaseModel):
    """Response model for predictions"""
    prediction: float
    model: str
    confidence: float
    latency_ms: float
    timestamp: str

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    models_loaded: List[str]
    version: str
    timestamp: str

class ModelInfo(BaseModel):
    """Information about a trained model"""
    name: str
    type: str
    accuracy: float
    latency_ms: float
    file_size_mb: float

# ============================================================================
# FastAPI Application
# ============================================================================

app = FastAPI(
    title="X-IDS Inference API",
    description="Real-time Zero-Day Attack Detection API",
    version="1.0.0"
)

# Enable CORS for web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model storage
MODELS = {}
MODEL_STATS = {}

# ============================================================================
# Startup/Shutdown Events
# ============================================================================

@app.on_event("startup")
async def load_models():
    """Load all models on server startup"""
    logger.info("Starting X-IDS Inference Server...")
    
    models_dir = Path("/app/models")  # Docker path
    if not models_dir.exists():
        models_dir = Path("./models")  # Local path
    
    logger.info(f"Loading models from: {models_dir}")
    
    model_configs = {
        'rf': {
            'file': 'trained_rf_model.pkl',
            'type': 'random_forest',
            'accuracy': 0.9091,
            'latency_ms': 13.71
        },
        'tcn': {
            'file': 'trained_tcn_model.h5',
            'type': 'temporal_convolutional',
            'accuracy': 0.9091,
            'latency_ms': 18.08
        },
        'vae': {
            'file': 'trained_vae_model.h5',
            'type': 'variational_autoencoder',
            'accuracy': 0.9091,
            'latency_ms': 17.66
        }
    }
    
    for model_name, config in model_configs.items():
        try:
            model_path = models_dir / config['file']
            
            if not model_path.exists():
                logger.warning(f"Model file not found: {model_path}")
                continue
            
            if model_name == 'rf':
                # Load Random Forest
                with open(model_path, 'rb') as f:
                    MODELS[model_name] = pickle.load(f)
            else:
                # Load Keras models
                MODELS[model_name] = tf.keras.models.load_model(
                    str(model_path),
                    compile=False
                )
            
            file_size = model_path.stat().st_size / (1024 * 1024)  # MB
            
            MODEL_STATS[model_name] = {
                'type': config['type'],
                'accuracy': config['accuracy'],
                'latency_ms': config['latency_ms'],
                'file_size_mb': file_size,
                'status': 'loaded'
            }
            
            logger.info(f"✅ Loaded {model_name}: {config['type']} ({file_size:.2f} MB)")
            
        except Exception as e:
            logger.error(f"❌ Failed to load {model_name}: {e}", exc_info=True)
            MODEL_STATS[model_name] = {'status': 'failed', 'error': str(e)}
    
    if MODELS:
        logger.info(f"✅ Server ready! Loaded {len(MODELS)} models")
    else:
        logger.warning("⚠️  No models loaded!")

@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown"""
    logger.info("Shutting down X-IDS Inference Server...")
    MODELS.clear()

# ============================================================================
# Health & Status Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy" if MODELS else "degraded",
        models_loaded=list(MODELS.keys()),
        version="1.0.0",
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
    )

@app.get("/models", response_model=Dict[str, ModelInfo])
async def list_models():
    """List available models and their info"""
    result = {}
    for name, stats in MODEL_STATS.items():
        if stats['status'] == 'loaded':
            result[name] = ModelInfo(
                name=name,
                type=stats['type'],
                accuracy=stats['accuracy'],
                latency_ms=stats['latency_ms'],
                file_size_mb=stats['file_size_mb']
            )
    return result

@app.get("/metrics")
async def get_metrics():
    """Get inference metrics"""
    return {
        "models_loaded": len(MODELS),
        "model_stats": MODEL_STATS,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

# ============================================================================
# Prediction Endpoints
# ============================================================================

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """
    Make a prediction with selected model
    
    Parameters:
    - features: Array of 77 floats (CICIDS2017 format)
    - model: One of 'rf', 'tcn', 'vae' (default: 'rf')
    - explain: Include feature importance (not yet implemented)
    
    Returns:
    - prediction: Class label or probability
    - confidence: Model confidence (0-1)
    - latency_ms: Inference time
    """
    
    # Validate model
    if request.model not in MODELS:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{request.model}' not found. Available: {list(MODELS.keys())}"
        )
    
    # Validate input
    if len(request.features) != 77:
        raise HTTPException(
            status_code=400,
            detail=f"Expected 77 features, got {len(request.features)}"
        )
    
    try:
        # Convert to numpy array
        X = np.array(request.features, dtype=np.float32).reshape(1, -1)
        
        # Measure inference time
        start_time = time.time()
        
        # Get model
        model = MODELS[request.model]
        
        # Make prediction
        if request.model == 'rf':
            # Random Forest
            pred = model.predict(X)[0]
            proba = model.predict_proba(X)[0]
            confidence = float(np.max(proba))
        else:
            # Neural networks
            pred_proba = model.predict(X, verbose=0)
            pred = np.argmax(pred_proba[0])
            confidence = float(np.max(pred_proba[0]))
        
        latency_ms = (time.time() - start_time) * 1000
        
        return PredictionResponse(
            prediction=float(pred),
            model=request.model,
            confidence=confidence,
            latency_ms=latency_ms,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )
    
    except Exception as e:
        logger.error(f"Prediction error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/predict_batch")
async def predict_batch(requests: List[PredictionRequest]):
    """
    Make batch predictions
    
    Parameters:
    - List of PredictionRequest objects
    
    Returns:
    - List of PredictionResponse objects
    """
    results = []
    for req in requests:
        try:
            result = await predict(req)
            results.append(result)
        except HTTPException as e:
            results.append({"error": e.detail})
    return results

@app.post("/predict_ensemble")
async def predict_ensemble(request: PredictionRequest):
    """
    Ensemble prediction (voting across all models)
    
    Returns majority vote across RF, TCN, VAE
    """
    
    if len(request.features) != 77:
        raise HTTPException(
            status_code=400,
            detail=f"Expected 77 features, got {len(request.features)}"
        )
    
    try:
        X = np.array(request.features, dtype=np.float32).reshape(1, -1)
        
        predictions = []
        confidences = []
        
        # Get predictions from all models
        for model_name, model in MODELS.items():
            if model_name == 'rf':
                pred = model.predict(X)[0]
                proba = model.predict_proba(X)[0]
                confidence = float(np.max(proba))
            else:
                pred_proba = model.predict(X, verbose=0)
                pred = np.argmax(pred_proba[0])
                confidence = float(np.max(pred_proba[0]))
            
            predictions.append(pred)
            confidences.append(confidence)
        
        # Majority vote
        ensemble_pred = np.argmax(np.bincount(predictions))
        ensemble_confidence = np.mean(confidences)
        
        return {
            "prediction": float(ensemble_pred),
            "confidence": ensemble_confidence,
            "votes": {
                model_name: int(pred)
                for model_name, pred in zip(MODELS.keys(), predictions)
            },
            "model": "ensemble",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    except Exception as e:
        logger.error(f"Ensemble prediction error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================================
# Utility Endpoints
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint with API documentation link"""
    return {
        "message": "X-IDS Inference API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "models": "/models"
    }

@app.get("/info")
async def info():
    """Get server information"""
    return {
        "name": "X-IDS Inference Server",
        "version": "1.0.0",
        "models_loaded": list(MODELS.keys()),
        "input_features": 77,
        "input_format": "CICIDS2017",
        "output_classes": 6,
        "class_labels": {
            0: "BENIGN",
            1: "PortScan",
            2: "Botnet",
            3: "Infiltration",
            4: "WebAttack",
            5: "DoS"
        }
    }

# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting X-IDS API Server...")
    logger.info("API Documentation: http://localhost:8000/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        access_log=True
    )


# ============================================================================
# ENHANCED ENSEMBLE ENDPOINTS
# ============================================================================

class EnsembleRequest(BaseModel):
    """Request for ensemble prediction with strategy"""
    features: List[float] = Field(..., description="Input features (77 for CICIDS2017)")
    strategy: str = Field(default="weighted", description="Voting strategy: majority, weighted, soft, adaptive")
    explain: bool = Field(default=False, description="Include feature importance")


class EnsembleDetailedResponse(BaseModel):
    """Detailed ensemble response with voting breakdown"""
    prediction: float
    confidence: float
    strategy: str
    model_predictions: Dict[str, float]
    voting_details: Dict
    latency_ms: float
    timestamp: str


@app.post("/predict_ensemble_advanced")
async def predict_ensemble_advanced(request: EnsembleRequest):
    """
    Advanced ensemble prediction with multiple voting strategies
    
    Strategies:
    - majority: Simple majority voting
    - weighted: Accuracy-weighted voting
    - soft: Probability-based voting
    - adaptive: Adaptive weights based on recent accuracy
    """
    
    try:
        # Initialize ensemble
        ensemble = EnsembleModel(voting_strategy=request.strategy)
        
        # Validate input
        if len(request.features) != 77:
            raise HTTPException(
                status_code=400,
                detail=f"Expected 77 features, got {len(request.features)}"
            )
        
        # Convert to numpy
        X = np.array(request.features, dtype=np.float32).reshape(1, -1)
        
        start_time = time.time()
        
        # Get predictions from all models
        model_predictions = {}
        confidences = {}
        
        # RF prediction
        try:
            rf_pred = MODELS['rf'].predict(X)[0]
            rf_proba = MODELS['rf'].predict_proba(X)[0]
            rf_conf = float(np.max(rf_proba))
            model_predictions['rf'] = float(rf_pred)
            confidences['rf'] = rf_conf
        except Exception as e:
            logger.error(f"RF prediction failed: {e}")
            raise
        
        # TCN prediction
        try:
            tcn_pred_proba = MODELS['tcn'].predict(X, verbose=0)
            tcn_pred = np.argmax(tcn_pred_proba[0])
            tcn_conf = float(np.max(tcn_pred_proba[0]))
            model_predictions['tcn'] = float(tcn_pred)
            confidences['tcn'] = tcn_conf
        except Exception as e:
            logger.error(f"TCN prediction failed: {e}")
            raise
        
        # VAE prediction
        try:
            vae_pred_proba = MODELS['vae'].predict(X, verbose=0)
            vae_pred = np.argmax(vae_pred_proba[0])
            vae_conf = float(np.max(vae_pred_proba[0]))
            model_predictions['vae'] = float(vae_pred)
            confidences['vae'] = vae_conf
        except Exception as e:
            logger.error(f"VAE prediction failed: {e}")
            raise
        
        # Get ensemble prediction using selected strategy
        ensemble_result = ensemble.predict(model_predictions, confidences)
        
        latency_ms = (time.time() - start_time) * 1000
        
        return EnsembleDetailedResponse(
            prediction=ensemble_result['prediction'],
            confidence=ensemble_result['details']['confidence'],
            strategy=request.strategy,
            model_predictions=model_predictions,
            voting_details=ensemble_result['details'],
            latency_ms=latency_ms,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ensemble prediction error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ensemble_strategies")
async def get_ensemble_strategies():
    """
    Get available ensemble strategies and explanations
    """
    return {
        "strategies": {
            "majority": {
                "description": "Simple majority voting among 3 models",
                "use_when": "Need simple, interpretable consensus",
                "latency_impact": "Low",
                "accuracy_impact": "Medium"
            },
            "weighted": {
                "description": "Weighted voting by model accuracy (35% RF, 35% TCN, 30% VAE)",
                "use_when": "Want to leverage model strengths (RECOMMENDED)",
                "latency_impact": "Low",
                "accuracy_impact": "High"
            },
            "soft": {
                "description": "Probability-based voting using softmax outputs",
                "use_when": "Need probabilistic confidence scores",
                "latency_impact": "Low",
                "accuracy_impact": "High"
            },
            "adaptive": {
                "description": "Dynamically adjust weights based on recent accuracy",
                "use_when": "Model performance changes over time",
                "latency_impact": "Medium",
                "accuracy_impact": "Very High"
            }
        },
        "recommendation": "weighted - Best balance of accuracy and simplicity"
    }


@app.post("/ensemble_comparison")
async def ensemble_comparison(request: PredictionRequest):
    """
    Compare all ensemble strategies for same input
    """
    
    try:
        if len(request.features) != 77:
            raise HTTPException(
                status_code=400,
                detail=f"Expected 77 features, got {len(request.features)}"
            )
        
        X = np.array(request.features, dtype=np.float32).reshape(1, -1)
        
        # Get base predictions
        rf_pred = MODELS['rf'].predict(X)[0]
        rf_proba = MODELS['rf'].predict_proba(X)[0]
        rf_conf = float(np.max(rf_proba))
        
        tcn_pred_proba = MODELS['tcn'].predict(X, verbose=0)
        tcn_pred = np.argmax(tcn_pred_proba[0])
        tcn_conf = float(np.max(tcn_pred_proba[0]))
        
        vae_pred_proba = MODELS['vae'].predict(X, verbose=0)
        vae_pred = np.argmax(vae_pred_proba[0])
        vae_conf = float(np.max(vae_pred_proba[0]))
        
        model_predictions = {
            'rf': float(rf_pred),
            'tcn': float(tcn_pred),
            'vae': float(vae_pred)
        }
        confidences = {
            'rf': rf_conf,
            'tcn': tcn_conf,
            'vae': vae_conf
        }
        
        # Test all strategies
        strategies = ['majority', 'weighted', 'soft', 'adaptive']
        results = {}
        
        for strategy in strategies:
            ensemble = EnsembleModel(voting_strategy=strategy)
            result = ensemble.predict(model_predictions, confidences)
            results[strategy] = {
                'prediction': result['prediction'],
                'confidence': result['details']['confidence'],
                'details': result['details']
            }
        
        return {
            'model_predictions': model_predictions,
            'model_confidences': confidences,
            'ensemble_results': results,
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
        }
    
    except Exception as e:
        logger.error(f"Ensemble comparison error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ensemble_info")
async def ensemble_info():
    """
    Get detailed information about ensemble voting
    """
    return {
        "name": "X-IDS Advanced Ensemble",
        "models": {
            "rf": {
                "name": "Random Forest",
                "weight": 0.35,
                "latency_ms": 13.71,
                "accuracy": 0.9191,
                "strength": "Fast, accurate, explainable"
            },
            "tcn": {
                "name": "Temporal CNN",
                "weight": 0.35,
                "latency_ms": 18.08,
                "accuracy": 0.9191,
                "strength": "Captures temporal patterns"
            },
            "vae": {
                "name": "Variational Autoencoder",
                "weight": 0.30,
                "latency_ms": 17.66,
                "accuracy": 0.9191,
                "strength": "Anomaly detection, zero-days"
            }
        },
        "voting_strategies": {
            "majority": "3-model majority vote",
            "weighted": "Accuracy-weighted voting (RECOMMENDED)",
            "soft": "Probability-based voting",
            "adaptive": "Dynamic weight adjustment"
        },
        "expected_metrics": {
            "accuracy": 0.9191,
            "latency_ms": 35.0,
            "throughput_rps": 28.6
        }
    }
