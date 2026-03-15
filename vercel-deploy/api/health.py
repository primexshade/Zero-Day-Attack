"""
Vercel Serverless Function: Health Check Endpoint
"""

import json
from datetime import datetime
from predict import load_models

def handler(req, resp):
    """Health check"""
    
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Content-Type'] = 'application/json'
    
    models = load_models()
    models_loaded = list(models.keys())
    
    response = {
        'status': 'healthy' if models_loaded else 'degraded',
        'models_loaded': models_loaded,
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    }
    
    resp.status_code = 200
    resp.text = json.dumps(response)
