"""
Vercel Serverless Function: X-IDS Prediction API
Handles threat detection requests from frontend
"""

import json
import os
import numpy as np
from datetime import datetime

# Add model path
MODEL_DIR = os.path.join(os.path.dirname(__file__), '../models')

# Global model cache (persists across warm invocations)
_model_cache = {}

def load_models():
    """Load all trained models"""
    if _model_cache:
        return _model_cache
    
    try:
        import pickle
        import tensorflow as tf
        
        # Load Random Forest
        rf_path = os.path.join(MODEL_DIR, 'trained_rf_model.pkl')
        if os.path.exists(rf_path):
            with open(rf_path, 'rb') as f:
                _model_cache['rf'] = pickle.load(f)
        
        # Load TCN
        tcn_path = os.path.join(MODEL_DIR, 'trained_tcn_model.h5')
        if os.path.exists(tcn_path):
            _model_cache['tcn'] = tf.keras.models.load_model(tcn_path, compile=False)
        
        # Load VAE
        vae_path = os.path.join(MODEL_DIR, 'trained_vae_model.h5')
        if os.path.exists(vae_path):
            _model_cache['vae'] = tf.keras.models.load_model(vae_path, compile=False)
        
        return _model_cache
    except Exception as e:
        print(f"Error loading models: {e}")
        return {}

def validate_features(features):
    """Validate feature array"""
    if not isinstance(features, (list, tuple)):
        return False, "Features must be array"
    
    if len(features) != 77:
        return False, f"Expected 77 features, got {len(features)}"
    
    try:
        features = [float(f) for f in features]
        if any(f < 0 or f > 1 for f in features):
            return False, "All features must be 0.0-1.0"
        return True, features
    except:
        return False, "Features must be numbers"

def predict_single(features, models):
    """Predict single packet"""
    features_array = np.array(features).reshape(1, -1)
    
    predictions = {}
    confidences = {}
    
    # RF prediction
    if 'rf' in models:
        try:
            pred = models['rf'].predict(features_array)[0]
            prob = max(models['rf'].predict_proba(features_array)[0]) * 100
            predictions['rf'] = int(pred)
            confidences['rf'] = float(prob)
        except:
            pass
    
    # TCN prediction
    if 'tcn' in models:
        try:
            features_reshaped = features_array.reshape(1, 77, 1)
            pred = models['tcn'].predict(features_reshaped, verbose=0)
            pred_class = np.argmax(pred[0])
            confidence = float(max(pred[0]) * 100)
            predictions['tcn'] = int(pred_class)
            confidences['tcn'] = confidence
        except:
            pass
    
    # VAE prediction (anomaly score)
    if 'vae' in models:
        try:
            features_reshaped = features_array.reshape(1, 77)
            reconstructed = models['vae'].predict(features_reshaped, verbose=0)
            mse = np.mean((features_array - reconstructed) ** 2)
            pred_class = min(5, int(mse * 10))
            confidence = max(50, min(100, (1 - mse) * 100))
            predictions['vae'] = pred_class
            confidences['vae'] = float(confidence)
        except:
            pass
    
    return predictions, confidences

def handler(req, resp):
    """Vercel serverless handler"""
    
    # CORS headers
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    resp.headers['Content-Type'] = 'application/json'
    
    # Handle OPTIONS
    if req.method == 'OPTIONS':
        resp.status_code = 204
        return
    
    # Only POST allowed
    if req.method != 'POST':
        resp.status_code = 405
        resp.text = json.dumps({
            'error': 'Method not allowed',
            'allowed': ['POST']
        })
        return
    
    try:
        data = req.json
    except:
        resp.status_code = 400
        resp.text = json.dumps({'error': 'Invalid JSON'})
        return
    
    # Get features
    features = data.get('features')
    if not features:
        resp.status_code = 400
        resp.text = json.dumps({'error': 'Missing features'})
        return
    
    # Validate
    valid, result = validate_features(features)
    if not valid:
        resp.status_code = 400
        resp.text = json.dumps({'error': result})
        return
    
    features = result
    
    # Load models
    models = load_models()
    if not models:
        resp.status_code = 503
        resp.text = json.dumps({
            'error': 'Models not loaded',
            'note': 'Deploy with model files in /api/../models/'
        })
        return
    
    # Predict
    try:
        predictions, confidences = predict_single(features, models)
        
        # Ensemble: Majority vote
        if predictions:
            votes = list(predictions.values())
            from collections import Counter
            vote_counts = Counter(votes)
            final_pred = vote_counts.most_common(1)[0][0]
            avg_confidence = np.mean(list(confidences.values()))
        else:
            final_pred = 0
            avg_confidence = 50.0
        
        response = {
            'prediction': int(final_pred),
            'confidence': float(avg_confidence),
            'models': predictions,
            'confidences': confidences,
            'timestamp': datetime.utcnow().isoformat(),
            'threat_type': [
                'BENIGN', 'PortScan', 'Botnet',
                'Infiltration', 'WebAttack', 'DoS'
            ][final_pred]
        }
        
        resp.status_code = 200
        resp.text = json.dumps(response)
    
    except Exception as e:
        resp.status_code = 500
        resp.text = json.dumps({
            'error': f'Prediction failed: {str(e)}'
        })
