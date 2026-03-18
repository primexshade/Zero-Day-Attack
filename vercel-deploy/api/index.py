"""Vercel API - Simple WSGI app using Werkzeug"""
import json
import os
import numpy as np
from datetime import datetime

class Request:
    def __init__(self, environ):
        self.environ = environ
        self.method = environ.get('REQUEST_METHOD', 'GET')
        self.path = environ.get('PATH_INFO', '/')
        self.url = environ.get('REQUEST_URI', '')
        try:
            content_length = int(environ.get('CONTENT_LENGTH', 0))
            if content_length > 0:
                import wsgiref.util
                self.body = environ['wsgi.input'].read(content_length)
                self.json = json.loads(self.body.decode())
            else:
                self.json = {}
        except:
            self.json = {}

class Response:
    def __init__(self):
        self.status_code = 200
        self.text = ''
        self.headers = {'Content-Type': 'application/json'}

def app(environ, start_response):
    """WSGI application"""
    req = Request(environ)
    resp = Response()
    
    resp.headers['Access-Control-Allow-Origin'] = '*'
    resp.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    
    if req.method == 'OPTIONS':
        status = '204 No Content'
        start_response(status, [(k, v) for k, v in resp.headers.items()])
        return [b'']
    
    try:
        # Route based on path
        if 'health' in req.path or req.path == '/api':
            handle_health(resp)
        elif 'predict' in req.path:
            handle_predict(req, resp)
        else:
            handle_root(resp)
    except Exception as e:
        resp.status_code = 500
        resp.text = json.dumps({'error': str(e)})
    
    status = f'{resp.status_code} OK'
    response_headers = [(k, v) for k, v in resp.headers.items()]
    start_response(status, response_headers)
    
    body = resp.text if isinstance(resp.text, bytes) else resp.text.encode()
    return [body]

def handle_health(resp):
    """Health check endpoint"""
    response = {
        'status': 'healthy',
        'version': '1.0.0',
        'model': 'random_forest',
        'timestamp': datetime.utcnow().isoformat()
    }
    resp.status_code = 200
    resp.text = json.dumps(response)

def handle_predict(req, resp):
    """Prediction endpoint"""
    if req.method != 'POST':
        resp.status_code = 405
        resp.text = json.dumps({'error': 'Method not allowed'})
        return
    
    data = req.json
    features = data.get('features', [])
    
    if not features or len(features) != 77:
        resp.status_code = 400
        resp.text = json.dumps({'error': 'Expected 77 features'})
        return
    
    try:
        features = [float(f) for f in features]
        if any(f < 0 or f > 1 for f in features):
            raise ValueError('Features out of range')
    except:
        resp.status_code = 400
        resp.text = json.dumps({'error': 'Invalid features'})
        return
    
    try:
        import pickle
        MODEL_PATH = os.path.join(os.path.dirname(__file__), '../models/trained_rf_model.pkl')
        
        with open(MODEL_PATH, 'rb') as f:
            model = pickle.load(f)
        
        X = np.array(features).reshape(1, -1)
        pred = int(model.predict(X)[0])
        conf = float(max(model.predict_proba(X)[0]) * 100)
        
        threat_types = ['BENIGN', 'PortScan', 'Botnet', 'Infiltration', 'WebAttack', 'DoS']
        
        response = {
            'prediction': pred,
            'confidence': conf,
            'threat_type': threat_types[pred] if pred < len(threat_types) else 'UNKNOWN',
            'timestamp': datetime.utcnow().isoformat(),
            'model': 'random_forest'
        }
        
        resp.status_code = 200
        resp.text = json.dumps(response)
    
    except Exception as e:
        resp.status_code = 500
        resp.text = json.dumps({'error': f'Error: {str(e)}'})

def handle_root(resp):
    """Root endpoint"""
    response = {
        'name': 'X-IDS API',
        'version': '1.0.0',
        'endpoints': {
            'GET /api/health': 'Health check',
            'POST /api/predict': 'Threat prediction'
        }
    }
    resp.status_code = 200
    resp.text = json.dumps(response)
