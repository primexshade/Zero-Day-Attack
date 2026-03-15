"""
X-IDS SIEM Integration Server
FastAPI server for SIEM integration and dashboard
"""

import logging
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import json
from typing import Dict, Any
import uvicorn

try:
    from siem_handler import SIEMHandler, AlertRouter
    SIEM_AVAILABLE = True
except ImportError:
    SIEM_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="X-IDS SIEM Integration Server",
    description="SIEM integration for X-IDS threat detection",
    version="1.0.0"
)

# Global SIEM handler
siem_handler = None
alert_router = None


def init_siem(siem_type: str = "both", **config):
    """Initialize SIEM handler"""
    global siem_handler, alert_router
    
    if not SIEM_AVAILABLE:
        logger.warning("SIEM modules not available")
        return
    
    try:
        siem_handler = SIEMHandler(siem_type, **config)
        alert_router = AlertRouter(siem_handler)
        logger.info("SIEM handler initialized")
    except Exception as e:
        logger.error(f"Failed to initialize SIEM handler: {e}")


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    init_siem(
        siem_type="both",
        es_hosts=["localhost:9200"],
        es_prefix="xids",
        hec_url="https://localhost:8088",
        hec_token=""  # Set via environment or config
    )


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "service": "x-ids-siem"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "X-IDS SIEM Integration Server",
        "version": "1.0.0",
        "endpoints": {
            "/health": "Health check",
            "/prediction": "Send prediction",
            "/alert": "Send alert",
            "/stats": "Get statistics",
            "/dashboard": "Interactive dashboard"
        }
    }


@app.post("/prediction")
async def send_prediction(prediction: Dict[str, Any]):
    """Send a prediction to SIEM"""
    if not siem_handler:
        raise HTTPException(status_code=503, detail="SIEM handler not available")
    
    try:
        success = siem_handler.send_prediction(prediction)
        return {
            "status": "sent" if success else "failed",
            "prediction_id": prediction.get("packet_id")
        }
    except Exception as e:
        logger.error(f"Failed to send prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/alert")
async def send_alert(alert: Dict[str, Any]):
    """Send an alert to SIEM"""
    if not siem_handler or not alert_router:
        raise HTTPException(status_code=503, detail="SIEM handler not available")
    
    try:
        alert_router.route_alert(alert)
        return {
            "status": "routed",
            "alert_id": alert.get("packet_id"),
            "severity": alert.get("severity")
        }
    except Exception as e:
        logger.error(f"Failed to route alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/bulk/predictions")
async def bulk_predictions(predictions: Dict[str, Any]):
    """Bulk send predictions"""
    if not siem_handler:
        raise HTTPException(status_code=503, detail="SIEM handler not available")
    
    try:
        preds = predictions.get("predictions", [])
        count = siem_handler.bulk_send_predictions(preds)
        return {"status": "sent", "count": count}
    except Exception as e:
        logger.error(f"Bulk send failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/bulk/alerts")
async def bulk_alerts(alerts: Dict[str, Any]):
    """Bulk send alerts"""
    if not siem_handler:
        raise HTTPException(status_code=503, detail="SIEM handler not available")
    
    try:
        alert_list = alerts.get("alerts", [])
        count = siem_handler.bulk_send_alerts(alert_list)
        return {"status": "sent", "count": count}
    except Exception as e:
        logger.error(f"Bulk send failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_stats(hours: int = 1):
    """Get SIEM statistics"""
    if not siem_handler:
        raise HTTPException(status_code=503, detail="SIEM handler not available")
    
    try:
        stats = siem_handler.get_dashboard_stats(hours)
        return stats
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/dashboard")
async def dashboard():
    """Interactive SIEM dashboard"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>X-IDS SIEM Dashboard</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: Arial, sans-serif; background: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
            .header { background: #2c3e50; color: white; padding: 20px; border-radius: 5px; margin-bottom: 20px; }
            .header h1 { margin: 0; }
            
            .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
            .card { background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .metric { margin: 10px 0; }
            .metric-label { font-size: 12px; color: #7f8c8d; text-transform: uppercase; }
            .metric-value { font-size: 28px; font-weight: bold; color: #2c3e50; }
            
            .alert { background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 10px 0; border-radius: 3px; }
            .alert.critical { background: #f8d7da; border-left-color: #dc3545; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔒 X-IDS SIEM Dashboard</h1>
                <p>Real-time threat detection and SIEM integration</p>
            </div>
            
            <div class="grid">
                <div class="card">
                    <div class="metric">
                        <div class="metric-label">Total Predictions (1h)</div>
                        <div class="metric-value" id="total-pred">-</div>
                    </div>
                </div>
                
                <div class="card">
                    <div class="metric">
                        <div class="metric-label">Alerts Detected (1h)</div>
                        <div class="metric-value" id="total-alerts">-</div>
                    </div>
                </div>
                
                <div class="card">
                    <div class="metric">
                        <div class="metric-label">Alert Rate</div>
                        <div class="metric-value" id="alert-rate">-</div>
                    </div>
                </div>
            </div>
            
            <div class="card" style="margin-top: 20px;">
                <h3>Instructions</h3>
                <p>1. Configure your SIEM system (Elasticsearch/Splunk)</p>
                <p>2. Send predictions: POST /prediction</p>
                <p>3. Send alerts: POST /alert</p>
                <p>4. View stats: GET /stats</p>
            </div>
        </div>
        
        <script>
            // Load stats
            fetch('/stats')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('total-pred').textContent = data.total_predictions || '-';
                    document.getElementById('total-alerts').textContent = data.total_alerts || '-';
                    document.getElementById('alert-rate').textContent = (data.alert_rate_percent || 0).toFixed(1) + '%';
                })
                .catch(e => console.error('Failed to load stats:', e));
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


def main():
    """Run SIEM integration server"""
    import argparse
    
    parser = argparse.ArgumentParser(description="X-IDS SIEM Integration Server")
    parser.add_argument("--port", type=int, default=8003, help="Server port")
    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    parser.add_argument("--siem-type", default="both", help="SIEM type (elasticsearch, splunk, both)")
    
    args = parser.parse_args()
    
    logger.info(f"Starting X-IDS SIEM Integration Server on {args.host}:{args.port}")
    logger.info(f"Dashboard: http://localhost:{args.port}/dashboard")
    
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
