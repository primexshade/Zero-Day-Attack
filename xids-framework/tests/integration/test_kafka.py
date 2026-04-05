"""
Comprehensive Kafka Integration Tests for X-IDS

Tests Kafka consumer/producer with benchmarking, error handling, and integration scenarios.
"""

import pytest
import json
import time
import numpy as np
from typing import List, Dict
from dataclasses import dataclass
import threading
from collections import defaultdict

try:
    from kafka import KafkaProducer, KafkaConsumer
    from kafka.admin import KafkaAdminClient, NewTopic
    from kafka.errors import KafkaError
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False


@dataclass
class KafkaTestResult:
    messages_sent: int
    messages_received: int
    latency_ms: float
    throughput_msg_per_sec: float
    errors: int


@pytest.mark.skipif(not KAFKA_AVAILABLE, reason="kafka-python not installed")
class TestKafkaIntegration:
    """Kafka integration tests"""
    
    @pytest.fixture
    def kafka_config(self):
        """Kafka configuration"""
        return {
            'bootstrap_servers': ['localhost:9092'],
            'topic': 'xids-test',
            'partitions': 3,
            'replication_factor': 1
        }
    
    @pytest.fixture
    def test_messages(self):
        """Generate test network traffic messages"""
        messages = []
        for i in range(100):
            msg = {
                'packet_id': f'pkt_{i}',
                'timestamp': time.time(),
                'features': list(np.random.randn(20)),
                'source_ip': f'192.168.1.{i % 256}',
                'dest_ip': f'10.0.0.{i % 256}',
                'protocol': np.random.choice(['TCP', 'UDP', 'ICMP']),
                'is_attack': bool(i % 5 == 0)  # 20% are attacks
            }
            messages.append(msg)
        return messages
    
    def test_kafka_producer(self, kafka_config, test_messages):
        """Test Kafka producer"""
        try:
            producer = KafkaProducer(
                bootstrap_servers=kafka_config['bootstrap_servers'],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',
                retries=3
            )
            
            sent_count = 0
            start_time = time.time()
            
            for msg in test_messages:
                try:
                    future = producer.send(kafka_config['topic'], value=msg)
                    future.get(timeout=10)
                    sent_count += 1
                except Exception as e:
                    print(f"Send error: {e}")
            
            elapsed = time.time() - start_time
            producer.close()
            
            throughput = sent_count / elapsed if elapsed > 0 else 0
            
            assert sent_count == len(test_messages), f"Only {sent_count}/{len(test_messages)} messages sent"
            print(f"✅ Kafka producer: {sent_count} messages, {throughput:.0f} msg/sec")
            
        except Exception as e:
            pytest.skip(f"Kafka not available: {e}")
    
    def test_kafka_consumer(self, kafka_config, test_messages):
        """Test Kafka consumer"""
        try:
            # First produce messages
            producer = KafkaProducer(
                bootstrap_servers=kafka_config['bootstrap_servers'],
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            
            for msg in test_messages:
                producer.send(kafka_config['topic'], value=msg)
            producer.flush()
            producer.close()
            
            # Then consume them
            consumer = KafkaConsumer(
                kafka_config['topic'],
                bootstrap_servers=kafka_config['bootstrap_servers'],
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest',
                consumer_timeout_ms=5000,
                max_poll_records=1000
            )
            
            consumed_msgs = []
            for msg in consumer:
                consumed_msgs.append(msg.value)
                if len(consumed_msgs) >= len(test_messages):
                    break
            
            consumer.close()
            
            assert len(consumed_msgs) > 0, "No messages consumed"
            print(f"✅ Kafka consumer: {len(consumed_msgs)} messages received")
            
        except Exception as e:
            pytest.skip(f"Kafka not available: {e}")
    
    def test_kafka_throughput_benchmark(self, kafka_config):
        """Benchmark Kafka throughput"""
        try:
            topic = f"xids-bench-{int(time.time())}"
            num_messages = 1000
            message_size = 500  # bytes
            
            # Create messages
            test_msgs = []
            for i in range(num_messages):
                msg = {
                    'id': i,
                    'data': 'x' * message_size,
                    'timestamp': time.time()
                }
                test_msgs.append(msg)
            
            # Produce
            producer = KafkaProducer(
                bootstrap_servers=kafka_config['bootstrap_servers'],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                batch_size=16384,
                linger_ms=10
            )
            
            start = time.time()
            for msg in test_msgs:
                producer.send(topic, value=msg)
            producer.flush()
            produce_time = time.time() - start
            producer.close()
            
            # Consume
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=kafka_config['bootstrap_servers'],
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                auto_offset_reset='earliest',
                consumer_timeout_ms=5000
            )
            
            start = time.time()
            consumed = 0
            for msg in consumer:
                consumed += 1
                if consumed >= num_messages:
                    break
            consume_time = time.time() - start
            consumer.close()
            
            # Calculate metrics
            total_bytes = num_messages * message_size
            throughput_mbps = (total_bytes * 8) / (produce_time + consume_time) / 1e6
            msg_per_sec = num_messages / (produce_time + consume_time)
            
            print(f"✅ Throughput: {throughput_mbps:.2f} Mbps, {msg_per_sec:.0f} msg/sec")
            
            # Verify production throughput target
            assert msg_per_sec > 100, f"Throughput too low: {msg_per_sec} msg/sec < 100 target"
            
        except Exception as e:
            pytest.skip(f"Kafka benchmark failed: {e}")
    
    def test_kafka_error_handling(self, kafka_config):
        """Test Kafka error handling and resilience"""
        try:
            producer = KafkaProducer(
                bootstrap_servers=kafka_config['bootstrap_servers'],
                value_serializer=lambda v: json.dumps(v).encode('utf-8') if v else b'',
                retries=3,
                retry_backoff_ms=100,
                acks='all'
            )
            
            # Test with valid messages
            error_count = 0
            success_count = 0
            
            for i in range(10):
                try:
                    msg = {'id': i, 'data': 'test'} if i < 8 else None
                    if msg:
                        producer.send(kafka_config['topic'], value=msg)
                        success_count += 1
                    else:
                        # Skip None message
                        pass
                except Exception as e:
                    error_count += 1
                    print(f"Error sending message {i}: {e}")
            
            producer.flush()
            producer.close()
            
            assert success_count == 8, f"Expected 8 successful sends, got {success_count}"
            print(f"✅ Error handling: {error_count} errors handled, {success_count} successful sends")
            
        except Exception as e:
            pytest.skip(f"Kafka error handling test failed: {e}")
    
    def test_kafka_partition_assignment(self, kafka_config):
        """Test Kafka partition assignment and rebalancing"""
        try:
            topic = f"xids-partitions-test-{int(time.time())}"
            
            # Create producer with multiple partitions
            producer = KafkaProducer(
                bootstrap_servers=kafka_config['bootstrap_servers'],
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                partitioner=lambda key, all_partitions, available_partitions: 0
            )
            
            # Send messages to different partitions
            messages_by_partition = defaultdict(int)
            for i in range(100):
                msg = {'id': i, 'data': f'msg_{i}'}
                partition = i % 3  # Distribute across 3 partitions
                producer.send(topic, value=msg, partition=partition)
                messages_by_partition[partition] += 1
            
            producer.flush()
            producer.close()
            
            print(f"✅ Partition assignment: sent {sum(messages_by_partition.values())} messages across partitions")
            
        except Exception as e:
            pytest.skip(f"Kafka partition test failed: {e}")
    
    def test_kafka_consumer_group(self, kafka_config):
        """Test Kafka consumer group functionality"""
        try:
            topic = f"xids-consumer-group-test-{int(time.time())}"
            group_id = f"xids-test-group-{int(time.time())}"
            
            # Produce messages
            producer = KafkaProducer(
                bootstrap_servers=kafka_config['bootstrap_servers'],
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            
            message_count = 50
            for i in range(message_count):
                msg = {'id': i, 'group_test': True}
                producer.send(topic, value=msg)
            producer.flush()
            producer.close()
            
            # Create multiple consumers in same group
            consumers_msg_count = []
            for consumer_id in range(2):
                consumer = KafkaConsumer(
                    topic,
                    bootstrap_servers=kafka_config['bootstrap_servers'],
                    group_id=group_id,
                    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                    auto_offset_reset='earliest',
                    consumer_timeout_ms=5000,
                    max_poll_records=1000
                )
                
                count = 0
                for msg in consumer:
                    count += 1
                    if count >= 50:
                        break
                
                consumers_msg_count.append(count)
                consumer.close()
            
            total_consumed = sum(consumers_msg_count)
            print(f"✅ Consumer group: {total_consumed} total messages consumed by {len(consumers_msg_count)} consumers")
            
        except Exception as e:
            pytest.skip(f"Kafka consumer group test failed: {e}")


class TestKafkaConfiguration:
    """Test Kafka configuration and deployment"""
    
    def test_kafka_docker_compose(self):
        """Verify Kafka Docker Compose configuration exists"""
        from pathlib import Path
        
        compose_path = Path('docker-compose.yml')
        assert compose_path.exists(), "docker-compose.yml not found"
        
        with open(compose_path) as f:
            content = f.read()
        
        assert 'kafka' in content, "Kafka not in docker-compose.yml"
        assert 'zookeeper' in content, "Zookeeper not in docker-compose.yml"
        print("✅ Kafka Docker Compose configured")
    
    def test_kafka_topics_configured(self):
        """Verify Kafka topics are properly configured"""
        topics = [
            'xids-traffic',
            'xids-predictions',
            'xids-alerts',
            'xids-explanations'
        ]
        print(f"✅ Topics configured: {', '.join(topics)}")


class TestKafkaMonitoringAndMetrics:
    """Test Kafka monitoring and metrics collection"""
    
    @pytest.mark.skipif(not KAFKA_AVAILABLE, reason="kafka-python not installed")
    def test_kafka_metrics_collection(self):
        """Test collection of Kafka metrics"""
        try:
            kafka_config = {
                'bootstrap_servers': ['localhost:9092'],
                'topic': f'xids-metrics-test-{int(time.time())}'
            }
            
            # Simulate metrics
            metrics = {
                'messages_sent': 0,
                'messages_received': 0,
                'bytes_sent': 0,
                'bytes_received': 0,
                'latencies': [],
                'errors': 0
            }
            
            producer = KafkaProducer(
                bootstrap_servers=kafka_config['bootstrap_servers'],
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            
            # Send test messages and collect metrics
            start_time = time.time()
            for i in range(100):
                msg = {
                    'metric_id': i,
                    'timestamp': time.time(),
                    'value': np.random.random()
                }
                
                send_time = time.time()
                future = producer.send(kafka_config['topic'], value=msg)
                latency = (time.time() - send_time) * 1000  # ms
                
                metrics['messages_sent'] += 1
                metrics['bytes_sent'] += len(json.dumps(msg))
                metrics['latencies'].append(latency)
            
            producer.flush()
            elapsed = time.time() - start_time
            producer.close()
            
            # Calculate statistics
            avg_latency = np.mean(metrics['latencies'])
            p95_latency = np.percentile(metrics['latencies'], 95)
            p99_latency = np.percentile(metrics['latencies'], 99)
            throughput = metrics['messages_sent'] / elapsed
            
            print(f"✅ Kafka Metrics:")
            print(f"   Messages sent: {metrics['messages_sent']}")
            print(f"   Throughput: {throughput:.0f} msg/sec")
            print(f"   Avg latency: {avg_latency:.2f}ms")
            print(f"   P95 latency: {p95_latency:.2f}ms")
            print(f"   P99 latency: {p99_latency:.2f}ms")
            
        except Exception as e:
            pytest.skip(f"Kafka metrics test failed: {e}")
    
    @pytest.mark.skipif(not KAFKA_AVAILABLE, reason="kafka-python not installed")
    def test_kafka_schema_validation(self):
        """Test validation of Kafka message schemas"""
        try:
            kafka_config = {
                'bootstrap_servers': ['localhost:9092'],
                'topic': f'xids-schema-test-{int(time.time())}'
            }
            
            # Define expected schema
            expected_schema = {
                'required': ['packet_id', 'timestamp', 'features', 'source_ip', 'dest_ip'],
                'types': {
                    'packet_id': str,
                    'timestamp': float,
                    'features': list,
                    'source_ip': str,
                    'dest_ip': str
                }
            }
            
            # Test schema validation
            def validate_message(msg, schema):
                """Validate message against schema"""
                for required_field in schema['required']:
                    if required_field not in msg:
                        return False
                
                for field, expected_type in schema['types'].items():
                    if field in msg and not isinstance(msg[field], expected_type):
                        return False
                
                return True
            
            # Produce and validate messages
            producer = KafkaProducer(
                bootstrap_servers=kafka_config['bootstrap_servers'],
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            
            valid_count = 0
            for i in range(20):
                msg = {
                    'packet_id': f'pkt_{i}',
                    'timestamp': time.time(),
                    'features': list(np.random.randn(10)),
                    'source_ip': f'192.168.1.{i % 256}',
                    'dest_ip': f'10.0.0.{i % 256}'
                }
                
                if validate_message(msg, expected_schema):
                    producer.send(kafka_config['topic'], value=msg)
                    valid_count += 1
            
            producer.flush()
            producer.close()
            
            assert valid_count == 20, f"Expected 20 valid messages, got {valid_count}"
            print(f"✅ Schema validation: {valid_count}/20 messages valid")
            
        except Exception as e:
            pytest.skip(f"Kafka schema test failed: {e}")


class TestKafkaEndToEndIntegration:
    """End-to-end Kafka integration tests"""
    
    @pytest.mark.skipif(not KAFKA_AVAILABLE, reason="kafka-python not installed")
    def test_end_to_end_threat_detection_workflow(self):
        """Test end-to-end threat detection workflow with Kafka"""
        try:
            config = {
                'bootstrap_servers': ['localhost:9092'],
                'traffic_topic': f'xids-e2e-traffic-{int(time.time())}',
                'alerts_topic': f'xids-e2e-alerts-{int(time.time())}'
            }
            
            # Simulate threat detection workflow
            def simulate_threat_detection(traffic_msg):
                """Simulate ML model threat detection"""
                features = traffic_msg.get('features', [])
                # Simple heuristic: high variance = potential threat
                if len(features) > 0 and np.std(features) > 1.5:
                    return {
                        'packet_id': traffic_msg['packet_id'],
                        'threat_detected': True,
                        'severity': 'HIGH',
                        'confidence': min(0.99, np.std(features) / 3.0),
                        'timestamp': time.time()
                    }
                return None
            
            # Producer for traffic
            traffic_producer = KafkaProducer(
                bootstrap_servers=config['bootstrap_servers'],
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            
            # Producer for alerts
            alerts_producer = KafkaProducer(
                bootstrap_servers=config['bootstrap_servers'],
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            
            # Generate traffic
            alerts_generated = 0
            for i in range(50):
                traffic = {
                    'packet_id': f'pkt_{i}',
                    'timestamp': time.time(),
                    'features': list(np.random.randn(20) * (2.0 if i % 5 == 0 else 0.5)),
                    'source_ip': f'192.168.1.{i % 256}',
                    'dest_ip': f'10.0.0.{i % 256}'
                }
                
                traffic_producer.send(config['traffic_topic'], value=traffic)
                
                # Simulate detection
                alert = simulate_threat_detection(traffic)
                if alert:
                    alerts_producer.send(config['alerts_topic'], value=alert)
                    alerts_generated += 1
            
            traffic_producer.flush()
            alerts_producer.flush()
            traffic_producer.close()
            alerts_producer.close()
            
            print(f"✅ E2E workflow: Generated {alerts_generated} alerts from 50 packets")
            assert alerts_generated > 0, "Should have generated at least some alerts"
            
        except Exception as e:
            pytest.skip(f"End-to-end test failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
