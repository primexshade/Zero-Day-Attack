"""Request schemas for X-IDS API"""

from typing import List, Optional
from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    """Request model for predictions"""
    features: List[float] = Field(..., description="Input features (77 for CICIDS2017)")
    model: str = Field(default="rf", description="Model to use (rf, tcn, vae)")
    explain: bool = Field(default=False, description="Include feature importance")


class BatchPredictionRequest(BaseModel):
    """Request model for batch predictions"""
    data: List[List[float]] = Field(..., description="Batch of input features")
    model: str = Field(default="rf", description="Model to use")
    explain: bool = Field(default=False, description="Include explanations")


class TrainingRequest(BaseModel):
    """Request model for training"""
    model_type: str = Field(..., description="Type of model to train")
    epochs: int = Field(default=50, ge=1)
    batch_size: int = Field(default=32, ge=1)
    learning_rate: float = Field(default=0.001, gt=0)


class ExplanationRequest(BaseModel):
    """Request model for explanations"""
    features: List[float] = Field(..., description="Input features")
    model: str = Field(default="rf", description="Model to explain")
    method: str = Field(default="shap", description="Explanation method (shap, lime)")
