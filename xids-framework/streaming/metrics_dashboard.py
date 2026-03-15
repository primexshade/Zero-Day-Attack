"""
X-IDS Metrics Dashboard
Real-time monitoring for Kafka streaming pipeline
"""

import json
from datetime import datetime, timedelta
from collections import deque
from typing import Dict, List, Any
import statistics


class MetricsCollector:
    """Collect and aggregate streaming metrics"""
    
    def __init__(self, window_size: int = 100):
        """
        Initialize metrics collector
        
        Args:
            window_size: Size of rolling window for aggregates
        """
        self.window_size = window_size
        
        # Latency tracking
        self.latencies = deque(maxlen=window_size)
        self.inference_times = deque(maxlen=window_size)
        
        # Throughput tracking
        self.packets_per_batch = deque(maxlen=window_size)
        self.batches_processed = 0
        
        # Detection tracking
        self.predictions = []
        self.alert_count = 0
        self.benign_count = 0
        
        # Timing
        self.start_time = datetime.utcnow()
        self.last_reset = datetime.utcnow()
    
    def record_latency(self, latency_ms: float):
        """Record end-to-end latency"""
        self.latencies.append(latency_ms)
    
    def record_inference(self, inference_time_ms: float):
        """Record inference time"""
        self.inference_times.append(inference_time_ms)
    
    def record_batch(self, batch_size: int, num_alerts: int):
        """Record batch processing"""
        self.packets_per_batch.append(batch_size)
        self.batches_processed += 1
        self.alert_count += num_alerts
        self.benign_count += (batch_size - num_alerts)
    
    def record_prediction(self, prediction: int):
        """Record prediction result"""
        self.predictions.append(prediction)
    
    def reset(self):
        """Reset metrics for new window"""
        self.latencies.clear()
        self.inference_times.clear()
        self.alert_count = 0
        self.benign_count = 0
        self.last_reset = datetime.utcnow()
    
    def get_summary(self) -> Dict[str, Any]:
        """Get current metrics summary"""
        elapsed = (datetime.utcnow() - self.start_time).total_seconds()
        window_elapsed = (datetime.utcnow() - self.last_reset).total_seconds()
        
        total_packets = self.alert_count + self.benign_count
        alert_rate = (self.alert_count / total_packets * 100) if total_packets > 0 else 0
        
        # Latency stats
        if self.latencies:
            avg_latency = statistics.mean(self.latencies)
            p95_latency = self._percentile(list(self.latencies), 95)
            p99_latency = self._percentile(list(self.latencies), 99)
        else:
            avg_latency = p95_latency = p99_latency = 0
        
        # Throughput
        throughput_pps = total_packets / elapsed if elapsed > 0 else 0
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'uptime_seconds': elapsed,
            'window_elapsed_seconds': window_elapsed,
            'batches_processed': self.batches_processed,
            'total_packets': total_packets,
            'alerts': self.alert_count,
            'benign': self.benign_count,
            'alert_rate_percent': alert_rate,
            'throughput_pps': throughput_pps,
            'latency': {
                'avg_ms': avg_latency,
                'p95_ms': p95_latency,
                'p99_ms': p99_latency,
            },
            'inference_time': {
                'avg_ms': statistics.mean(self.inference_times) if self.inference_times else 0,
            }
        }
    
    def get_alerts_distribution(self) -> Dict[str, int]:
        """Get distribution of predictions"""
        if not self.predictions:
            return {}
        
        distribution = {}
        for pred in self.predictions:
            distribution[str(pred)] = distribution.get(str(pred), 0) + 1
        
        return distribution
    
    @staticmethod
    def _percentile(data: List[float], percentile: int) -> float:
        """Calculate percentile"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]


class MetricsDashboard:
    """Web-ready metrics dashboard"""
    
    def __init__(self, collector: MetricsCollector):
        self.collector = collector
    
    def to_json(self) -> str:
        """Export metrics as JSON"""
        return json.dumps(self.collector.get_summary(), indent=2)
    
    def to_text(self) -> str:
        """Export metrics as formatted text"""
        summary = self.collector.get_summary()
        
        lines = [
            "=" * 70,
            "X-IDS METRICS DASHBOARD",
            "=" * 70,
            f"Timestamp: {summary['timestamp']}",
            f"Uptime: {summary['uptime_seconds']:.1f} seconds",
            f"",
            f"THROUGHPUT:",
            f"  Total Packets: {summary['total_packets']}",
            f"  Throughput: {summary['throughput_pps']:.1f} pps",
            f"  Batches: {summary['batches_processed']}",
            f"",
            f"DETECTIONS:",
            f"  Alerts: {summary['alerts']}",
            f"  Benign: {summary['benign']}",
            f"  Alert Rate: {summary['alert_rate_percent']:.1f}%",
            f"",
            f"LATENCY:",
            f"  Average: {summary['latency']['avg_ms']:.2f} ms",
            f"  P95: {summary['latency']['p95_ms']:.2f} ms",
            f"  P99: {summary['latency']['p99_ms']:.2f} ms",
            f"",
            f"INFERENCE TIME:",
            f"  Average: {summary['inference_time']['avg_ms']:.2f} ms",
            "=" * 70,
        ]
        
        return "\n".join(lines)
    
    def to_html(self) -> str:
        """Export metrics as HTML"""
        summary = self.collector.get_summary()
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>X-IDS Metrics Dashboard</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
        .metrics {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px; }}
        .metric-box {{ background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .metric-title {{ font-size: 14px; font-weight: bold; color: #2c3e50; }}
        .metric-value {{ font-size: 32px; font-weight: bold; color: #27ae60; margin-top: 10px; }}
        .metric-unit {{ font-size: 12px; color: #7f8c8d; }}
        .alert-rate {{ color: #e74c3c; }}
        .timestamp {{ font-size: 12px; color: #95a5a6; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔒 X-IDS Metrics Dashboard</h1>
            <p>Real-time monitoring for Kafka streaming detection</p>
        </div>
        
        <div class="metrics">
            <div class="metric-box">
                <div class="metric-title">Throughput (packets/sec)</div>
                <div class="metric-value">{summary['throughput_pps']:.1f}</div>
                <div class="metric-unit">pps</div>
            </div>
            
            <div class="metric-box">
                <div class="metric-title">Total Packets Processed</div>
                <div class="metric-value">{summary['total_packets']}</div>
                <div class="metric-unit">packets</div>
            </div>
            
            <div class="metric-box">
                <div class="metric-title alert-rate">Alert Rate</div>
                <div class="metric-value alert-rate">{summary['alert_rate_percent']:.1f}%</div>
                <div class="metric-unit">{summary['alerts']} alerts</div>
            </div>
            
            <div class="metric-box">
                <div class="metric-title">Average Latency</div>
                <div class="metric-value">{summary['latency']['avg_ms']:.2f}</div>
                <div class="metric-unit">milliseconds</div>
            </div>
        </div>
        
        <div class="timestamp">
            Last updated: {summary['timestamp']}
        </div>
    </div>
</body>
</html>
"""
        return html


# Example usage
if __name__ == '__main__':
    collector = MetricsCollector()
    
    # Simulate some metrics
    for i in range(100):
        collector.record_batch(100, 10)
        collector.record_latency(27.1 + (i % 5))
        collector.record_inference(13.71)
    
    dashboard = MetricsDashboard(collector)
    print(dashboard.to_text())
