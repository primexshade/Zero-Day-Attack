"""
X-IDS Splunk Connector
Integrates X-IDS with Splunk for real-time threat visibility
"""

import logging
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import requests
from requests.auth import HTTPBasicAuth

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SplunkConnector:
    """Connect X-IDS to Splunk via HTTP Event Collector (HEC)"""
    
    def __init__(self, hec_url: str, hec_token: str, sourcetype: str = "xids"):
        """
        Initialize Splunk connector
        
        Args:
            hec_url: HEC URL (e.g., https://localhost:8088)
            hec_token: HEC authentication token
            sourcetype: Splunk source type
        """
        self.hec_url = hec_url
        self.hec_token = hec_token
        self.sourcetype = sourcetype
        self.headers = {
            "Authorization": f"Splunk {hec_token}",
            "Content-Type": "application/json"
        }
        self.verify_ssl = False
        self._test_connection()
    
    def _test_connection(self):
        """Test connection to Splunk HEC"""
        try:
            response = requests.get(
                f"{self.hec_url}/services/collector/health",
                headers=self.headers,
                verify=self.verify_ssl,
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info(f"Connected to Splunk HEC: {self.hec_url}")
            else:
                logger.warning(f"Splunk HEC returned: {response.status_code}")
        except Exception as e:
            logger.warning(f"Could not connect to Splunk HEC: {e}")
    
    def send_event(self, event: Dict[str, Any], sourcetype: str = None) -> bool:
        """Send a single event to Splunk"""
        try:
            if sourcetype is None:
                sourcetype = self.sourcetype
            
            payload = {
                "event": event,
                "sourcetype": sourcetype,
                "time": datetime.utcnow().timestamp()
            }
            
            response = requests.post(
                f"{self.hec_url}/services/collector",
                headers=self.headers,
                json=payload,
                verify=self.verify_ssl,
                timeout=10
            )
            
            if response.status_code == 200:
                return True
            else:
                logger.error(f"Splunk returned: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"Failed to send event: {e}")
            return False
    
    def send_prediction(self, prediction_data: Dict[str, Any]) -> bool:
        """Send a prediction event to Splunk"""
        event = {
            **prediction_data,
            "event_type": "prediction",
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        return self.send_event(event, sourcetype="xids:prediction")
    
    def send_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Send an alert event to Splunk"""
        # Determine severity and priority
        severity = alert_data.get("severity", "MEDIUM")
        severity_priority = {
            "CRITICAL": 1,
            "HIGH": 2,
            "MEDIUM": 3,
            "LOW": 4,
            "INFO": 5
        }
        
        event = {
            **alert_data,
            "event_type": "alert",
            "severity": severity,
            "priority": severity_priority.get(severity, 3),
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        logger.info(f"Sending {severity} alert to Splunk: {alert_data.get('packet_id')}")
        return self.send_event(event, sourcetype="xids:alert")
    
    def bulk_send_events(self, events: List[Dict[str, Any]], sourcetype: str = None) -> int:
        """Bulk send events to Splunk"""
        if sourcetype is None:
            sourcetype = self.sourcetype
        
        success_count = 0
        
        try:
            # HEC accepts multiple events in JSON format
            payload_lines = []
            
            for event in events:
                payload = {
                    "event": event,
                    "sourcetype": sourcetype,
                    "time": datetime.utcnow().timestamp()
                }
                payload_lines.append(json.dumps(payload))
            
            # Send all events (Splunk HEC accepts newline-delimited JSON)
            response = requests.post(
                f"{self.hec_url}/services/collector",
                headers=self.headers,
                data="\n".join(payload_lines),
                verify=self.verify_ssl,
                timeout=30
            )
            
            if response.status_code == 200:
                success_count = len(events)
                logger.info(f"Bulk sent {success_count} events to Splunk")
            else:
                logger.error(f"Splunk returned: {response.status_code}")
        except Exception as e:
            logger.error(f"Bulk send failed: {e}")
        
        return success_count
    
    def create_alert_rule(self, rule_name: str, query: str, alert_action: str = "webhook") -> bool:
        """Create a saved search alert rule in Splunk"""
        try:
            # This requires access to Splunk REST API (not HEC)
            # Usually requires authentication and admin access
            logger.warning("Alert rule creation requires Splunk REST API access")
            return False
        except Exception as e:
            logger.error(f"Failed to create alert rule: {e}")
            return False
    
    def search(self, query: str, output_mode: str = "json") -> Dict[str, Any]:
        """Execute a search query (requires REST API access)"""
        try:
            logger.warning("Search requires Splunk REST API access, not HEC")
            return {}
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {}


class SplunkWebhookReceiver:
    """Receive webhook callbacks from Splunk alerts"""
    
    @staticmethod
    def parse_webhook(payload: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Splunk webhook alert payload"""
        try:
            # Splunk sends alert payload in specific format
            return {
                "alert_name": payload.get("alert_name"),
                "search_query": payload.get("search"),
                "result_count": payload.get("result_count"),
                "results": payload.get("results", []),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to parse webhook: {e}")
            return {}
