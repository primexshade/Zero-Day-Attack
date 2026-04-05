"""
X-IDS Kafka Consumer - Real-Time Traffic Processing

Consumes network traffic from Kafka topics, runs inference,
and produces alerts/predictions to output topics.

Supports:
- High-volume (Gbps) throughput
- Batch processing
- Real-time streaming
- Metrics tracking
"""

import json
import logging
import numpy as np
from typing import Dict, List, Optional, Callable
from datetime import datetime
import time
from dataclasses import dataclass

try:
    from kafka import KafkaConsumer, KafkaProducer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    print("⚠️  Install kafka-python: pip install kafka-python")

logger = logging.getLogger(__name__)


@dataclass
class TrafficPacket:
    """Represents a network traffic packet"""
    timestamp: str
    packet_id: str
    features: List[float]  # 77 network features
    source_ip: str
    dest_ip: str
    protocol: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp,
            'packet_id': self.packet_id,
            'features': self.features,
            'source_ip': self.source_ip,
            'dest_ip': self.dest_ip,
            'protocol': self.protocol
        }
    
    @staticmethod
    def from_json(data: str) -> 'TrafficPacket':
        """Create from JSON"""
        obj = json.loads(data)
        return TrafficPacket(
            timestamp=obj['timestamp'],
            packet_id=obj['packet_id'],
            features=obj['features'],
            source_ip=obj['source_ip'],
            dest_ip=obj['dest_ip'],
            protocol=obj['protocol']
        )


@dataclass
class DetectionResult:
    """Prediction result from model"""
    packet_id: str
    prediction: float
    confidence: float
    model: str
    latency_ms: float
    timestamp: str
    is_attack: bool
    
    def to_json(self) -> str:
        """Convert to JSON"""
        return json.dumps({
            'packet_id': self.packet_id,
            'prediction': self.prediction,
            'confidence': self.confidence,
            'model': self.model,
            'latency_ms': self.latency_ms,
            'timestamp': self.timestamp,
            'is_attack': self.is_attack
        })


class KafkaTrafficConsumer:
    """Kafka consumer for network traffic"""
    
    def __init__(self, bootstrap_servers: List[str], 
                 input_topic: str = "network-traffic",
                 group_id: str = "xids-consumer"):
        """
        Initialize Kafka traffic consumer
        
        Args:
            bootstrap_servers: List of Kafka broker addresses
            input_topic: Topic to consume traffic from
            group_id: Consumer group ID
        """
        if not KAFKA_AVAILABLE:
            raise ImportError("kafka-python not installed")
        
        self.bootstrap_servers = bootstrap_servers
        self.input_topic = input_topic
        self.group_id = group_id
        
        self.consumer = KafkaConsumer(
            input_topic,
            bootstrap_servers=bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda m: m.decode('utf-8'),
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            max_poll_records=1000  # Batch processing
        )
        
        self.packets_consumed = 0
        self.packets_processed = 0
        self.start_time = time.time()
    
    def consume_batch(self, batch_size: int = 100) -> List[TrafficPacket]:
        """
        Consume batch of traffic packets
        
        Args:
            batch_size: Number of packets to consume
            
        Returns:
            List of TrafficPacket objects
        """
        packets = []
        try:
            for message in self.consumer:
                try:
                    packet = TrafficPacket.from_json(message.value)
                    packets.append(packet)
                    self.packets_consumed += 1
                except Exception as e:
                    logger.error(f"Failed to parse packet: {e}")
                
                if len(packets) >= batch_size:
                    break
        
        except Exception as e:
            logger.error(f"Consumer error: {e}")
        
        return packets
    
    def get_metrics(self) -> Dict:
        """Get consumer metrics"""
        elapsed = time.time() - self.start_time
        throughput = self.packets_consumed / elapsed if elapsed > 0 else 0
        
        return {
            'packets_consumed': self.packets_consumed,
            'packets_processed': self.packets_processed,
            'throughput_pps': throughput,
            'elapsed_seconds': elapsed
        }


class KafkaPredictionProducer:
    """Kafka producer for predictions/alerts"""
    
    def __init__(self, bootstrap_servers: List[str],
                 output_topic: str = "xids-predictions",
                 alert_topic: str = "xids-alerts"):
        """
        Initialize Kafka producer
        
        Args:
            bootstrap_servers: List of Kafka broker addresses
            output_topic: Topic for all predictions
            alert_topic: Topic for alerts only
        """
        if not KAFKA_AVAILABLE:
            raise ImportError("kafka-python not installed")
        
        self.bootstrap_servers = bootstrap_servers
        self.output_topic = output_topic
        self.alert_topic = alert_topic
        
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            batch_size=16384,  # 16KB batches
            linger_ms=10  # Wait 10ms to batch messages
        )
        
        self.messages_sent = 0
        self.alerts_sent = 0
    
    def send_prediction(self, result: DetectionResult) -> bool:
        """Send prediction to output topic"""
        try:
            self.producer.send(self.output_topic, result.to_json())
            self.messages_sent += 1
            return True
        except Exception as e:
            logger.error(f"Failed to send prediction: {e}")
            return False
    
    def send_alert(self, result: DetectionResult, 
                   severity: str = "high") -> bool:
        """Send alert if attack detected"""
        if result.is_attack:
            try:
                alert_data = {
                    **json.loads(result.to_json()),
                    'severity': severity,
                    'alert_timestamp': datetime.utcnow().isoformat()
                }
                self.producer.send(self.alert_topic, alert_data)
                self.alerts_sent += 1
                logger.warning(f"ALERT: Attack detected {result.packet_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to send alert: {e}")
                return False
        return False
    
    def flush(self):
        """Flush pending messages"""
        self.producer.flush()
    
    def get_metrics(self) -> Dict:
        """Get producer metrics"""
        return {
            'messages_sent': self.messages_sent,
            'alerts_sent': self.alerts_sent,
            'alert_rate': self.alerts_sent / max(self.messages_sent, 1)
        }


class StreamingDetectionPipeline:
    """Complete streaming detection pipeline"""
    
    def __init__(self, kafka_bootstrap_servers: List[str],
                 prediction_callback: Callable):
        """
        Initialize streaming pipeline
        
        Args:
            kafka_bootstrap_servers: Kafka broker addresses
            prediction_callback: Function to call for prediction
                                (receives numpy array of features)
        """
        self.consumer = KafkaTrafficConsumer(kafka_bootstrap_servers)
        self.producer = KafkaPredictionProducer(kafka_bootstrap_servers)
        self.prediction_callback = prediction_callback
        
        self.total_latency = 0
        self.predictions_made = 0
        self.start_time = time.time()
    
    def process_stream(self, batch_size: int = 100, 
                       max_batches: Optional[int] = None):
        """
        Process streaming traffic
        
        Args:
            batch_size: Packets per batch
            max_batches: Max batches to process (None = infinite)
        """
        batch_count = 0
        
        try:
            while max_batches is None or batch_count < max_batches:
                # Consume batch
                packets = self.consumer.consume_batch(batch_size)
                
                if not packets:
                    time.sleep(0.1)
                    continue
                
                # Convert to numpy array
                features_batch = np.array([p.features for p in packets])
                
                # Run inference
                start_time = time.time()
                predictions = self.prediction_callback(features_batch)
                latency_ms = (time.time() - start_time) * 1000
                
                # Send results
                for packet, pred in zip(packets, predictions):
                    result = DetectionResult(
                        packet_id=packet.packet_id,
                        prediction=float(pred),
                        confidence=abs(pred) / 6.0 if pred != 0 else 0.5,
                        model='ensemble',
                        latency_ms=latency_ms,
                        timestamp=datetime.utcnow().isoformat(),
                        is_attack=pred > 0
                    )
                    
                    self.producer.send_prediction(result)
                    self.producer.send_alert(result)
                    
                    self.predictions_made += 1
                    self.total_latency += latency_ms
                
                batch_count += 1
                
                # Log progress
                if batch_count % 10 == 0:
                    logger.info(f"Processed {self.predictions_made} packets")
                    logger.info(f"Metrics: {self.get_metrics()}")
        
        except KeyboardInterrupt:
            logger.info("Stream processing stopped by user")
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
        finally:
            self.producer.flush()
    
    def get_metrics(self) -> Dict:
        """Get complete pipeline metrics"""
        elapsed = time.time() - self.start_time
        
        return {
            'elapsed_seconds': elapsed,
            'predictions_made': self.predictions_made,
            'average_latency_ms': self.total_latency / max(self.predictions_made, 1),
            'throughput_pps': self.predictions_made / elapsed if elapsed > 0 else 0,
            'consumer_metrics': self.consumer.get_metrics(),
            'producer_metrics': self.producer.get_metrics()
        }


class StreamingMetricsCollector:
    """Collects and reports streaming metrics"""
    
    def __init__(self):
        """Initialize metrics collector"""
        self.metrics = {
            'start_time': time.time(),
            'packets_processed': 0,
            'alerts_generated': 0,
            'total_latency': 0,
            'min_latency': float('inf'),
            'max_latency': 0
        }
    
    def record_prediction(self, latency_ms: float, is_alert: bool = False):
        """Record a prediction"""
        self.metrics['packets_processed'] += 1
        self.metrics['total_latency'] += latency_ms
        self.metrics['min_latency'] = min(self.metrics['min_latency'], latency_ms)
        self.metrics['max_latency'] = max(self.metrics['max_latency'], latency_ms)
        
        if is_alert:
            self.metrics['alerts_generated'] += 1
    
    def get_report(self) -> Dict:
        """Get metrics report"""
        elapsed = time.time() - self.metrics['start_time']
        
        return {
            'uptime_seconds': elapsed,
            'packets_processed': self.metrics['packets_processed'],
            'throughput_pps': self.metrics['packets_processed'] / elapsed if elapsed > 0 else 0,
            'alerts_generated': self.metrics['alerts_generated'],
            'alert_rate': self.metrics['alerts_generated'] / max(self.metrics['packets_processed'], 1),
            'latency_stats': {
                'average_ms': self.metrics['total_latency'] / max(self.metrics['packets_processed'], 1),
                'min_ms': self.metrics['min_latency'],
                'max_ms': self.metrics['max_latency']
            }
        }
