"""
Tests for Advanced Kafka Integration Features
Tests schema registry, exactly-once semantics, DLQ, and monitoring
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock

# Import advanced Kafka components
try:
    from streaming.kafka_advanced import (
        SchemaRegistry, ExactlyOnceProcessor, DeadLetterQueue,
        KafkaMonitor, AdvancedKafkaProducer, AdvancedKafkaConsumer
    )
    ADVANCED_KAFKA_AVAILABLE = True
except ImportError:
    ADVANCED_KAFKA_AVAILABLE = False


class TestSchemaRegistry:
    """Test Kafka schema validation"""
    
    def test_schema_validation_success(self):
        """Test valid message passes schema validation"""
        message = {
            'packet_id': 'pkt_1',
            'timestamp': 1234567890.0,
            'features': [1, 2, 3],
            'source_ip': '192.168.1.1',
            'dest_ip': '10.0.0.1',
            'protocol': 'TCP'
        }
        
        assert SchemaRegistry.validate('xids-traffic', message) == True
    
    def test_schema_validation_missing_required_field(self):
        """Test validation fails when required field missing"""
        message = {
            'packet_id': 'pkt_1',
            'timestamp': 1234567890.0,
            # Missing 'features'
            'source_ip': '192.168.1.1',
            'dest_ip': '10.0.0.1'
        }
        
        assert SchemaRegistry.validate('xids-traffic', message) == False
    
    def test_schema_validation_type_mismatch(self):
        """Test validation fails with type mismatch"""
        message = {
            'packet_id': 'pkt_1',
            'timestamp': 'not a float',  # Wrong type
            'features': [1, 2, 3],
            'source_ip': '192.168.1.1',
            'dest_ip': '10.0.0.1'
        }
        
        assert SchemaRegistry.validate('xids-traffic', message) == False
    
    def test_schema_validation_alerts(self):
        """Test alert message validation"""
        message = {
            'packet_id': 'alert_1',
            'timestamp': 1234567890.0,
            'severity': 'HIGH',
            'attack_type': 'DDoS',
            'confidence': 0.95
        }
        
        assert SchemaRegistry.validate('xids-alerts', message) == True
    
    def test_unknown_topic(self):
        """Test validation with unknown topic"""
        message = {'test': 'data'}
        assert SchemaRegistry.validate('unknown-topic', message) == False


class TestExactlyOnceProcessor:
    """Test exactly-once message processing"""
    
    def test_first_message_not_duplicate(self):
        """Test first message is not marked as duplicate"""
        processor = ExactlyOnceProcessor()
        assert processor.is_duplicate('pkt_1') == False
    
    def test_duplicate_detection(self):
        """Test duplicate messages are detected"""
        processor = ExactlyOnceProcessor()
        processor.is_duplicate('pkt_1')
        
        # Same message should be detected as duplicate
        assert processor.is_duplicate('pkt_1') == True
    
    def test_different_messages_not_duplicates(self):
        """Test different messages are not detected as duplicates"""
        processor = ExactlyOnceProcessor()
        processor.is_duplicate('pkt_1')
        
        # Different message should not be duplicate
        assert processor.is_duplicate('pkt_2') == False
    
    def test_cleanup_old_entries(self):
        """Test old entries are cleaned up"""
        processor = ExactlyOnceProcessor()
        processor.cleanup_interval = 0  # Cleanup immediately
        
        processor.is_duplicate('pkt_1')
        initial_count = len(processor.processed_messages)
        
        # Force cleanup
        processor._cleanup_old_entries()
        
        # Old entries should be removed
        assert len(processor.processed_messages) < initial_count or initial_count == 0


class TestDeadLetterQueue:
    """Test Dead Letter Queue functionality"""
    
    def test_dlq_initialization(self):
        """Test DLQ initialization"""
        dlq = DeadLetterQueue(['localhost:9092'])
        assert dlq.dlq_topic == 'xids-dlq'
        assert len(dlq.get_dlq_messages()) == 0
    
    def test_send_to_dlq(self):
        """Test sending message to DLQ"""
        dlq = DeadLetterQueue(['localhost:9092'])
        
        message = {'packet_id': 'pkt_1', 'data': 'test'}
        dlq.send_to_dlq(message, 'Test error', 'xids-traffic')
        
        dlq_messages = dlq.get_dlq_messages()
        assert len(dlq_messages) == 1
        assert dlq_messages[0]['message'] == message
        assert dlq_messages[0]['error'] == 'Test error'
    
    def test_clear_dlq(self):
        """Test clearing DLQ"""
        dlq = DeadLetterQueue(['localhost:9092'])
        
        dlq.send_to_dlq({'test': 'data'}, 'Error', 'topic')
        assert len(dlq.get_dlq_messages()) == 1
        
        dlq.clear_dlq()
        assert len(dlq.get_dlq_messages()) == 0


class TestKafkaMonitor:
    """Test Kafka monitoring and metrics"""
    
    def test_monitor_initialization(self):
        """Test monitor initialization"""
        monitor = KafkaMonitor(['localhost:9092'])
        
        metrics = monitor.get_metrics()
        assert metrics['messages_sent'] == 0
        assert metrics['messages_received'] == 0
        assert metrics['errors'] == 0
    
    def test_record_send(self):
        """Test recording sent messages"""
        monitor = KafkaMonitor(['localhost:9092'])
        
        monitor.record_send(25.5, 'xids-traffic')
        
        metrics = monitor.get_metrics()
        assert metrics['messages_sent'] == 1
        assert 'xids-traffic' in metrics['topics']
        assert metrics['topics']['xids-traffic']['sent'] == 1
    
    def test_record_receive(self):
        """Test recording received messages"""
        monitor = KafkaMonitor(['localhost:9092'])
        
        monitor.record_send(25.5, 'xids-traffic')
        monitor.record_receive('xids-traffic')
        
        metrics = monitor.get_metrics()
        assert metrics['messages_received'] == 1
        assert metrics['topics']['xids-traffic']['received'] == 1
    
    def test_latency_metrics(self):
        """Test latency metrics calculation"""
        monitor = KafkaMonitor(['localhost:9092'])
        
        monitor.record_send(10.0, 'topic')
        monitor.record_send(20.0, 'topic')
        monitor.record_send(30.0, 'topic')
        
        metrics = monitor.get_metrics()
        assert 'avg_latency_ms' in metrics
        assert metrics['avg_latency_ms'] == 20.0
    
    def test_error_rate(self):
        """Test error rate calculation"""
        monitor = KafkaMonitor(['localhost:9092'])
        
        monitor.record_send(10.0, 'topic')
        monitor.record_receive('topic')
        monitor.record_error()
        
        metrics = monitor.get_metrics()
        assert 'error_rate' in metrics
        # 1 error out of 2 total operations
        assert metrics['error_rate'] == 0.5


class TestAdvancedKafkaIntegration:
    """Integration tests for advanced Kafka features"""
    
    def test_schema_registry_with_producer(self):
        """Test schema validation in producer context"""
        # Valid prediction message
        prediction = {
            'packet_id': 'pkt_123',
            'timestamp': 1234567890.0,
            'model': 'tcn',
            'prediction': 1,
            'confidence': 0.95
        }
        
        assert SchemaRegistry.validate('xids-predictions', prediction) == True
    
    def test_dlq_error_tracking(self):
        """Test DLQ tracks error messages"""
        dlq = DeadLetterQueue(['localhost:9092'])
        
        errors = [
            ('Schema validation failed', 'xids-traffic'),
            ('Timeout error', 'xids-alerts'),
            ('Connection error', 'xids-predictions')
        ]
        
        for error_msg, topic in errors:
            dlq.send_to_dlq({'test': 'data'}, error_msg, topic)
        
        messages = dlq.get_dlq_messages()
        assert len(messages) == 3
        
        errors_tracked = [msg['error'] for msg in messages]
        assert 'Schema validation failed' in errors_tracked
        assert 'Timeout error' in errors_tracked
    
    def test_exactly_once_semantics(self):
        """Test exactly-once message processing"""
        processor = ExactlyOnceProcessor()
        
        # Simulate message processing
        packets = ['pkt_1', 'pkt_2', 'pkt_3', 'pkt_1']  # pkt_1 appears twice
        
        processed = []
        for packet in packets:
            if not processor.is_duplicate(packet):
                processed.append(packet)
        
        # Should only have 3 unique packets
        assert len(processed) == 3
        assert processed == ['pkt_1', 'pkt_2', 'pkt_3']


class TestTopicConfiguration:
    """Test Kafka topic configuration"""
    
    def test_topics_defined(self):
        """Test all required topics are defined"""
        from streaming.kafka_advanced import XIDS_TOPICS
        
        required_topics = [
            'xids-traffic',
            'xids-predictions',
            'xids-alerts',
            'xids-explanations',
            'xids-dlq'
        ]
        
        for topic in required_topics:
            assert topic in XIDS_TOPICS
            assert 'partitions' in XIDS_TOPICS[topic]
            assert 'replication_factor' in XIDS_TOPICS[topic]
            assert 'retention_ms' in XIDS_TOPICS[topic]
    
    def test_dlq_retention(self):
        """Test DLQ has appropriate retention period"""
        from streaming.kafka_advanced import XIDS_TOPICS
        
        dlq_config = XIDS_TOPICS['xids-dlq']
        # DLQ should retain for 30 days
        assert dlq_config['retention_ms'] == 2592000000


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
