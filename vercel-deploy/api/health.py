"""
Health check endpoint
"""

import json
import os
from predict import load_models
from datetime import datetime

def handler(request):
    """Health check"""
    
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
    }
    
    models = load_models()
    models_loaded = list(models.keys())
    
    response = {
        'status': 'healthy' if models_loaded else 'degraded',
        'models_loaded': models_loaded,
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    }
    
    return (json.dumps(response), 200, headers)
