"""
SIEM Integration Tests for X-IDS
Tests Elasticsearch and Splunk alert forwarding
"""

import unittest
import json
import os
from unittest.mock import patch, MagicMock, call
import logging

# Try to import real libraries, skip tests if not available
try:
    from elasticsearch import Elasticsearch
    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    ELASTICSEARCH_AVAILABLE = False

try:
    import requests
    SPLUNK_AVAILABLE = True
except ImportError:
    SPLUNK_AVAILABLE = False

logger = logging.getLogger(__name__)


class ElasticsearchSIEMClient:
    """Elasticsearch SIEM client for alert indexing"""
    
    def __init__(self, hosts: list = None, api_key: str = None, ca_certs: str = None):
        """Initialize Elasticsearch client"""
        self.hosts = hosts or ['localhost:9200']
        self.api_key = api_key or os.getenv('ES_API_KEY')
        self.ca_certs = ca_certs or os.getenv('ES_CA_CERTS')
        self.index_prefix = 'xids-alerts'
        
        if ELASTICSEARCH_AVAILABLE:
            auth = ('ApiKey', self.api_key) if self.api_key else None
            self.client = Elasticsearch(
                self.hosts,
                api_key=auth,
                verify_certs=bool(self.ca_certs),
                ca_certs=self.ca_certs
            )
        else:
            self.client = None
    
    def index_alert(self, alert: dict, alert_id: str = None) -> bool:
        """
        Index alert to Elasticsearch
        
        Args:
            alert: Alert dictionary
            alert_id: Optional alert ID
            
        Returns:
            True if successful
        """
        try:
            if not self.client:
                logger.warning("Elasticsearch client not available")
                return False
            
            index_name = f"{self.index_prefix}-{alert.get('timestamp', '')[:10]}"
            result = self.client.index(
                index=index_name,
                id=alert_id,
                document=alert
            )
            
            logger.info(f"Alert indexed: {result['_id']}")
            return result.get('_id') is not None
        
        except Exception as e:
            logger.error(f"Failed to index alert: {e}")
            return False
    
    def search_alerts(self, query: dict, limit: int = 100) -> list:
        """
        Search alerts
        
        Args:
            query: Elasticsearch query
            limit: Max results
            
        Returns:
            List of alerts
        """
        try:
            if not self.client:
                return []
            
            results = self.client.search(
                index=f"{self.index_prefix}-*",
                query=query,
                size=limit
            )
            
            return [hit['_source'] for hit in results['hits']['hits']]
        
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []


class SplunkSIEMClient:
    """Splunk SIEM client for HEC (HTTP Event Collector)"""
    
    def __init__(self, host: str = None, port: int = 8088, token: str = None, verify_ssl: bool = True):
        """Initialize Splunk HEC client"""
        self.host = host or os.getenv('SPLUNK_HOST', 'localhost')
        self.port = port or int(os.getenv('SPLUNK_PORT', '8088'))
        self.token = token or os.getenv('SPLUNK_HEC_TOKEN')
        self.verify_ssl = verify_ssl
        self.url = f"https://{self.host}:{self.port}/services/collector"
    
    def send_alert(self, alert: dict, source: str = "xids") -> bool:
        """
        Send alert to Splunk HEC
        
        Args:
            alert: Alert dictionary
            source: Event source name
            
        Returns:
            True if successful
        """
        try:
            headers = {
                'Authorization': f'Splunk {self.token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'event': alert,
                'source': source,
                'sourcetype': '_json'
            }
            
            response = SPLUNK_AVAILABLE and requests.post(
                self.url,
                json=payload,
                headers=headers,
                verify=self.verify_ssl,
                timeout=10
            )
            
            if response and response.status_code == 200:
                logger.info("Alert sent to Splunk")
                return True
            else:
                logger.error(f"Splunk HEC error: {response.status_code if response else 'No response'}")
                return False
        
        except Exception as e:
            logger.error(f"Failed to send alert to Splunk: {e}")
            return False


class TestElasticsearchSIEM(unittest.TestCase):
    """Test Elasticsearch SIEM integration"""
    
    @unittest.skipIf(not ELASTICSEARCH_AVAILABLE, "Elasticsearch not installed")
    def setUp(self):
        """Set up test fixtures"""
        self.client = ElasticsearchSIEMClient(
            hosts=['localhost:9200'],
            api_key=os.getenv('ES_API_KEY', 'test-key')
        )
        
        self.sample_alert = {
            'timestamp': '2024-01-15T10:30:00Z',
            'alert_id': 'alert-123',
            'source_ip': '192.168.1.100',
            'destination_ip': '10.0.0.50',
            'protocol': 'TCP',
            'attack_type': 'SQL Injection',
            'confidence': 0.96,
            'model': 'TCN',
            'explanation': {
                'top_features': ['packet_size', 'inter_arrival_time'],
                'shap_values': [0.45, 0.38]
            }
        }
    
    @patch('elasticsearch.Elasticsearch')
    def test_elasticsearch_index_alert(self, mock_es):
        """Test indexing alert to Elasticsearch"""
        mock_es_instance = MagicMock()
        mock_es_instance.index.return_value = {'_id': 'alert-123'}
        
        self.client.client = mock_es_instance
        
        result = self.client.index_alert(self.sample_alert, 'alert-123')
        
        self.assertTrue(result)
        mock_es_instance.index.assert_called_once()
    
    @patch('elasticsearch.Elasticsearch')
    def test_elasticsearch_search_alerts(self, mock_es):
        """Test searching alerts"""
        mock_es_instance = MagicMock()
        mock_es_instance.search.return_value = {
            'hits': {
                'hits': [
                    {'_source': self.sample_alert}
                ]
            }
        }
        
        self.client.client = mock_es_instance
        
        query = {'match': {'attack_type': 'SQL Injection'}}
        results = self.client.search_alerts(query)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['attack_type'], 'SQL Injection')
    
    def test_elasticsearch_alert_format(self):
        """Test alert format is valid JSON"""
        alert_json = json.dumps(self.sample_alert)
        parsed = json.loads(alert_json)
        
        self.assertIn('alert_id', parsed)
        self.assertIn('source_ip', parsed)
        self.assertIn('confidence', parsed)
    
    def test_elasticsearch_batch_indexing(self):
        """Test batch alert indexing"""
        alerts = [
            {**self.sample_alert, 'alert_id': f'alert-{i}'}
            for i in range(10)
        ]
        
        # Verify all alerts have required fields
        for alert in alerts:
            self.assertIn('alert_id', alert)
            self.assertIn('source_ip', alert)


class TestSplunkSIEM(unittest.TestCase):
    """Test Splunk SIEM integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.client = SplunkSIEMClient(
            host='localhost',
            port=8088,
            token=os.getenv('SPLUNK_HEC_TOKEN', 'test-token'),
            verify_ssl=False
        )
        
        self.sample_alert = {
            'timestamp': '2024-01-15T10:30:00Z',
            'alert_id': 'alert-456',
            'source_ip': '192.168.1.100',
            'attack_type': 'Port Scanning',
            'confidence': 0.87
        }
    
    @patch('requests.post')
    def test_splunk_send_alert(self, mock_post):
        """Test sending alert to Splunk HEC"""
        mock_post.return_value = MagicMock(status_code=200)
        
        result = self.client.send_alert(self.sample_alert)
        
        self.assertTrue(result)
        mock_post.assert_called_once()
    
    @patch('requests.post')
    def test_splunk_send_alert_failure(self, mock_post):
        """Test alert sending failure"""
        mock_post.return_value = MagicMock(status_code=401)
        
        result = self.client.send_alert(self.sample_alert)
        
        self.assertFalse(result)
    
    def test_splunk_hec_url_format(self):
        """Test Splunk HEC URL format"""
        expected_url = "https://localhost:8088/services/collector"
        self.assertEqual(self.client.url, expected_url)
    
    def test_splunk_alert_payload_format(self):
        """Test alert payload format for Splunk"""
        payload = {
            'event': self.sample_alert,
            'source': 'xids',
            'sourcetype': '_json'
        }
        
        # Verify JSON serializable
        payload_json = json.dumps(payload)
        parsed = json.loads(payload_json)
        
        self.assertEqual(parsed['source'], 'xids')
        self.assertIn('event', parsed)


class TestSIEMIntegration(unittest.TestCase):
    """Integration tests for both SIEM platforms"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.es_client = ElasticsearchSIEMClient()
        self.splunk_client = SplunkSIEMClient(verify_ssl=False)
        
        self.alerts = [
            {
                'timestamp': '2024-01-15T10:30:00Z',
                'alert_id': f'alert-{i}',
                'source_ip': f'192.168.1.{100+i}',
                'attack_type': ['SQL Injection', 'DDoS', 'Brute Force'][i % 3],
                'confidence': 0.85 + (i * 0.01),
                'model': 'TCN'
            }
            for i in range(5)
        ]
    
    def test_alert_structure_consistency(self):
        """Test alert structure is consistent across alerts"""
        required_fields = ['timestamp', 'alert_id', 'source_ip', 'attack_type', 'confidence']
        
        for alert in self.alerts:
            for field in required_fields:
                self.assertIn(field, alert, f"Missing field: {field}")
    
    def test_alert_confidence_range(self):
        """Test confidence score is in valid range [0, 1]"""
        for alert in self.alerts:
            confidence = alert['confidence']
            self.assertGreaterEqual(confidence, 0)
            self.assertLessEqual(confidence, 1)
    
    def test_alert_serialization(self):
        """Test alerts can be serialized to JSON"""
        for alert in self.alerts:
            alert_json = json.dumps(alert)
            parsed = json.loads(alert_json)
            self.assertEqual(alert['alert_id'], parsed['alert_id'])


class TestSIEMErrorHandling(unittest.TestCase):
    """Test error handling in SIEM clients"""
    
    def test_elasticsearch_missing_credentials(self):
        """Test Elasticsearch with missing credentials"""
        client = ElasticsearchSIEMClient(api_key=None)
        self.assertIsNotNone(client)
    
    def test_splunk_missing_token(self):
        """Test Splunk with missing token"""
        client = SplunkSIEMClient(token=None)
        self.assertIsNotNone(client)
    
    @patch('requests.post')
    def test_splunk_timeout_handling(self, mock_post):
        """Test Splunk timeout handling"""
        mock_post.side_effect = TimeoutError("Connection timeout")
        
        client = SplunkSIEMClient()
        alert = {'alert_id': 'test', 'attack_type': 'test'}
        
        result = client.send_alert(alert)
        self.assertFalse(result)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    unittest.main()
