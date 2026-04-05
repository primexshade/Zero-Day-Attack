"""
X-IDS Web Dashboard Backend
FastAPI server with WebSocket support for real-time alerts and metrics
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from fastapi import FastAPI, WebSocket, HTTPException, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict
import numpy as np
from fastapi.encoders import jsonable_encoder

logger = logging.getLogger(__name__)

# Models
class Alert(BaseModel):
    id: str
    timestamp: datetime
    source_ip: str
    destination_ip: str
    protocol: str
    confidence: float
    severity: str  # low, medium, high, critical
    alert_type: str
    description: str
    explanation: Optional[Dict] = None
    

class ModelMetrics(BaseModel):
    timestamp: datetime
    f1_score: float
    precision: float
    recall: float
    roc_auc: float
    inference_time_ms: float
    

class SystemMetrics(BaseModel):
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    alerts_per_minute: float
    prediction_latency_ms: float
    throughput_rps: float


class DashboardStats(BaseModel):
    total_alerts: int
    critical_alerts: int
    high_alerts: int
    medium_alerts: int
    low_alerts: int
    alerts_today: int
    avg_confidence: float
    model_f1_score: float
    uptime_hours: float


# Connection Manager for WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast message: {e}")
    
    async def send_personal(self, websocket: WebSocket, message: dict):
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")


# Initialize FastAPI app
app = FastAPI(
    title="X-IDS Dashboard",
    description="Web dashboard for X-IDS alert management and monitoring",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Connection manager
manager = ConnectionManager()

# In-memory storage (replace with database in production)
alerts_store: List[Alert] = []
metrics_store: List[ModelMetrics] = []
system_metrics_store: List[SystemMetrics] = []

# Startup event
@app.on_event("startup")
async def startup():
    """Initialize dashboard on startup"""
    logger.info("X-IDS Dashboard starting up...")


# REST Endpoints

@app.get("/health")
async def health_check() -> Dict:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.get("/api/stats")
async def get_dashboard_stats() -> DashboardStats:
    """Get dashboard summary statistics"""
    now = datetime.utcnow()
    today = now.date()
    
    # Calculate statistics
    total_alerts = len(alerts_store)
    critical_alerts = len([a for a in alerts_store if a.severity == "critical"])
    high_alerts = len([a for a in alerts_store if a.severity == "high"])
    medium_alerts = len([a for a in alerts_store if a.severity == "medium"])
    low_alerts = len([a for a in alerts_store if a.severity == "low"])
    
    alerts_today = len([a for a in alerts_store if a.timestamp.date() == today])
    
    avg_confidence = np.mean([a.confidence for a in alerts_store]) if alerts_store else 0.0
    
    # Get latest model metrics
    model_f1 = metrics_store[-1].f1_score if metrics_store else 0.0
    
    return DashboardStats(
        total_alerts=total_alerts,
        critical_alerts=critical_alerts,
        high_alerts=high_alerts,
        medium_alerts=medium_alerts,
        low_alerts=low_alerts,
        alerts_today=alerts_today,
        avg_confidence=float(avg_confidence),
        model_f1_score=model_f1,
        uptime_hours=24.0  # Placeholder
    )


@app.get("/api/alerts")
async def get_alerts(
    severity: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Alert]:
    """
    Get alerts with optional filtering
    
    Args:
        severity: Filter by severity (low, medium, high, critical)
        limit: Number of alerts to return
        offset: Offset for pagination
        
    Returns:
        List of alerts
    """
    filtered = alerts_store
    
    if severity:
        filtered = [a for a in filtered if a.severity == severity]
    
    # Sort by timestamp descending
    filtered = sorted(filtered, key=lambda x: x.timestamp, reverse=True)
    
    return filtered[offset:offset + limit]


@app.get("/api/alerts/{alert_id}")
async def get_alert(alert_id: str) -> Alert:
    """Get specific alert by ID"""
    for alert in alerts_store:
        if alert.id == alert_id:
            return alert
    raise HTTPException(status_code=404, detail=f"Alert {alert_id} not found")


@app.post("/api/alerts")
async def create_alert(alert: Alert) -> Alert:
    """Create new alert"""
    alerts_store.append(alert)
    
    # Broadcast to WebSocket clients
    await manager.broadcast({
        "type": "new_alert",
        "alert": jsonable_encoder(alert)
    })
    
    return alert


@app.get("/api/metrics")
async def get_metrics(
    hours: int = 24,
    limit: int = 100
) -> List[ModelMetrics]:
    """Get model metrics for the last N hours"""
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    filtered = [m for m in metrics_store if m.timestamp >= cutoff]
    return sorted(filtered, key=lambda x: x.timestamp, reverse=True)[:limit]


@app.post("/api/metrics")
async def record_metrics(metrics: ModelMetrics) -> ModelMetrics:
    """Record model metrics"""
    metrics_store.append(metrics)
    
    # Keep only last 1000 metrics
    if len(metrics_store) > 1000:
        metrics_store.pop(0)
    
    # Broadcast to WebSocket clients
    await manager.broadcast({
        "type": "metrics_update",
        "metrics": jsonable_encoder(metrics)
    })
    
    return metrics


@app.get("/api/system-metrics")
async def get_system_metrics(hours: int = 1) -> List[SystemMetrics]:
    """Get system metrics for the last N hours"""
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    filtered = [m for m in system_metrics_store if m.timestamp >= cutoff]
    return sorted(filtered, key=lambda x: x.timestamp)


@app.post("/api/system-metrics")
async def record_system_metrics(metrics: SystemMetrics) -> SystemMetrics:
    """Record system metrics"""
    system_metrics_store.append(metrics)
    
    # Keep only last 500 metrics
    if len(system_metrics_store) > 500:
        system_metrics_store.pop(0)
    
    return metrics


# WebSocket Endpoints

@app.websocket("/ws/alerts")
async def websocket_alerts(websocket: WebSocket):
    """WebSocket endpoint for real-time alerts"""
    await manager.connect(websocket)
    try:
        while True:
            # Wait for any message
            data = await websocket.receive_text()
            
            # Echo back or handle commands
            if data == "get_stats":
                stats = await get_dashboard_stats()
                await manager.send_personal(websocket, {
                    "type": "stats",
                    "data": jsonable_encoder(stats)
                })
     
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected from alerts WebSocket")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


@app.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket):
    """WebSocket endpoint for real-time metrics"""
    await manager.connect(websocket)
    try:
        while True:
            # Send metrics every 5 seconds
            await asyncio.sleep(5)
            
            if metrics_store:
                latest = metrics_store[-1]
                await manager.send_personal(websocket, {
                    "type": "metrics",
                    "data": jsonable_encoder(latest)
                })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("Client disconnected from metrics WebSocket")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# Configuration Endpoints

@app.get("/api/config")
async def get_config() -> Dict:
    """Get dashboard configuration"""
    return {
        "alert_severities": ["low", "medium", "high", "critical"],
        "alert_types": ["intrusion", "anomaly", "port_scan", "ddos", "malware"],
        "refresh_interval_ms": 5000,
        "max_alerts_display": 1000,
        "charts": {
            "alert_timeline": True,
            "severity_distribution": True,
            "model_performance": True,
            "system_resources": True
        }
    }


@app.post("/api/config")
async def update_config(config: Dict) -> Dict:
    """Update dashboard configuration"""
    logger.info(f"Dashboard configuration updated: {config}")
    return {"status": "ok", "config": config}


# Root endpoint
@app.get("/")
async def root() -> Dict:
    """Root endpoint"""
    return {
        "name": "X-IDS Dashboard API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "running"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
