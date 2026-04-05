"""
Comprehensive load and performance tests for X-IDS
Tests throughput, latency, resource usage, and SLA compliance
"""

import pytest
import time
import psutil
import threading
import numpy as np
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

logger = logging.getLogger(__name__)


class PerformanceBenchmark:
    """Performance benchmarking utilities"""
    
    def __init__(self, warmup_iterations: int = 100):
        self.warmup_iterations = warmup_iterations
        self.measurements: List[Dict] = []
    
    def measure_latency(self, func, *args, **kwargs) -> float:
        """Measure function execution latency in milliseconds"""
        start = time.perf_counter()
        func(*args, **kwargs)
        end = time.perf_counter()
        return (end - start) * 1000  # Convert to ms
    
    def measure_throughput(self, func, num_requests: int, num_threads: int = 4) -> Dict:
        """
        Measure throughput with concurrent requests
        
        Args:
            func: Function to execute
            num_requests: Total number of requests
            num_threads: Number of concurrent threads
            
        Returns:
            Dict with throughput metrics
        """
        requests_per_thread = num_requests // num_threads
        start_time = time.perf_counter()
        success_count = 0
        error_count = 0
        latencies = []
        
        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []
            for _ in range(num_threads):
                for _ in range(requests_per_thread):
                    future = executor.submit(self._execute_and_measure, func, latencies)
                    futures.append(future)
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        success_count += 1
                    else:
                        error_count += 1
                except Exception as e:
                    logger.error(f"Request failed: {e}")
                    error_count += 1
        
        end_time = time.perf_counter()
        elapsed = end_time - start_time
        
        return {
            'total_requests': num_requests,
            'successful_requests': success_count,
            'failed_requests': error_count,
            'success_rate': (success_count / num_requests) * 100 if num_requests > 0 else 0,
            'elapsed_time': elapsed,
            'throughput_rps': num_requests / elapsed if elapsed > 0 else 0,
            'avg_latency_ms': np.mean(latencies) if latencies else 0,
            'p50_latency_ms': np.percentile(latencies, 50) if latencies else 0,
            'p95_latency_ms': np.percentile(latencies, 95) if latencies else 0,
            'p99_latency_ms': np.percentile(latencies, 99) if latencies else 0,
            'min_latency_ms': np.min(latencies) if latencies else 0,
            'max_latency_ms': np.max(latencies) if latencies else 0,
        }
    
    def _execute_and_measure(self, func, latencies: List) -> bool:
        """Execute function and record latency"""
        try:
            start = time.perf_counter()
            func()
            end = time.perf_counter()
            latency = (end - start) * 1000  # Convert to ms
            latencies.append(latency)
            return True
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            return False
    
    def measure_resource_usage(self, func, duration: float = 10.0) -> Dict:
        """
        Measure resource usage during execution
        
        Args:
            func: Function to execute
            duration: Duration to run in seconds
            
        Returns:
            Dict with resource metrics
        """
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        cpu_samples = []
        memory_samples = []
        start_time = time.perf_counter()
        
        def monitor_resources():
            while time.perf_counter() - start_time < duration:
                try:
                    cpu_samples.append(process.cpu_percent(interval=0.1))
                    memory_samples.append(process.memory_info().rss / 1024 / 1024)
                    time.sleep(0.1)
                except Exception as e:
                    logger.error(f"Resource monitoring failed: {e}")
        
        monitor_thread = threading.Thread(target=monitor_resources)
        monitor_thread.start()
        
        # Execute function
        func()
        
        # Wait for monitoring to complete
        while time.perf_counter() - start_time < duration:
            time.sleep(0.1)
        monitor_thread.join(timeout=5)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        return {
            'initial_memory_mb': initial_memory,
            'final_memory_mb': final_memory,
            'memory_delta_mb': final_memory - initial_memory,
            'avg_cpu_percent': np.mean(cpu_samples) if cpu_samples else 0,
            'max_cpu_percent': np.max(cpu_samples) if cpu_samples else 0,
            'avg_memory_mb': np.mean(memory_samples) if memory_samples else 0,
            'max_memory_mb': np.max(memory_samples) if memory_samples else 0,
        }


class TestLoadPerformance:
    """Load and performance tests for X-IDS API"""
    
    @pytest.fixture
    def benchmark(self):
        """Create benchmark instance"""
        return PerformanceBenchmark()
    
    def dummy_prediction(self) -> Dict:
        """Dummy prediction for testing"""
        return {
            'prediction': 0,
            'confidence': 0.95,
            'explanation': {'feature': 'value'}
        }
    
    def test_simple_function_latency(self, benchmark):
        """Test latency of simple function"""
        latency = benchmark.measure_latency(self.dummy_prediction)
        
        # Simple function should complete in < 1ms
        assert latency < 1.0, f"Latency {latency}ms exceeds threshold"
        logger.info(f"Simple function latency: {latency:.3f}ms")
    
    def test_throughput_1000_requests(self, benchmark):
        """Test throughput with 1000 requests"""
        results = benchmark.measure_throughput(self.dummy_prediction, num_requests=1000, num_threads=10)
        
        # Target: 1000+ requests/second
        assert results['throughput_rps'] >= 100, f"Throughput {results['throughput_rps']} RPS < 100 RPS target"
        assert results['success_rate'] >= 95, f"Success rate {results['success_rate']}% < 95%"
        
        logger.info(f"Throughput: {results['throughput_rps']:.0f} RPS")
        logger.info(f"Success Rate: {results['success_rate']:.1f}%")
        logger.info(f"P95 Latency: {results['p95_latency_ms']:.1f}ms")
        logger.info(f"P99 Latency: {results['p99_latency_ms']:.1f}ms")
    
    def test_latency_p95_sla(self, benchmark):
        """Test P95 latency SLA compliance"""
        results = benchmark.measure_throughput(self.dummy_prediction, num_requests=500, num_threads=5)
        
        # Target: P95 latency < 100ms
        assert results['p95_latency_ms'] < 100, f"P95 latency {results['p95_latency_ms']:.1f}ms > 100ms SLA"
        
        logger.info(f"P95 Latency: {results['p95_latency_ms']:.1f}ms (SLA: 100ms)")
    
    def test_latency_p99_sla(self, benchmark):
        """Test P99 latency SLA compliance"""
        results = benchmark.measure_throughput(self.dummy_prediction, num_requests=500, num_threads=5)
        
        # Target: P99 latency < 200ms
        assert results['p99_latency_ms'] < 200, f"P99 latency {results['p99_latency_ms']:.1f}ms > 200ms SLA"
        
        logger.info(f"P99 Latency: {results['p99_latency_ms']:.1f}ms (SLA: 200ms)")
    
    @pytest.mark.slow
    def test_resource_stability(self, benchmark):
        """Test resource usage stability under load"""
        def sustained_load():
            for _ in range(100):
                self.dummy_prediction()
        
        results = benchmark.measure_resource_usage(sustained_load, duration=5.0)
        
        # Memory should not grow unboundedly
        assert results['memory_delta_mb'] < 100, f"Memory growth {results['memory_delta_mb']}MB > 100MB threshold"
        
        logger.info(f"Memory Delta: {results['memory_delta_mb']:.1f}MB")
        logger.info(f"Avg CPU: {results['avg_cpu_percent']:.1f}%")
        logger.info(f"Max CPU: {results['max_cpu_percent']:.1f}%")
    
    def test_concurrent_load_1000_concurrent_requests(self, benchmark):
        """Test with 1000 concurrent requests"""
        results = benchmark.measure_throughput(self.dummy_prediction, num_requests=1000, num_threads=50)
        
        assert results['success_rate'] >= 90, f"Success rate {results['success_rate']}% < 90%"
        assert results['throughput_rps'] > 0, "Throughput is zero"
        
        logger.info(f"Concurrent Load Test Results:")
        logger.info(f"  Throughput: {results['throughput_rps']:.0f} RPS")
        logger.info(f"  Success Rate: {results['success_rate']:.1f}%")
        logger.info(f"  Avg Latency: {results['avg_latency_ms']:.1f}ms")


class TestSLACompliance:
    """SLA compliance verification tests"""
    
    @pytest.fixture
    def benchmark(self):
        """Create benchmark instance"""
        return PerformanceBenchmark()
    
    def dummy_prediction(self) -> Dict:
        """Dummy prediction for testing"""
        return {
            'prediction': 0,
            'confidence': 0.95
        }
    
    def test_p95_latency_under_100ms(self, benchmark):
        """SLA: P95 latency must be < 100ms"""
        results = benchmark.measure_throughput(self.dummy_prediction, num_requests=200, num_threads=10)
        
        assert results['p95_latency_ms'] < 100, \
            f"SLA VIOLATION: P95 latency {results['p95_latency_ms']:.1f}ms >= 100ms"
        
        logger.info(f"✓ SLA PASS: P95 latency {results['p95_latency_ms']:.1f}ms < 100ms")
    
    def test_success_rate_above_99(self, benchmark):
        """SLA: Success rate must be >= 99%"""
        results = benchmark.measure_throughput(self.dummy_prediction, num_requests=500, num_threads=10)
        
        assert results['success_rate'] >= 99, \
            f"SLA VIOLATION: Success rate {results['success_rate']:.1f}% < 99%"
        
        logger.info(f"✓ SLA PASS: Success rate {results['success_rate']:.1f}% >= 99%")
    
    def test_throughput_minimum_100_rps(self, benchmark):
        """SLA: Minimum throughput 100 RPS"""
        results = benchmark.measure_throughput(self.dummy_prediction, num_requests=300, num_threads=10)
        
        assert results['throughput_rps'] >= 100, \
            f"SLA VIOLATION: Throughput {results['throughput_rps']:.0f} RPS < 100 RPS"
        
        logger.info(f"✓ SLA PASS: Throughput {results['throughput_rps']:.0f} RPS >= 100 RPS")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
