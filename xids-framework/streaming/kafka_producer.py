"""
X-IDS Kafka Producer - Network Traffic Generator for Streaming

Simulates network traffic packets and sends them to Kafka
for testing the streaming detection pipeline.
"""

import json
import time
import random
import logging
from typing import List, Optional
from datetime import datetime

try:
    from kafka import KafkaProducer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False

logger = logging.getLogger(__name__)


class NetworkTrafficSimulator:
    """Simulates realistic network traffic packets"""
    
    @staticmethod
    def generate_packet(is_attack: bool = False) -> dict:
        """
        Generate a network traffic packet
        
        Args:
            is_attack: Whether this packet should be attack traffic
            
        Returns:
            Dictionary with packet data
        """
        if is_attack:
            # Attack-like patterns
            duration = random.uniform(0.1, 100)
            bytes_sent = random.uniform(1000, 1000000)
            packets = random.uniform(10, 10000)
            byte_rate = bytes_sent / max(duration, 0.1)
        else:
            # Benign traffic patterns
            duration = random.uniform(0.01, 10)
            bytes_sent = random.uniform(100, 100000)
            packets = random.uniform(1, 1000)
            byte_rate = bytes_sent / max(duration, 0.1)
        
        # Generate 77 network features
        features = [
            duration,
            bytes_sent,
            packets,
            byte_rate,
            packets / max(duration, 0.1),  # packet rate
            random.uniform(0, 65535),  # source port
            random.uniform(0, 65535),  # dest port
            random.uniform(0, 100),    # tcp flags
            random.uniform(0, 1),      # ack count
            random.uniform(0, 100),    # syn count
            random.uniform(0, 100),    # fin count
            random.uniform(0, 100),    # rst count
            random.uniform(0, 1),      # psh flag
            random.uniform(0, 1),      # urg flag
            random.uniform(0, 100),    # cwe flag
            random.uniform(0, 1),      # ece flag
            # More features for total of 77
            *[random.uniform(0, 1) for _ in range(61)]
        ]
        
        packet = {
            'timestamp': datetime.utcnow().isoformat(),
            'packet_id': f"PKT-{int(time.time()*1000000)}",
            'features': features,
            'source_ip': f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
            'dest_ip': f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
            'protocol': random.choice(['TCP', 'UDP', 'ICMP']),
            'is_attack': is_attack
        }
        
        return packet


class KafkaTrafficProducer:
    """Produces simulated network traffic to Kafka"""
    
    def __init__(self, bootstrap_servers: List[str],
                 topic: str = "network-traffic"):
        """
        Initialize Kafka producer
        
        Args:
            bootstrap_servers: List of Kafka broker addresses
            topic: Topic to produce traffic to
        """
        if not KAFKA_AVAILABLE:
            raise ImportError("kafka-python not installed")
        
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        self.packets_sent = 0
        self.attacks_sent = 0
    
    def send_packet(self, packet: dict) -> bool:
        """Send a packet to Kafka"""
        try:
            self.producer.send(self.topic, value=packet)
            self.packets_sent += 1
            
            if packet.get('is_attack'):
                self.attacks_sent += 1
            
            return True
        except Exception as e:
            logger.error(f"Failed to send packet: {e}")
            return False
    
    def generate_stream(self, duration_seconds: int = 60,
                        packets_per_second: int = 100,
                        attack_rate: float = 0.1):
        """
        Generate continuous stream of traffic
        
        Args:
            duration_seconds: How long to generate traffic
            packets_per_second: Traffic rate
            attack_rate: Percentage of packets that are attacks (0-1)
        """
        start_time = time.time()
        
        try:
            while time.time() - start_time < duration_seconds:
                # Generate packet
                is_attack = random.random() < attack_rate
                packet = NetworkTrafficSimulator.generate_packet(is_attack)
                
                # Send packet
                self.send_packet(packet)
                
                # Rate limiting
                sleep_time = 1.0 / packets_per_second
                time.sleep(sleep_time)
                
                # Progress
                if self.packets_sent % 1000 == 0:
                    elapsed = time.time() - start_time
                    rate = self.packets_sent / elapsed
                    logger.info(f"Sent {self.packets_sent} packets ({rate:.0f} pps)")
        
        except KeyboardInterrupt:
            logger.info("Stream generation stopped")
        finally:
            self.producer.flush()
            self.print_summary()
    
    def print_summary(self):
        """Print sending summary"""
        logger.info(f"Total packets sent: {self.packets_sent}")
        logger.info(f"Total attacks sent: {self.attacks_sent}")
        logger.info(f"Attack rate: {self.attacks_sent / max(self.packets_sent, 1) * 100:.1f}%")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    # Example: Generate traffic stream
    bootstrap_servers = ['localhost:9092']
    producer = KafkaTrafficProducer(bootstrap_servers)
    
    print("Generating traffic stream (60 seconds, 100 pps, 10% attacks)...")
    producer.generate_stream(duration_seconds=60, packets_per_second=100, attack_rate=0.1)
