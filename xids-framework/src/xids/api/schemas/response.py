"""Response schemas for X-IDS API"""

from typing import List, Dict, Optional, Any
from pydantic import BaseModel


class PredictionResponse(BaseModel):
    """Response model for predictions"""
    prediction: float
    model: str
    confidence: float
    latency_ms: float
    timestamp: str


class BatchPredictionResponse(BaseModel):
    """Response model for batch predictions"""
    predictions: List[float]
    model: str
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


class MetricsResponse(BaseModel):
    """Model performance metrics"""
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: float


class ExplanationResponse(BaseModel):
    """Explanation response"""
    feature_importance: Dict[str, float]
    top_features: List[str]
    explanation_method: str
    timestamp: str


class AlertResponse(BaseModel):
    """Alert response"""
    alert_id: str
    threat_level: str
    message: str
    timestamp: str
    details: Dict[str, Any]


class ErrorResponse(BaseModel):
    """Error response"""
    error: str
    detail: str
    timestamp: str
