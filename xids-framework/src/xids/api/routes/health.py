"""Health check and monitoring API routes"""

import logging
from datetime import datetime
import psutil
import os

from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["health"])

# Global model storage
MODELS = {}


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "models_loaded": list(MODELS.keys()),
        "version": "1.0.0"
    }


@router.get("/ready")
async def readiness_check():
    """Readiness check endpoint"""
    if not MODELS:
        return {"ready": False, "reason": "No models loaded"}
    
    return {
        "ready": True,
        "models": len(MODELS),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/metrics")
async def get_system_metrics():
    """Get system metrics"""
    try:
        process = psutil.Process(os.getpid())
        
        return {
            "cpu_percent": process.cpu_percent(interval=0.1),
            "memory_mb": process.memory_info().rss / 1024 / 1024,
            "memory_percent": process.memory_percent(),
            "num_threads": process.num_threads(),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Error collecting metrics: {str(e)}")
        return {"error": str(e)}


@router.get("/version")
async def get_version():
    """Get API version and information"""
    return {
        "version": "1.0.0",
        "name": "X-IDS Inference API",
        "description": "Real-time Zero-Day Attack Detection",
        "timestamp": datetime.utcnow().isoformat()
    }
