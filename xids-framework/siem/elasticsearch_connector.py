"""
X-IDS Elasticsearch Connector
Integrates X-IDS with ELK Stack for real-time threat visibility
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

try:
    from elasticsearch import Elasticsearch
    from elasticsearch.helpers import bulk
    ES_AVAILABLE = True
except ImportError:
    ES_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ElasticsearchConnector:
    """Connect X-IDS to Elasticsearch"""
    
    def __init__(self, hosts: List[str], index_prefix: str = "xids"):
        """Initialize Elasticsearch connector"""
        self.hosts = hosts
        self.index_prefix = index_prefix
        self.es = None
        
        if not ES_AVAILABLE:
            logger.warning("elasticsearch-py not installed. Run: pip install elasticsearch")
            return
        
        self.connect()
        self._create_mappings()
    
    def connect(self):
        """Connect to Elasticsearch"""
        try:
            self.es = Elasticsearch(self.hosts, request_timeout=30)
            if self.es.ping():
                logger.info(f"Connected to Elasticsearch: {self.hosts}")
            else:
                logger.warning("Could not ping Elasticsearch")
        except Exception as e:
            logger.error(f"Elasticsearch connection failed: {e}")
    
    def _create_mappings(self):
        """Create index mappings"""
        if not self.es:
            return
        
        predictions_mapping = {
            "mappings": {
                "properties": {
                    "timestamp": {"type": "date"},
                    "packet_id": {"type": "keyword"},
                    "prediction": {"type": "integer"},
                    "confidence": {"type": "float"},
                    "model": {"type": "keyword"},
                    "source_ip": {"type": "ip"},
                    "dest_ip": {"type": "ip"},
                    "protocol": {"type": "keyword"}
                }
            }
        }
        
        alerts_mapping = {
            "mappings": {
                "properties": {
                    "timestamp": {"type": "date"},
                    "packet_id": {"type": "keyword"},
                    "severity": {"type": "keyword"},
                    "attack_type": {"type": "keyword"},
                    "source_ip": {"type": "ip"},
                    "dest_ip": {"type": "ip"},
                    "protocol": {"type": "keyword"},
                    "model": {"type": "keyword"},
                    "confidence": {"type": "float"},
                    "acknowledged": {"type": "boolean"}
                }
            }
        }
        
        for index_type, mapping in [("predictions", predictions_mapping), ("alerts", alerts_mapping)]:
            try:
                index_name = f"{self.index_prefix}-{index_type}"
                if not self.es.indices.exists(index=index_name):
                    self.es.indices.create(index=index_name, body=mapping)
                    logger.info(f"Created index: {index_name}")
            except Exception as e:
                logger.warning(f"Could not create mapping: {e}")
    
    def send_prediction(self, prediction_data: Dict[str, Any]) -> Optional[str]:
        """Send a single prediction"""
        if not self.es:
            return None
        
        try:
            doc = {
                **prediction_data,
                "timestamp": datetime.utcnow().isoformat(),
                "@timestamp": datetime.utcnow()
            }
            
            result = self.es.index(index=f"{self.index_prefix}-predictions", body=doc)
            return result.get('_id')
        except Exception as e:
            logger.error(f"Failed to send prediction: {e}")
            return None
    
    def send_alert(self, alert_data: Dict[str, Any]) -> Optional[str]:
        """Send an alert"""
        if not self.es:
            return None
        
        try:
            doc = {
                **alert_data,
                "timestamp": datetime.utcnow().isoformat(),
                "@timestamp": datetime.utcnow(),
                "acknowledged": False
            }
            
            result = self.es.index(index=f"{self.index_prefix}-alerts", body=doc)
            logger.info(f"Alert sent: {alert_data.get('packet_id')}")
            return result.get('_id')
        except Exception as e:
            logger.error(f"Failed to send alert: {e}")
            return None
    
    def bulk_send_predictions(self, predictions: List[Dict[str, Any]]) -> int:
        """Bulk send predictions"""
        if not self.es:
            return 0
        
        try:
            actions = []
            for pred in predictions:
                doc = {**pred, "timestamp": datetime.utcnow().isoformat(), "@timestamp": datetime.utcnow()}
                actions.append({"_index": f"{self.index_prefix}-predictions", "_source": doc})
            
            success, failed = bulk(self.es, actions, raise_on_error=False)
            logger.info(f"Bulk sent {success} predictions")
            return success
        except Exception as e:
            logger.error(f"Bulk send failed: {e}")
            return 0
    
    def get_dashboard_stats(self, hours: int = 1) -> Dict[str, Any]:
        """Get dashboard statistics"""
        if not self.es:
            return {}
        
        try:
            pred_result = self.es.search(
                index=f"{self.index_prefix}-predictions",
                query={"range": {"@timestamp": {"gte": f"now-{hours}h"}}},
                size=0
            )
            total_predictions = pred_result['hits']['total']['value']
            
            alert_result = self.es.search(
                index=f"{self.index_prefix}-alerts",
                query={"range": {"@timestamp": {"gte": f"now-{hours}h"}}},
                size=0
            )
            total_alerts = alert_result['hits']['total']['value']
            
            alert_rate = (total_alerts / total_predictions * 100) if total_predictions > 0 else 0
            
            return {
                "time_window_hours": hours,
                "total_predictions": total_predictions,
                "total_alerts": total_alerts,
                "alert_rate_percent": alert_rate,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Stats query failed: {e}")
            return {}
    
    def close(self):
        """Close connection"""
        if self.es:
            self.es.close()
            logger.info("Elasticsearch connection closed")
