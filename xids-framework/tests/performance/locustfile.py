"""
Load testing for X-IDS API using Locust
Test throughput, latency, and resource usage under load
Target: 1000+ requests/second

Run with: 
  locust -f tests/locustfile.py --host=http://localhost:8000
  locust -f tests/locustfile.py --host=http://localhost:8000 -u 1000 -r 100 -t 10m
  
For non-UI mode:
  locust -f tests/locustfile.py --host=http://localhost:8000 -u 500 -r 50 --headless
"""

from locust import HttpUser, task, between, TaskSet, events
import random
import numpy as np
import json
import logging
import time
from statistics import mean

logger = logging.getLogger(__name__)

# Global metrics
request_times = []
error_count = 0
success_count = 0


class PredictionTaskSet(TaskSet):
    """Load test tasks for prediction endpoint"""
    
    def on_start(self):
        """Initialize test data"""
        self.features_cache = [
            list(np.random.randn(20)) for _ in range(100)
        ]
    
    @task(40)  # 40% of traffic
    def predict(self):
        """Test prediction endpoint - most common operation"""
        features = random.choice(self.features_cache)
        
        start_time = time.time()
        try:
            response = self.client.post(
                "/api/predict",
                json={
                    "features": features,
                    "explain": False
                },
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                request_times.append(latency_ms)
                global success_count
                success_count += 1
                logger.debug(f"Prediction successful: {latency_ms:.2f}ms")
            else:
                global error_count
                error_count += 1
                logger.warning(f"Prediction failed: {response.status_code}")
        except Exception as e:
            error_count += 1
            logger.error(f"Prediction error: {e}")
    
    @task(20)  # 20% of traffic
    def predict_with_explanation(self):
        """Test prediction with explanation"""
        features = random.choice(self.features_cache)
        
        start_time = time.time()
        try:
            response = self.client.post(
                "/api/predict",
                json={
                    "features": features,
                    "explain": True,
                    "method": "shap"
                },
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                request_times.append(latency_ms)
                success_count += 1
                logger.debug(f"Prediction with explanation: {latency_ms:.2f}ms")
            else:
                error_count += 1
                logger.warning(f"Failed: {response.status_code}")
        except Exception as e:
            error_count += 1
            logger.error(f"Explanation error: {e}")
    
    @task(10)  # 10% of traffic
    def health_check(self):
        """Test health endpoint"""
        start_time = time.time()
        try:
            response = self.client.get("/health", timeout=2)
            
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                request_times.append(latency_ms)
                success_count += 1
                logger.debug(f"Health check: {latency_ms:.2f}ms")
            else:
                error_count += 1
                logger.warning(f"Health check failed: {response.status_code}")
        except Exception as e:
            error_count += 1
            logger.error(f"Health check error: {e}")
    
    @task(15)  # 15% of traffic
    def batch_predict(self):
        """Test batch prediction"""
        batch = random.sample(self.features_cache, min(10, len(self.features_cache)))
        
        start_time = time.time()
        try:
            response = self.client.post(
                "/api/batch_predict",
                json={
                    "batch": batch,
                    "explain": False
                },
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                request_times.append(latency_ms)
                success_count += 1
                logger.debug(f"Batch prediction successful: {latency_ms:.2f}ms")
            else:
                error_count += 1
                logger.error(f"Batch prediction failed: {response.status_code}")
        except Exception as e:
            error_count += 1
            logger.error(f"Batch prediction error: {e}")
    
    @task(15)  # 15% of traffic
    def metrics_endpoint(self):
        """Test metrics endpoint"""
        start_time = time.time()
        try:
            response = self.client.get("/metrics", timeout=5)
            
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                request_times.append(latency_ms)
                success_count += 1
            else:
                error_count += 1
        except Exception as e:
            error_count += 1


class XIDSLoadTest(HttpUser):
    """Standard load test user simulating normal traffic"""
    
    tasks = [PredictionTaskSet]
    wait_time = between(0.01, 0.1)  # 10-100ms between requests


class HighThroughputTest(HttpUser):
    """High throughput test targeting 1000+ req/sec"""
    
    tasks = [PredictionTaskSet]
    wait_time = between(0.001, 0.01)  # Very aggressive: 1-10ms between requests


class StressTest(HttpUser):
    """Maximum stress test"""
    
    tasks = [PredictionTaskSet]
    wait_time = between(0, 0.001)  # Almost no wait


class RealisticTest(HttpUser):
    """Realistic user behavior with longer think time"""
    
    tasks = [PredictionTaskSet]
    wait_time = between(0.5, 2.0)  # 500ms-2s between requests


# Event handlers for metrics collection
@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Test start handler"""
    logger.info("🚀 X-IDS Load Test Started")
    logger.info(f"Target throughput: 1000+ req/sec")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Test stop handler - print summary statistics"""
    global request_times, success_count, error_count
    
    logger.info("\n" + "="*60)
    logger.info("📊 LOAD TEST SUMMARY")
    logger.info("="*60)
    
    if request_times:
        logger.info(f"✅ Successful requests: {success_count}")
        logger.info(f"❌ Failed requests: {error_count}")
        logger.info(f"📈 Total requests: {success_count + error_count}")
        
        avg_latency = mean(request_times)
        min_latency = min(request_times)
        max_latency = max(request_times)
        p95_latency = np.percentile(request_times, 95)
        p99_latency = np.percentile(request_times, 99)
        
        logger.info(f"\n⏱️  Latency Metrics (ms):")
        logger.info(f"  Min: {min_latency:.2f}")
        logger.info(f"  Avg: {avg_latency:.2f}")
        logger.info(f"  P95: {p95_latency:.2f}")
        logger.info(f"  P99: {p99_latency:.2f}")
        logger.info(f"  Max: {max_latency:.2f}")
        
        error_rate = (error_count / (success_count + error_count)) * 100 if (success_count + error_count) > 0 else 0
        logger.info(f"\n📉 Error Rate: {error_rate:.2f}%")
        logger.info("="*60)
    else:
        logger.warning("No requests were made!")


if __name__ == "__main__":
    import subprocess
    import sys
    
    print("🚀 X-IDS Locust Load Testing")
    print("="*60)
    print("\nUsage examples:")
    print("  1. Standard load test (GUI):")
    print("     locust -f tests/locustfile.py --host=http://localhost:8000")
    print("\n  2. High throughput test (1000+ req/sec target):")
    print("     locust -f tests/locustfile.py --host=http://localhost:8000 \\")
    print("       -u 1000 -r 100 -t 10m --headless")
    print("\n  3. Stress test (maximum load):")
    print("     locust -f tests/locustfile.py --host=http://localhost:8000 \\")
    print("       -u 2000 -r 200 -t 5m --headless")
    print("\nLocust parameters:")
    print("  -u: Number of concurrent users")
    print("  -r: Ramp-up rate (users per second)")
    print("  -t: Test duration (e.g., '10m' for 10 minutes)")
    print("  --headless: Run without GUI")
    print("  --csv=results: Save results to CSV")
    print("="*60)
