"""
X-IDS SIEM Integration Handler
Unified interface for multiple SIEM systems
"""

import logging
from typing import Dict, List, Any, Optional
from enum import Enum

try:
    from elasticsearch_connector import ElasticsearchConnector
    ES_AVAILABLE = True
except ImportError:
    ES_AVAILABLE = False

try:
    from splunk_connector import SplunkConnector
    SPLUNK_AVAILABLE = True
except ImportError:
    SPLUNK_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SIEMType(Enum):
    """Supported SIEM systems"""
    ELASTICSEARCH = "elasticsearch"
    SPLUNK = "splunk"
    BOTH = "both"


class SIEMHandler:
    """Unified handler for multiple SIEM systems"""
    
    def __init__(self, siem_type: str = "both", **config):
        """
        Initialize SIEM handler
        
        Args:
            siem_type: SIEM system type ('elasticsearch', 'splunk', or 'both')
            **config: Configuration for SIEM systems
        """
        self.siem_type = siem_type
        self.es_connector = None
        self.splunk_connector = None
        
        self._initialize_siems(config)
    
    def _initialize_siems(self, config: Dict[str, Any]):
        """Initialize SIEM connectors"""
        
        # Elasticsearch
        if self.siem_type in ["elasticsearch", "both"]:
            try:
                es_hosts = config.get("es_hosts", ["localhost:9200"])
                es_prefix = config.get("es_prefix", "xids")
                
                if ES_AVAILABLE:
                    self.es_connector = ElasticsearchConnector(es_hosts, es_prefix)
                    logger.info("Elasticsearch connector initialized")
                else:
                    logger.warning("Elasticsearch not available")
            except Exception as e:
                logger.error(f"Failed to initialize Elasticsearch: {e}")
        
        # Splunk
        if self.siem_type in ["splunk", "both"]:
            try:
                hec_url = config.get("hec_url", "https://localhost:8088")
                hec_token = config.get("hec_token", "")
                
                if SPLUNK_AVAILABLE and hec_token:
                    self.splunk_connector = SplunkConnector(hec_url, hec_token)
                    logger.info("Splunk connector initialized")
                else:
                    logger.warning("Splunk not available or HEC token missing")
            except Exception as e:
                logger.error(f"Failed to initialize Splunk: {e}")
    
    def send_prediction(self, prediction_data: Dict[str, Any]) -> bool:
        """Send prediction to all configured SIEMs"""
        success = True
        
        if self.es_connector:
            try:
                self.es_connector.send_prediction(prediction_data)
            except Exception as e:
                logger.error(f"Failed to send to Elasticsearch: {e}")
                success = False
        
        if self.splunk_connector:
            try:
                self.splunk_connector.send_prediction(prediction_data)
            except Exception as e:
                logger.error(f"Failed to send to Splunk: {e}")
                success = False
        
        return success
    
    def send_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Send alert to all configured SIEMs"""
        success = True
        
        if self.es_connector:
            try:
                self.es_connector.send_alert(alert_data)
            except Exception as e:
                logger.error(f"Failed to send to Elasticsearch: {e}")
                success = False
        
        if self.splunk_connector:
            try:
                self.splunk_connector.send_alert(alert_data)
            except Exception as e:
                logger.error(f"Failed to send to Splunk: {e}")
                success = False
        
        return success
    
    def bulk_send_predictions(self, predictions: List[Dict[str, Any]]) -> int:
        """Bulk send predictions to all SIEMs"""
        count = 0
        
        if self.es_connector:
            try:
                count += self.es_connector.bulk_send_predictions(predictions)
            except Exception as e:
                logger.error(f"Elasticsearch bulk send failed: {e}")
        
        if self.splunk_connector:
            try:
                count += self.splunk_connector.bulk_send_events(predictions, sourcetype="xids:prediction")
            except Exception as e:
                logger.error(f"Splunk bulk send failed: {e}")
        
        return count
    
    def bulk_send_alerts(self, alerts: List[Dict[str, Any]]) -> int:
        """Bulk send alerts to all SIEMs"""
        count = 0
        
        if self.es_connector:
            try:
                count += self.es_connector.bulk_send_alerts(alerts)
            except Exception as e:
                logger.error(f"Elasticsearch bulk send failed: {e}")
        
        if self.splunk_connector:
            try:
                count += self.splunk_connector.bulk_send_events(alerts, sourcetype="xids:alert")
            except Exception as e:
                logger.error(f"Splunk bulk send failed: {e}")
        
        return count
    
    def get_dashboard_stats(self, hours: int = 1) -> Dict[str, Any]:
        """Get stats from Elasticsearch (primary SIEM)"""
        if self.es_connector:
            return self.es_connector.get_dashboard_stats(hours)
        return {}
    
    def close(self):
        """Close all SIEM connections"""
        if self.es_connector:
            self.es_connector.close()
        if self.splunk_connector:
            logger.info("Splunk connector closed")


class AlertRouter:
    """Route alerts based on severity and rules"""
    
    def __init__(self, handler: SIEMHandler):
        """Initialize alert router"""
        self.handler = handler
        self.routes = {
            "CRITICAL": self._route_critical,
            "HIGH": self._route_high,
            "MEDIUM": self._route_medium,
            "LOW": self._route_low
        }
    
    def route_alert(self, alert: Dict[str, Any]) -> bool:
        """Route alert based on severity"""
        severity = alert.get("severity", "MEDIUM")
        route_fn = self.routes.get(severity, self._route_medium)
        return route_fn(alert)
    
    def _route_critical(self, alert: Dict[str, Any]) -> bool:
        """Route CRITICAL alerts (immediate action)"""
        logger.critical(f"CRITICAL ALERT: {alert.get('packet_id')}")
        
        # Send to all SIEMs
        self.handler.send_alert(alert)
        
        # Could trigger:
        # - PagerDuty notification
        # - SMS alert
        # - Slack message
        # - Automated response
        
        return True
    
    def _route_high(self, alert: Dict[str, Any]) -> bool:
        """Route HIGH severity alerts"""
        logger.warning(f"HIGH severity alert: {alert.get('packet_id')}")
        self.handler.send_alert(alert)
        return True
    
    def _route_medium(self, alert: Dict[str, Any]) -> bool:
        """Route MEDIUM severity alerts"""
        logger.info(f"MEDIUM severity alert: {alert.get('packet_id')}")
        self.handler.send_alert(alert)
        return True
    
    def _route_low(self, alert: Dict[str, Any]) -> bool:
        """Route LOW severity alerts"""
        logger.debug(f"LOW severity alert: {alert.get('packet_id')}")
        # Only send to Elasticsearch (cheaper storage)
        if self.handler.es_connector:
            self.handler.es_connector.send_alert(alert)
        return True


if __name__ == '__main__':
    # Example usage
    handler = SIEMHandler(
        siem_type="both",
        es_hosts=["localhost:9200"],
        es_prefix="xids",
        hec_url="https://localhost:8088",
        hec_token="YOUR-HEC-TOKEN"
    )
    
    # Send sample alert
    sample_alert = {
        "packet_id": "PKT-001",
        "severity": "HIGH",
        "attack_type": "PortScan",
        "source_ip": "192.168.1.50",
        "dest_ip": "192.168.1.100",
        "protocol": "TCP",
        "confidence": 0.92,
        "model": "RandomForest"
    }
    
    router = AlertRouter(handler)
    router.route_alert(sample_alert)
    
    handler.close()
