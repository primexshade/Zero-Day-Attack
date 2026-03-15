"""
X-IDS Advanced Ensemble Voting API
Separate endpoints for advanced ensemble functionality
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict
import numpy as np
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from ensemble_handler import AdvancedEnsemble, create_ensemble_response

app = FastAPI(title="X-IDS Advanced Ensemble API", version="1.0.0")


class EnsembleRequest(BaseModel):
    """Request model for ensemble prediction"""
    rf_prediction: float = Field(..., description="Random Forest prediction")
    rf_confidence: float = Field(..., description="RF confidence")
    tcn_prediction: float = Field(..., description="TCN prediction")
    tcn_confidence: float = Field(..., description="TCN confidence")
    vae_prediction: float = Field(..., description="VAE prediction")
    vae_confidence: float = Field(..., description="VAE confidence")
    strategy: str = Field(default="weighted", description="voting strategy: majority, weighted, soft")


@app.get("/strategies")
async def get_strategies():
    """Get available voting strategies"""
    return {
        "available_strategies": {
            "majority": {
                "description": "Simple majority voting (2+ votes wins)",
                "use_case": "Need clear consensus",
                "latency_impact": "minimal"
            },
            "weighted": {
                "description": "Accuracy-weighted voting (RF:35%, TCN:35%, VAE:30%)",
                "use_case": "Best balance (RECOMMENDED)",
                "latency_impact": "minimal"
            },
            "soft": {
                "description": "Probability-based soft voting",
                "use_case": "Need probabilistic scores",
                "latency_impact": "minimal"
            }
        }
    }


@app.post("/predict")
async def ensemble_predict(request: EnsembleRequest):
    """Make ensemble prediction with specified strategy"""
    try:
        predictions = {
            'rf': request.rf_prediction,
            'tcn': request.tcn_prediction,
            'vae': request.vae_prediction
        }
        confidences = {
            'rf': request.rf_confidence,
            'tcn': request.tcn_confidence,
            'vae': request.vae_confidence
        }
        
        ensemble = AdvancedEnsemble()
        result = ensemble.predict(predictions, strategy=request.strategy, confidences=confidences)
        
        return {
            'status': 'success',
            'result': result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/compare")
async def compare_strategies(request: EnsembleRequest):
    """Compare all strategies with same input"""
    try:
        predictions = {
            'rf': request.rf_prediction,
            'tcn': request.tcn_prediction,
            'vae': request.vae_prediction
        }
        confidences = {
            'rf': request.rf_confidence,
            'tcn': request.tcn_confidence,
            'vae': request.vae_confidence
        }
        
        ensemble = AdvancedEnsemble()
        
        majority = ensemble.majority_vote(predictions)
        weighted = ensemble.weighted_vote(predictions, confidences)
        soft = ensemble.soft_vote(predictions)
        
        return {
            'model_predictions': predictions,
            'model_confidences': confidences,
            'strategies': {
                'majority': majority,
                'weighted': weighted,
                'soft': soft
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/info")
async def ensemble_info():
    """Get ensemble configuration info"""
    return {
        'name': 'X-IDS Advanced Ensemble',
        'models': {
            'rf': {'weight': 0.35, 'type': 'Random Forest', 'latency_ms': 13.71},
            'tcn': {'weight': 0.35, 'type': 'Temporal CNN', 'latency_ms': 18.08},
            'vae': {'weight': 0.30, 'type': 'Variational AE', 'latency_ms': 17.66}
        },
        'strategies': 3,
        'expected_latency_ms': 35,
        'accuracy': 0.9191
    }


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8001)
