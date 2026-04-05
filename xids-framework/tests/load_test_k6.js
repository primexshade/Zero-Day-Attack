/**
 * K6 Load Testing Script for X-IDS API
 * 
 * Run with:
 *   k6 run tests/load_test_k6.js
 *   k6 run tests/load_test_k6.js -u 100 -d 5m  (100 users, 5 minute duration)
 *   k6 run tests/load_test_k6.js --vus 1000 --duration 10m  (1000 users, 10 minutes)
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Gauge, Counter } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const predictionLatency = new Trend('prediction_latency');
const batchPredictionLatency = new Trend('batch_prediction_latency');
const healthCheckLatency = new Trend('health_check_latency');
const throughput = new Counter('throughput');

// Test options
export const options = {
  // Test stages: ramp up, sustain, ramp down
  stages: [
    { duration: '30s', target: 50 },    // Ramp-up to 50 users
    { duration: '1m30s', target: 100 }, // Ramp-up to 100 users
    { duration: '3m', target: 500 },    // Ramp-up to 500 users
    { duration: '5m', target: 500 },    // Sustain 500 users for 5 minutes
    { duration: '30s', target: 0 },     // Ramp-down to 0 users
  ],
  thresholds: {
    'errors': ['rate<0.05'],                 // Error rate must be below 5%
    'prediction_latency': ['p(95)<500'],     // 95% of predictions must complete within 500ms
    'batch_prediction_latency': ['p(95)<2000'], // 95% of batch predictions within 2s
    'health_check_latency': ['p(99)<100'],   // 99% of health checks within 100ms
  },
};

// Test setup
export function setup() {
  console.log('🚀 Starting X-IDS load tests');
  console.log('Target: 1000+ requests/second');
  return { startTime: new Date() };
}

// Helper function to generate random features
function generateFeatures(size = 20) {
  const features = [];
  for (let i = 0; i < size; i++) {
    features.push(Math.random() * 2 - 1); // Random value between -1 and 1
  }
  return features;
}

// Health check test
export function testHealthCheck(data) {
  const res = http.get('http://localhost:8000/health');
  healthCheckLatency.add(res.timings.duration);
  
  const success = check(res, {
    'health check status 200': (r) => r.status === 200,
    'health check response time < 100ms': (r) => r.timings.duration < 100,
  });
  
  if (!success) {
    errorRate.add(1);
  } else {
    throughput.add(1);
  }
}

// Single prediction test
export function testPrediction(data) {
  const features = generateFeatures(20);
  const payload = JSON.stringify({
    features: features,
    explain: false,
  });
  
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer test-token',
    },
  };
  
  const res = http.post('http://localhost:8000/api/predict', payload, params);
  predictionLatency.add(res.timings.duration);
  
  const success = check(res, {
    'prediction status 200': (r) => r.status === 200,
    'prediction has result': (r) => r.body.includes('result') || r.body.includes('prediction'),
    'prediction latency < 500ms': (r) => r.timings.duration < 500,
  });
  
  if (!success) {
    errorRate.add(1);
  } else {
    throughput.add(1);
  }
}

// Batch prediction test
export function testBatchPrediction(data) {
  const batch = [];
  for (let i = 0; i < 10; i++) {
    batch.push(generateFeatures(20));
  }
  
  const payload = JSON.stringify({
    batch: batch,
    explain: false,
  });
  
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer test-token',
    },
  };
  
  const res = http.post('http://localhost:8000/api/batch_predict', payload, params);
  batchPredictionLatency.add(res.timings.duration);
  
  const success = check(res, {
    'batch prediction status 200': (r) => r.status === 200,
    'batch prediction latency < 2000ms': (r) => r.timings.duration < 2000,
  });
  
  if (!success) {
    errorRate.add(1);
  } else {
    throughput.add(1);
  }
}

// Explainability test
export function testPredictionWithExplanation(data) {
  const features = generateFeatures(20);
  const payload = JSON.stringify({
    features: features,
    explain: true,
  });
  
  const params = {
    headers: {
      'Content-Type': 'application/json',
      'Authorization': 'Bearer test-token',
    },
  };
  
  const res = http.post('http://localhost:8000/api/predict', payload, params);
  
  const success = check(res, {
    'explanation status 200': (r) => r.status === 200,
    'has explanation': (r) => r.body.includes('explanation') || r.body.includes('shap') || r.body.includes('lime'),
  });
  
  if (!success) {
    errorRate.add(1);
  }
}

// Metrics endpoint test
export function testMetrics(data) {
  const res = http.get('http://localhost:8000/metrics');
  
  const success = check(res, {
    'metrics status 200': (r) => r.status === 200,
    'metrics contains data': (r) => r.body.length > 0,
  });
  
  if (!success) {
    errorRate.add(1);
  } else {
    throughput.add(1);
  }
}

// Main test execution
export default function (data) {
  // Distribute tests based on realistic ratios
  const rand = Math.random();
  
  if (rand < 0.05) {
    testHealthCheck(data);
  } else if (rand < 0.10) {
    testMetrics(data);
  } else if (rand < 0.20) {
    testBatchPrediction(data);
  } else if (rand < 0.30) {
    testPredictionWithExplanation(data);
  } else {
    testPrediction(data);
  }
  
  // Small sleep to avoid overwhelming the server
  sleep(0.1);
}

// Test teardown
export function teardown(data) {
  console.log('✅ Load tests completed');
  console.log(`Duration: ${(new Date() - new Date(data.startTime)) / 1000} seconds`);
}
