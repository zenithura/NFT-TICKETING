#!/usr/bin/env node
/**
 * Backend Performance Test Script
 * Tests backend endpoints using autocannon or simple fetch
 */

import { writeFileSync, mkdirSync } from 'fs';
import { join } from 'path';
import { execSync } from 'child_process';

const PERF_DIR = join(process.cwd(), 'perf');
mkdirSync(PERF_DIR, { recursive: true });

const BASE_URL = process.env.BACKEND_URL || 'http://localhost:8000';
const ENDPOINTS = [
  { method: 'GET', path: '/api/health', name: 'health' },
  { method: 'GET', path: '/api/events/', name: 'events_list' },
  { Method: 'GET', path: '/api/marketplace/?status=active', name: 'marketplace_listings' },
];

async function testEndpoint(method, path, name) {
  const url = `${BASE_URL}${path}`;
  const startTime = Date.now();
  
  try {
    const response = await fetch(url, { method });
    const endTime = Date.now();
    const latency = endTime - startTime;
    
    const data = await response.text();
    const payloadSize = new Blob([data]).size;
    
    return {
      name,
      method,
      path,
      status: response.status,
      latency,
      payloadSize,
      success: response.ok,
    };
  } catch (error) {
    return {
      name,
      method,
      path,
      error: error.message,
      success: false,
    };
  }
}

async function runBackendTests() {
  console.log('🧪 Running backend performance tests...\n');
  console.log(`🌐 Backend URL: ${BASE_URL}\n`);

  const results = [];

  for (const endpoint of ENDPOINTS) {
    console.log(`Testing ${endpoint.method} ${endpoint.path}...`);
    const result = await testEndpoint(endpoint.method, endpoint.path, endpoint.name);
    results.push(result);
    
    if (result.success) {
      console.log(`  ✅ ${result.latency}ms, ${result.payloadSize} bytes`);
    } else {
      console.log(`  ❌ Failed: ${result.error || 'Unknown error'}`);
    }
  }

  // Calculate statistics
  const successfulTests = results.filter(r => r.success);
  const avgLatency = successfulTests.length > 0
    ? successfulTests.reduce((sum, r) => sum + r.latency, 0) / successfulTests.length
    : 0;
  const totalPayload = successfulTests.reduce((sum, r) => sum + (r.payloadSize || 0), 0);

  const report = {
    timestamp: new Date().toISOString(),
    baseUrl: BASE_URL,
    summary: {
      totalTests: results.length,
      successful: successfulTests.length,
      failed: results.length - successfulTests.length,
      averageLatency: Math.round(avgLatency),
      totalPayloadSize: totalPayload,
    },
    endpoints: results,
  };

  const reportPath = join(PERF_DIR, 'backend_report.json');
  writeFileSync(reportPath, JSON.stringify(report, null, 2));
  
  console.log('\n✅ Backend performance report saved!');
  console.log(`📊 Average latency: ${Math.round(avgLatency)}ms`);
  console.log(`📦 Total payload: ${totalPayload} bytes`);
  console.log(`📁 Report: ${reportPath}`);
}

runBackendTests().catch(console.error);

