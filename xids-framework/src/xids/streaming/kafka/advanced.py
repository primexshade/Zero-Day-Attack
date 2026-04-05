"""
Advanced Kafka Integration for X-IDS
Includes schema registry, exactly-once semantics, DLQ, and comprehensive monitoring
"""

import logging
import json
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import os

try:
    from kafka import KafkaProducer, KafkaConsumer
    from kafka.errors import KafkaError, TopicAlreadyExistsError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class KafkaMessage:
    """Kafka message wrapper with metadata"""
    packet_id: str
    timestamp: float
    data: Dict[str, Any]
    source: str
    retry_count: int = 0
    max_retries: int = 3


class SchemaRegistry:
    """Simple schema registry for message validation"""
    
    SCHEMAS = {
        'xids-traffic': {
            'version': 1,
            'fields': {
                'packet_id': 'string',
                'timestamp': 'float',
                'features': 'array',
                'source_ip': 'string',
                'dest_ip': 'string',
                'protocol': 'string'
            },
            'required': ['packet_id', 'timestamp', 'features']
        },
        'xids-predictions': {
            'version': 1,
            'fields': {
                'packet_id': 'string',
                'timestamp': 'float',
                'model': 'string',
                'prediction': 'integer',
                'confidence': 'float'
            },
            'required': ['packet_id', 'prediction', 'confidence']
        },
        'xids-alerts': {
            'version': 1,
            'fields': {
                'packet_id': 'string',
                'timestamp': 'float',
                'severity': 'string',
                'attack_type': 'string',
                'confidence': 'float'
            },
            'required': ['packet_id', 'severity', 'confidence']
        },
        'xids-explanations': {
            'version': 1,
            'fields': {
                'packet_id': 'string',
                'timestamp': 'float',
                'method': 'string',
                'explanation': 'object'
            },
            'required': ['packet_id', 'method']
        }
    }
    
    @classmethod
    def validate(cls, topic: str, message: Dict[str, Any]) -> bool:
        """Validate message against schema"""
        if topic not in cls.SCHEMAS:
            logger.warning(f"Unknown topic: {topic}")
            return False
        
        schema = cls.SCHEMAS[topic]
        
        # Check required fields
        for field in schema['required']:
            if field not in message:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Check field types (simple validation)
        for field, expected_type in schema['fields'].items():
            if field in message:
                value = message[field]
                type_match = False
                
                if expected_type == 'string' and isinstance(value, str):
                    type_match = True
                elif expected_type == 'integer' and isinstance(value, int):
                    type_match = True
                elif expected_type == 'float' and isinstance(value, (int, float)):
                    type_match = True
                elif expected_type == 'array' and isinstance(value, list):
                    type_match = True
                elif expected_type == 'object' and isinstance(value, dict):
                    type_match = True
                
                if not type_match:
                    logger.error(f"Type mismatch for {field}: expected {expected_type}, got {type(value)}")
                    return False
        
        return True


class ExactlyOnceProcessor:
    """Ensures exactly-once message processing"""
    
    def __init__(self):
        self.processed_messages = {}  # packet_id -> timestamp
        self.cleanup_interval = 3600  # 1 hour
        
    def is_duplicate(self, packet_id: str) -> bool:
        """Check if message has been processed before"""
        if packet_id in self.processed_messages:
            return True
        
        self.processed_messages[packet_id] = time.time()
        self._cleanup_old_entries()
        return False
    
    def _cleanup_old_entries(self):
        """Remove old processed message records"""
        now = time.time()
        cutoff = now - self.cleanup_interval
        
        self.processed_messages = {
            k: v for k, v in self.processed_messages.items()
            if v > cutoff
        }


class DeadLetterQueue:
    """Handle failed messages gracefully"""
    
    def __init__(self, bootstrap_servers: List[str]):
        self.bootstrap_servers = bootstrap_servers
        self.dlq_topic = 'xids-dlq'
        self.dlq_messages = []
        
        if KAFKA_AVAILABLE:
            self.producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
        else:
            self.producer = None
    
    def send_to_dlq(self, message: Dict[str, Any], error: str, original_topic: str):
        """Send failed message to DLQ"""
        dlq_entry = {
            'original_topic': original_topic,
            'message': message,
            'error': error,
            'timestamp': datetime.utcnow().isoformat(),
            'processed_at': datetime.utcnow().isoformat()
        }
        
        self.dlq_messages.append(dlq_entry)
        
        if self.producer:
            try:
                self.producer.send(self.dlq_topic, value=dlq_entry)
                logger.warning(f"Message sent to DLQ: {message.get('packet_id', 'unknown')}")
            except Exception as e:
                logger.error(f"Failed to send to DLQ: {e}")
    
    def get_dlq_messages(self) -> List[Dict[str, Any]]:
        """Retrieve DLQ messages for review"""
        return self.dlq_messages.copy()
    
    def clear_dlq(self):
        """Clear processed DLQ messages"""
        self.dlq_messages.clear()


class KafkaMonitor:
    """Monitor Kafka cluster health and metrics"""
    
    def __init__(self, bootstrap_servers: List[str]):
        self.bootstrap_servers = bootstrap_servers
        self.metrics = {
            'messages_sent': 0,
            'messages_received': 0,
            'errors': 0,
            'latencies': [],
            'topics': {}
        }
    
    def record_send(self, latency_ms: float, topic: str):
        """Record sent message"""
        self.metrics['messages_sent'] += 1
        self.metrics['latencies'].append(latency_ms)
        
        if topic not in self.metrics['topics']:
            self.metrics['topics'][topic] = {'sent': 0, 'received': 0}
        self.metrics['topics'][topic]['sent'] += 1
    
    def record_receive(self, topic: str):
        """Record received message"""
        self.metrics['messages_received'] += 1
        if topic in self.metrics['topics']:
            self.metrics['topics'][topic]['received'] += 1
    
    def record_error(self):
        """Record error"""
        self.metrics['errors'] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        import numpy as np
        
        metrics = self.metrics.copy()
        if metrics['latencies']:
            metrics['avg_latency_ms'] = float(np.mean(metrics['latencies']))
            metrics['p95_latency_ms'] = float(np.percentile(metrics['latencies'], 95))
            metrics['p99_latency_ms'] = float(np.percentile(metrics['latencies'], 99))
        
        total = metrics['messages_sent'] + metrics['messages_received']
        if total > 0:
            metrics['error_rate'] = metrics['errors'] / total
        
        return metrics


class AdvancedKafkaProducer:
    """Advanced Kafka producer with monitoring and error handling"""
    
    def __init__(self, bootstrap_servers: List[str], monitor: Optional[KafkaMonitor] = None):
        self.bootstrap_servers = bootstrap_servers
        self.monitor = monitor or KafkaMonitor(bootstrap_servers)
        self.dlq = DeadLetterQueue(bootstrap_servers)
        
        if KAFKA_AVAILABLE:
            self.producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',  # Wait for all replicas
                retries=3,
                max_in_flight_requests_per_connection=1  # Exactly-once semantics
            )
        else:
            self.producer = None
    
    def send(self, topic: str, message: Dict[str, Any], callback: Optional[Callable] = None) -> bool:
        """Send message with validation and monitoring"""
        try:
            # Validate against schema
            if not SchemaRegistry.validate(topic, message):
                self.dlq.send_to_dlq(message, "Schema validation failed", topic)
                self.monitor.record_error()
                return False
            
            # Send message
            start_time = time.time()
            
            if self.producer:
                future = self.producer.send(topic, value=message)
                record_metadata = future.get(timeout=10)
                
                latency_ms = (time.time() - start_time) * 1000
                self.monitor.record_send(latency_ms, topic)
                
                if callback:
                    callback(record_metadata)
                
                logger.debug(f"Message sent to {topic}: {message.get('packet_id', 'unknown')}")
                return True
            else:
                logger.error("Kafka producer not available")
                return False
        
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            self.dlq.send_to_dlq(message, str(e), topic)
            self.monitor.record_error()
            return False
    
    def flush(self):
        """Flush pending messages"""
        if self.producer:
            self.producer.flush()
    
    def close(self):
        """Close producer"""
        if self.producer:
            self.producer.close()


class AdvancedKafkaConsumer:
    """Advanced Kafka consumer with monitoring and error handling"""
    
    def __init__(self, bootstrap_servers: List[str], group_id: str, 
                 monitor: Optional[KafkaMonitor] = None):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.monitor = monitor or KafkaMonitor(bootstrap_servers)
        self.exactly_once = ExactlyOnceProcessor()
        self.dlq = DeadLetterQueue(bootstrap_servers)
        
        if KAFKA_AVAILABLE:
            self.consumer = KafkaConsumer(
                bootstrap_servers=bootstrap_servers,
                group_id=group_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest',
                enable_auto_commit=False,  # Manual commit for exactly-once
                session_timeout_ms=30000
            )
        else:
            self.consumer = None
    
    def subscribe(self, topics: List[str]):
        """Subscribe to topics"""
        if self.consumer:
            self.consumer.subscribe(topics)
            logger.info(f"Subscribed to topics: {topics}")
    
    def consume(self, timeout_ms: int = 1000) -> Optional[Dict[str, Any]]:
        """Consume next message with validation"""
        if not self.consumer:
            return None
        
        try:
            messages = self.consumer.poll(timeout_ms=timeout_ms)
            
            for topic_partition, records in messages.items():
                for record in records:
                    message = record.value
                    
                    # Check for duplicates
                    packet_id = message.get('packet_id')
                    if packet_id and self.exactly_once.is_duplicate(packet_id):
                        logger.warning(f"Duplicate message: {packet_id}")
                        self.consumer.commit()
                        continue
                    
                    # Validate schema
                    if not SchemaRegistry.validate(record.topic, message):
                        self.dlq.send_to_dlq(message, "Schema validation failed", record.topic)
                        self.consumer.commit()
                        continue
                    
                    self.monitor.record_receive(record.topic)
                    logger.debug(f"Message received from {record.topic}: {packet_id}")
                    
                    # Commit offset
                    self.consumer.commit()
                    return message
            
            return None
        
        except Exception as e:
            logger.error(f"Error consuming message: {e}")
            self.monitor.record_error()
            return None
    
    def close(self):
        """Close consumer"""
        if self.consumer:
            self.consumer.close()


# Configuration for X-IDS topics
XIDS_TOPICS = {
    'xids-traffic': {
        'partitions': 3,
        'replication_factor': 1,
        'retention_ms': 86400000  # 24 hours
    },
    'xids-predictions': {
        'partitions': 3,
        'replication_factor': 1,
        'retention_ms': 86400000
    },
    'xids-alerts': {
        'partitions': 3,
        'replication_factor': 1,
        'retention_ms': 604800000  # 7 days
    },
    'xids-explanations': {
        'partitions': 2,
        'replication_factor': 1,
        'retention_ms': 604800000  # 7 days
    },
    'xids-dlq': {
        'partitions': 1,
        'replication_factor': 1,
        'retention_ms': 2592000000  # 30 days
    }
}


if __name__ == "__main__":
    # Example usage
    logger.info("Advanced Kafka Integration Module Loaded")
    logger.info(f"Available topics: {list(XIDS_TOPICS.keys())}")
