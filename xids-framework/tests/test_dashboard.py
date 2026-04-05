import json
"""
Tests for X-IDS Dashboard Backend
Tests REST APIs, WebSocket connections, and real-time features
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import sys
sys.path.insert(0, '/Users/aryantiwari/Documents/Zero_Day_Attack/xids-framework')

from dashboard.backend import (
    app, Alert, ModelMetrics, SystemMetrics, 
    alerts_store, metrics_store, system_metrics_store
)


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def sample_alert():
    """Create sample alert"""
    return Alert(
        id="alert_001",
        timestamp=datetime.utcnow(),
        source_ip="192.168.1.100",
        destination_ip="192.168.1.1",
        protocol="TCP",
        confidence=0.95,
        severity="high",
        alert_type="intrusion",
        description="Possible intrusion detected",
        explanation={"feature_importance": {"bytes_transferred": 0.8}}
    )


@pytest.fixture
def sample_metrics():
    """Create sample metrics"""
    return ModelMetrics(
        timestamp=datetime.utcnow(),
        f1_score=0.92,
        precision=0.94,
        recall=0.90,
        roc_auc=0.96,
        inference_time_ms=28.5
    )


@pytest.fixture
def sample_system_metrics():
    """Create sample system metrics"""
    return SystemMetrics(
        timestamp=datetime.utcnow(),
        cpu_percent=45.2,
        memory_percent=62.1,
        alerts_per_minute=12.5,
        prediction_latency_ms=28.5,
        throughput_rps=456
    )


class TestDashboardHealth:
    """Health check tests"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["version"] == "1.0.0"
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert data["status"] == "running"


class TestAlertOperations:
    """Alert CRUD operations"""
    
    def setup_method(self):
        """Clear stores before each test"""
        alerts_store.clear()
        metrics_store.clear()
        system_metrics_store.clear()
    
    def test_create_alert(self, client, sample_alert):
        """Test creating an alert"""
        response = client.post("/api/alerts", json=json.loads(json.dumps(sample_alert.model_dump(), default=str)))
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "alert_001"
        assert data["severity"] == "high"
    
    def test_get_alerts(self, client, sample_alert):
        """Test retrieving alerts"""
        # Create alert
        client.post("/api/alerts", json=json.loads(json.dumps(sample_alert.model_dump(), default=str)))
        
        # Get alerts
        response = client.get("/api/alerts")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["id"] == "alert_001"
    
    def test_get_alerts_with_severity_filter(self, client):
        """Test alert filtering by severity"""
        # Create alerts with different severities
        alert1 = Alert(
            id="alert_001",
            timestamp=datetime.utcnow(),
            source_ip="192.168.1.100",
            destination_ip="192.168.1.1",
            protocol="TCP",
            confidence=0.95,
            severity="high",
            alert_type="intrusion",
            description="High severity alert"
        )
        alert2 = Alert(
            id="alert_002",
            timestamp=datetime.utcnow(),
            source_ip="192.168.1.101",
            destination_ip="192.168.1.1",
            protocol="TCP",
            confidence=0.60,
            severity="low",
            alert_type="anomaly",
            description="Low severity alert"
        )
        
        client.post("/api/alerts", json=json.loads(json.dumps(alert1.model_dump(), default=str)))
        client.post("/api/alerts", json=json.loads(json.dumps(alert2.model_dump(), default=str)))
        
        # Filter by high severity
        response = client.get("/api/alerts?severity=high")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["severity"] == "high"
    
    def test_get_alert_by_id(self, client, sample_alert):
        """Test retrieving a specific alert"""
        client.post("/api/alerts", json=json.loads(json.dumps(sample_alert.model_dump(), default=str)))
        
        response = client.get("/api/alerts/alert_001")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "alert_001"
    
    def test_get_nonexistent_alert(self, client):
        """Test retrieving non-existent alert"""
        response = client.get("/api/alerts/nonexistent")
        assert response.status_code == 404
    
    def test_get_alerts_with_pagination(self, client):
        """Test alert pagination"""
        # Create multiple alerts
        for i in range(10):
            alert = Alert(
                id=f"alert_{i:03d}",
                timestamp=datetime.utcnow(),
                source_ip="192.168.1.100",
                destination_ip="192.168.1.1",
                protocol="TCP",
                confidence=0.95,
                severity="high" if i % 2 == 0 else "low",
                alert_type="intrusion",
                description=f"Alert {i}"
            )
            client.post("/api/alerts", json=json.loads(json.dumps(alert.model_dump(), default=str)))
        
        # Get first page
        response = client.get("/api/alerts?limit=5&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
        
        # Get second page
        response = client.get("/api/alerts?limit=5&offset=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5


class TestMetricsOperations:
    """Metrics CRUD operations"""
    
    def setup_method(self):
        """Clear stores before each test"""
        alerts_store.clear()
        metrics_store.clear()
        system_metrics_store.clear()
    
    def test_record_metrics(self, client, sample_metrics):
        """Test recording metrics"""
        response = client.post("/api/metrics", json=json.loads(json.dumps(sample_metrics.model_dump(), default=str)))
        assert response.status_code == 200
        data = response.json()
        assert data["f1_score"] == 0.92
        assert data["precision"] == 0.94
    
    def test_get_metrics(self, client, sample_metrics):
        """Test retrieving metrics"""
        client.post("/api/metrics", json=json.loads(json.dumps(sample_metrics.model_dump(), default=str)))
        
        response = client.get("/api/metrics")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["f1_score"] == 0.92


class TestDashboardStats:
    """Dashboard statistics tests"""
    
    def setup_method(self):
        """Clear stores before each test"""
        alerts_store.clear()
        metrics_store.clear()
        system_metrics_store.clear()
    
    def test_dashboard_stats_empty(self, client):
        """Test dashboard stats with empty data"""
        response = client.get("/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_alerts"] == 0
        assert data["critical_alerts"] == 0
        assert data["alerts_today"] == 0
    
    def test_dashboard_stats_with_data(self, client):
        """Test dashboard stats with data"""
        # Create alerts
        alert1 = Alert(
            id="alert_001",
            timestamp=datetime.utcnow(),
            source_ip="192.168.1.100",
            destination_ip="192.168.1.1",
            protocol="TCP",
            confidence=0.95,
            severity="critical",
            alert_type="intrusion",
            description="Critical alert"
        )
        alert2 = Alert(
            id="alert_002",
            timestamp=datetime.utcnow(),
            source_ip="192.168.1.101",
            destination_ip="192.168.1.1",
            protocol="TCP",
            confidence=0.85,
            severity="high",
            alert_type="anomaly",
            description="High alert"
        )
        
        client.post("/api/alerts", json=json.loads(json.dumps(alert1.model_dump(), default=str)))
        client.post("/api/alerts", json=json.loads(json.dumps(alert2.model_dump(), default=str)))
        
        # Get stats
        response = client.get("/api/stats")
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_alerts"] == 2
        assert data["critical_alerts"] == 1
        assert data["high_alerts"] == 1
        assert abs(data["avg_confidence"] - 0.9) < 0.01  # (0.95 + 0.85) / 2


class TestConfiguration:
    """Configuration management tests"""
    
    def test_get_config(self, client):
        """Test getting configuration"""
        response = client.get("/api/config")
        assert response.status_code == 200
        data = response.json()
        assert "alert_severities" in data
        assert "alert_types" in data
        assert "charts" in data
    
    def test_update_config(self, client):
        """Test updating configuration"""
        new_config = {
            "refresh_interval_ms": 10000,
            "max_alerts_display": 2000
        }
        response = client.post("/api/config", json=new_config)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestSystemMetrics:
    """System metrics tests"""
    
    def setup_method(self):
        """Clear stores before each test"""
        alerts_store.clear()
        metrics_store.clear()
        system_metrics_store.clear()
    
    def test_record_system_metrics(self, client, sample_system_metrics):
        """Test recording system metrics"""
        response = client.post("/api/system-metrics", json=json.loads(json.dumps(sample_system_metrics.model_dump(), default=str)))
        assert response.status_code == 200
        data = response.json()
        assert data["cpu_percent"] == 45.2
        assert data["memory_percent"] == 62.1
    
    def test_get_system_metrics(self, client, sample_system_metrics):
        """Test retrieving system metrics"""
        client.post("/api/system-metrics", json=json.loads(json.dumps(sample_system_metrics.model_dump(), default=str)))
        
        response = client.get("/api/system-metrics")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["cpu_percent"] == 45.2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
