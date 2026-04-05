"""
X-IDS Splunk Connector
Integrates X-IDS with Splunk for real-time threat visibility
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import requests
from requests.auth import HTTPBasicAuth
from urllib.parse import urljoin

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SplunkConnector:
    """Connect X-IDS to Splunk via HTTP Event Collector (HEC)"""
    
    def __init__(self, hec_url: str = None, hec_token: str = None, 
                 sourcetype: str = "xids", verify_ssl: bool = False,
                 rest_url: str = None, username: str = None, password: str = None):
        """
        Initialize Splunk connector with authentication
        
        Args:
            hec_url: HEC URL (e.g., https://localhost:8088) - from env: SPLUNK_HEC_URL
            hec_token: HEC authentication token - from env: SPLUNK_HEC_TOKEN
            sourcetype: Splunk source type
            verify_ssl: Verify SSL certificates
            rest_url: REST API URL for search/alert creation - from env: SPLUNK_REST_URL
            username: Username for REST API - from env: SPLUNK_USERNAME
            password: Password for REST API - from env: SPLUNK_PASSWORD
        """
        # Get from environment variables if not provided
        self.hec_url = hec_url or os.getenv('SPLUNK_HEC_URL', 'https://localhost:8088')
        self.hec_token = hec_token or os.getenv('SPLUNK_HEC_TOKEN')
        self.rest_url = rest_url or os.getenv('SPLUNK_REST_URL', 'https://localhost:8089')
        self.username = username or os.getenv('SPLUNK_USERNAME')
        self.password = password or os.getenv('SPLUNK_PASSWORD')
        self.sourcetype = sourcetype
        self.verify_ssl = verify_ssl
        
        # Validate HEC token
        if not self.hec_token:
            logger.warning("⚠️  SPLUNK_HEC_TOKEN not provided. HEC operations will fail.")
        
        self.headers = {
            "Authorization": f"Splunk {self.hec_token}" if self.hec_token else "",
            "Content-Type": "application/json"
        }
        
        self._test_hec_connection()
    
    def _test_hec_connection(self):
        """Test connection to Splunk HEC"""
        try:
            response = requests.get(
                f"{self.hec_url}/services/collector/health",
                headers=self.headers,
                verify=self.verify_ssl,
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info(f"✅ Connected to Splunk HEC: {self.hec_url}")
            else:
                logger.warning(f"⚠️  Splunk HEC returned: {response.status_code}")
        except Exception as e:
            logger.warning(f"❌ Could not connect to Splunk HEC: {e}")
    
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
    
    
    def _get_rest_session(self) -> Optional[requests.Session]:
        """Get authenticated session for Splunk REST API"""
        if not self.username or not self.password:
            logger.warning("Splunk REST API requires username and password")
            return None
        
        try:
            session = requests.Session()
            session.auth = HTTPBasicAuth(self.username, self.password)
            session.verify = self.verify_ssl
            
            # Test authentication
            response = session.get(
                f"{self.rest_url}/services/auth/httpauth",
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info("✅ Authenticated with Splunk REST API")
                return session
            else:
                logger.warning(f"❌ Splunk REST API auth failed: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"❌ Failed to create REST session: {e}")
            return None
    
    def create_alert_rule(self, rule_name: str, query: str, alert_action: str = "webhook") -> bool:
        """Create a saved search alert rule in Splunk using REST API"""
        session = self._get_rest_session()
        if not session:
            return False
        
        try:
            # Create saved search
            payload = {
                'search': query,
                'dispatch.earliest_time': '-15m',
                'dispatch.latest_time': 'now',
                'alert.threshold_type': 'greater than',
                'alert.threshold': '0',
                'alert_type': 'always',
                'actions': alert_action
            }
            
            response = session.post(
                f"{self.rest_url}/services/saved/searches",
                data=payload,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Created alert rule: {rule_name}")
                return True
            else:
                logger.error(f"❌ Failed to create alert rule: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Failed to create alert rule: {e}")
            return False
    
    def search(self, query: str, output_mode: str = "json", earliest: str = "-24h") -> Dict[str, Any]:
        """Execute a search query using Splunk REST API"""
        session = self._get_rest_session()
        if not session:
            logger.error("Splunk REST API search requires authentication")
            return {}
        
        try:
            payload = {
                'search': query,
                'earliest_time': earliest,
                'latest_time': 'now',
                'output_mode': output_mode
            }
            
            response = session.post(
                f"{self.rest_url}/services/search/jobs",
                data=payload,
                timeout=30
            )
            
            if response.status_code == 201:
                result = response.json()
                logger.info(f"✅ Search executed successfully")
                return result
            else:
                logger.error(f"❌ Search failed: {response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"❌ Search execution failed: {e}")
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
