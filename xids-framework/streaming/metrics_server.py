"""
X-IDS Metrics Server - Real-time monitoring API

FastAPI server that provides:
- JSON metrics endpoint
- HTML dashboard
- WebSocket for live updates
"""

from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import asyncio
import json
import logging
from datetime import datetime
import uvicorn

try:
    from metrics_dashboard import MetricsCollector, MetricsDashboard
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    print("⚠️  Run from xids-framework/streaming directory")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global metrics collector
metrics_collector = MetricsCollector() if METRICS_AVAILABLE else None

app = FastAPI(
    title="X-IDS Metrics Server",
    description="Real-time streaming metrics for X-IDS",
    version="1.0.0"
)


@app.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "service": "x-ids-metrics"}


@app.get("/metrics")
async def get_metrics():
    """Get current metrics as JSON"""
    if not metrics_collector:
        return {"error": "Metrics not available"}
    
    return metrics_collector.get_summary()


@app.get("/metrics/html")
async def get_metrics_html():
    """Get HTML dashboard"""
    if not metrics_collector:
        return {"error": "Metrics not available"}
    
    dashboard = MetricsDashboard(metrics_collector)
    return HTMLResponse(content=dashboard.to_html())


@app.get("/metrics/text")
async def get_metrics_text():
    """Get text-formatted metrics"""
    if not metrics_collector:
        return {"error": "Metrics not available"}
    
    dashboard = MetricsDashboard(metrics_collector)
    return {"text": dashboard.to_text()}


@app.post("/metrics/record")
async def record_metrics(event: dict):
    """Record a metric event
    
    Example payload:
    {
        "type": "batch",
        "batch_size": 100,
        "num_alerts": 10,
        "latency_ms": 27.1,
        "inference_time_ms": 13.71
    }
    """
    if not metrics_collector:
        return {"error": "Metrics not available"}
    
    event_type = event.get("type")
    
    if event_type == "batch":
        metrics_collector.record_batch(
            event.get("batch_size", 0),
            event.get("num_alerts", 0)
        )
    elif event_type == "latency":
        metrics_collector.record_latency(event.get("latency_ms", 0))
    elif event_type == "inference":
        metrics_collector.record_inference(event.get("inference_time_ms", 0))
    
    return {"status": "recorded"}


@app.post("/metrics/reset")
async def reset_metrics():
    """Reset metrics"""
    if not metrics_collector:
        return {"error": "Metrics not available"}
    
    metrics_collector.reset()
    return {"status": "reset"}


@app.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket):
    """WebSocket endpoint for live metrics"""
    if not metrics_collector:
        await websocket.close(code=1000, reason="Metrics not available")
        return
    
    await websocket.accept()
    
    try:
        while True:
            # Send metrics every 5 seconds
            summary = metrics_collector.get_summary()
            await websocket.send_json(summary)
            await asyncio.sleep(5)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()


@app.get("/dashboard")
async def dashboard():
    """Main dashboard HTML"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>X-IDS Streaming Metrics</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js@3.9.1/dist/chart.min.js"></script>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #e2e8f0; }}
            .container {{ max-width: 1400px; margin: 0 auto; padding: 20px; }}
            .header {{ text-align: center; margin-bottom: 40px; border-bottom: 2px solid #1e293b; padding-bottom: 20px; }}
            .header h1 {{ font-size: 2.5em; color: #60a5fa; margin-bottom: 5px; }}
            .header p {{ color: #94a3b8; font-size: 1.1em; }}
            
            .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 40px; }}
            .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 20px; }}
            .card:hover {{ border-color: #60a5fa; box-shadow: 0 0 20px rgba(96, 165, 250, 0.2); }}
            
            .metric {{ margin-bottom: 15px; }}
            .metric-label {{ font-size: 0.9em; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; }}
            .metric-value {{ font-size: 2em; font-weight: bold; color: #60a5fa; margin-top: 5px; }}
            .metric-unit {{ font-size: 0.8em; color: #64748b; }}
            
            .alert {{ color: #f87171; }}
            .success {{ color: #34d399; }}
            .warning {{ color: #fbbf24; }}
            
            .chart-container {{ position: relative; height: 300px; margin-top: 20px; }}
            .row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
            
            @media (max-width: 768px) {{
                .row {{ grid-template-columns: 1fr; }}
                .header h1 {{ font-size: 1.8em; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔒 X-IDS Streaming Dashboard</h1>
                <p>Real-time detection metrics and performance monitoring</p>
                <p id="timestamp" style="margin-top: 10px; font-size: 0.9em;"></p>
            </div>
            
            <div class="grid">
                <div class="card">
                    <div class="metric">
                        <div class="metric-label">Throughput</div>
                        <div class="metric-value"><span id="throughput">0</span></div>
                        <div class="metric-unit">packets/second</div>
                    </div>
                </div>
                
                <div class="card">
                    <div class="metric">
                        <div class="metric-label">Total Packets</div>
                        <div class="metric-value"><span id="total-packets">0</span></div>
                        <div class="metric-unit">processed</div>
                    </div>
                </div>
                
                <div class="card">
                    <div class="metric">
                        <div class="metric-label alert">Alert Rate</div>
                        <div class="metric-value alert"><span id="alert-rate">0</span>%</div>
                        <div class="metric-unit">(<span id="alert-count">0</span> alerts)</div>
                    </div>
                </div>
                
                <div class="card">
                    <div class="metric">
                        <div class="metric-label">Average Latency</div>
                        <div class="metric-value success"><span id="latency">0</span></div>
                        <div class="metric-unit">milliseconds</div>
                    </div>
                </div>
            </div>
            
            <div class="row">
                <div class="card">
                    <h3>Latency Distribution</h3>
                    <div class="chart-container">
                        <canvas id="latency-chart"></canvas>
                    </div>
                </div>
                
                <div class="card">
                    <h3>Alerts vs Benign</h3>
                    <div class="chart-container">
                        <canvas id="detection-chart"></canvas>
                    </div>
                </div>
            </div>
        </div>
        
        <script>
            // Connect WebSocket
            const ws = new WebSocket('ws://localhost:8002/ws/metrics');
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                updateDashboard(data);
            };
            
            function updateDashboard(data) {
                // Update metrics
                document.getElementById('throughput').textContent = data.throughput_pps.toFixed(1);
                document.getElementById('total-packets').textContent = data.total_packets;
                document.getElementById('alert-rate').textContent = data.alert_rate_percent.toFixed(1);
                document.getElementById('alert-count').textContent = data.alerts;
                document.getElementById('latency').textContent = data.latency.avg_ms.toFixed(2);
                document.getElementById('timestamp').textContent = 'Last updated: ' + new Date().toLocaleTimeString();
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "X-IDS Metrics Server",
        "version": "1.0.0",
        "endpoints": {
            "/health": "Health check",
            "/metrics": "Current metrics (JSON)",
            "/metrics/html": "HTML dashboard",
            "/metrics/text": "Text-formatted metrics",
            "/dashboard": "Interactive dashboard",
            "/ws/metrics": "WebSocket live metrics"
        }
    }


def main():
    """Run metrics server"""
    import argparse
    
    parser = argparse.ArgumentParser(description="X-IDS Metrics Server")
    parser.add_argument("--port", type=int, default=8002, help="Server port")
    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    
    args = parser.parse_args()
    
    logger.info(f"Starting X-IDS Metrics Server on {args.host}:{args.port}")
    logger.info(f"Dashboard: http://localhost:{args.port}/dashboard")
    
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        log_level="info"
    )


if __name__ == "__main__":
    main()
