"""
Vercel Serverless Function: Batch Prediction Endpoint
Handles multiple packets
"""

import json
import os
import numpy as np
from datetime import datetime
from predict import load_models, validate_features, predict_single

def handler(request):
    """Batch prediction handler"""
    
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
    }
    
    if request.method == 'OPTIONS':
        return ('', 204, headers)
    
    if request.method != 'POST':
        return (json.dumps({'error': 'Method not allowed'}), 405, headers)
    
    try:
        data = json.loads(request.get_data(as_text=True))
    except:
        return (json.dumps({'error': 'Invalid JSON'}), 400, headers)
    
    features_list = data.get('features_list', [])
    if not features_list:
        return (json.dumps({'error': 'Missing features_list'}), 400, headers)
    
    if not isinstance(features_list, list):
        return (json.dumps({'error': 'features_list must be array'}), 400, headers)
    
    # Load models
    models = load_models()
    if not models:
        return (json.dumps({'error': 'Models not loaded'}), 503, headers)
    
    results = []
    errors = []
    
    for idx, features in enumerate(features_list):
        valid, result = validate_features(features)
        if not valid:
            errors.append({
                'packet': idx,
                'error': result
            })
            continue
        
        features = result
        
        try:
            predictions, confidences = predict_single(features, models)
            
            if predictions:
                votes = list(predictions.values())
                from collections import Counter
                vote_counts = Counter(votes)
                final_pred = vote_counts.most_common(1)[0][0]
                avg_confidence = np.mean(list(confidences.values()))
            else:
                final_pred = 0
                avg_confidence = 50.0
            
            results.append({
                'packet': idx,
                'prediction': int(final_pred),
                'confidence': float(avg_confidence),
                'threat_type': [
                    'BENIGN', 'PortScan', 'Botnet',
                    'Infiltration', 'WebAttack', 'DoS'
                ][final_pred]
            })
        except Exception as e:
            errors.append({
                'packet': idx,
                'error': f'Prediction failed: {str(e)}'
            })
    
    response = {
        'total': len(features_list),
        'processed': len(results),
        'errors': len(errors),
        'results': results,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if errors:
        response['error_details'] = errors
    
    return (json.dumps(response), 200, headers)
