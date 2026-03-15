"""
X-IDS Streaming Server - Real-Time Detection Pipeline

Runs the complete streaming detection pipeline with:
- Kafka consumer for traffic
- Model inference
- Kafka producer for results
- Metrics tracking
"""

import logging
import argparse
from typing import Callable
import pickle
import numpy as np

try:
    from kafka_consumer import StreamingDetectionPipeline, StreamingMetricsCollector
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    print("⚠️  Run from xids-framework/streaming directory")

logger = logging.getLogger(__name__)


class StreamingServer:
    """X-IDS Streaming Server"""
    
    def __init__(self, kafka_brokers: str, model_path: str):
        """
        Initialize streaming server
        
        Args:
            kafka_brokers: Comma-separated list of Kafka brokers
            model_path: Path to trained model (pickle file)
        """
        self.kafka_brokers = [b.strip() for b in kafka_brokers.split(',')]
        self.model = self._load_model(model_path)
        self.metrics = StreamingMetricsCollector()
        
        # Create prediction pipeline
        self.pipeline = StreamingDetectionPipeline(
            self.kafka_brokers,
            self._predict
        )
    
    def _load_model(self, model_path: str):
        """Load model from file"""
        try:
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            logger.info(f"Loaded model from {model_path}")
            return model
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def _predict(self, features_batch: np.ndarray) -> np.ndarray:
        """
        Run prediction on batch
        
        Args:
            features_batch: Numpy array of shape (batch_size, 77)
            
        Returns:
            Predictions array
        """
        try:
            predictions = self.model.predict(features_batch)
            return predictions
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return np.zeros(len(features_batch))
    
    def run(self, batch_size: int = 100, max_batches: int = None):
        """
        Run streaming detection pipeline
        
        Args:
            batch_size: Packets per batch
            max_batches: Maximum batches to process (None = infinite)
        """
        logger.info("Starting X-IDS Streaming Server...")
        logger.info(f"Kafka brokers: {self.kafka_brokers}")
        logger.info(f"Batch size: {batch_size}")
        
        try:
            self.pipeline.process_stream(batch_size, max_batches)
        except KeyboardInterrupt:
            logger.info("Server stopped by user")
        finally:
            self.print_summary()
    
    def print_summary(self):
        """Print final metrics"""
        metrics = self.pipeline.get_metrics()
        
        print("\n" + "="*70)
        print("X-IDS STREAMING SERVER - FINAL METRICS")
        print("="*70)
        print(f"Elapsed Time: {metrics['elapsed_seconds']:.1f} seconds")
        print(f"Predictions Made: {metrics['predictions_made']}")
        print(f"Average Latency: {metrics['average_latency_ms']:.2f} ms")
        print(f"Throughput: {metrics['throughput_pps']:.1f} pps")
        
        consumer_metrics = metrics['consumer_metrics']
        print(f"\nConsumer:")
        print(f"  Packets Consumed: {consumer_metrics['packets_consumed']}")
        print(f"  Throughput: {consumer_metrics['throughput_pps']:.1f} pps")
        
        producer_metrics = metrics['producer_metrics']
        print(f"\nProducer:")
        print(f"  Messages Sent: {producer_metrics['messages_sent']}")
        print(f"  Alerts Sent: {producer_metrics['alerts_sent']}")
        print(f"  Alert Rate: {producer_metrics['alert_rate']*100:.1f}%")
        print("="*70 + "\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="X-IDS Streaming Server")
    parser.add_argument(
        '--kafka-brokers',
        default='localhost:9092',
        help='Kafka brokers (comma-separated)'
    )
    parser.add_argument(
        '--model-path',
        default='../models/trained_rf_model.pkl',
        help='Path to trained model'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Batch size for processing'
    )
    parser.add_argument(
        '--max-batches',
        type=int,
        default=None,
        help='Maximum batches to process (None=infinite)'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and run server
    server = StreamingServer(args.kafka_brokers, args.model_path)
    server.run(args.batch_size, args.max_batches)


if __name__ == '__main__':
    main()
