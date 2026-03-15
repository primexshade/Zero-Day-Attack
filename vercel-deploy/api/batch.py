"""
Vercel Serverless Function: Batch Prediction Endpoint
Handles multiple packets
"""

import json
import os
import numpy as np
from datetime import datetime
from predict import load_models, validate_features, predict_single

def handler(req, resp):
    """Batch prediction handler"""
    
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    resp.headers['Content-Type'] = 'application/json'
    
    if req.method == 'OPTIONS':
        resp.status_code = 204
        return
    
    if req.method != 'POST':
        resp.status_code = 405
        resp.text = json.dumps({'error': 'Method not allowed'})
        return
    
    try:
        data = req.json
    except:
        resp.status_code = 400
        resp.text = json.dumps({'error': 'Invalid JSON'})
        return
    
    features_list = data.get('features_list', [])
    if not features_list:
        resp.status_code = 400
        resp.text = json.dumps({'error': 'Missing features_list'})
        return
    
    if not isinstance(features_list, list):
        resp.status_code = 400
        resp.text = json.dumps({'error': 'features_list must be array'})
        return
    
    # Load models
    models = load_models()
    if not models:
        resp.status_code = 503
        resp.text = json.dumps({'error': 'Models not loaded'})
        return
    
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
    
    resp.status_code = 200
    resp.text = json.dumps(response)
