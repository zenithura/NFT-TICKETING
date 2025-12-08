#!/usr/bin/env node
/**
 * Performance Baseline Analysis Script
 * Generates baseline performance reports including bundle analysis, Lighthouse, and coverage
 */

import { execSync } from 'child_process';
import { writeFileSync, mkdirSync, existsSync } from 'fs';
import { join, resolve } from 'path';

// Detect project root - if we're in frontend, go up one level
function getProjectRoot() {
  const cwd = process.cwd();
  // Check if we're in frontend directory
  if (cwd.endsWith('frontend') || cwd.includes('/frontend/')) {
    return resolve(cwd, '..');
  }
  return cwd;
}

const PROJECT_ROOT = getProjectRoot();
const PERF_DIR = join(PROJECT_ROOT, 'perf');
const BASELINE_DIR = join(PERF_DIR, 'baseline');
const LIGHTHOUSE_DIR = join(PERF_DIR, 'lighthouse');
const FRONTEND_DIR = join(PROJECT_ROOT, 'frontend');

// Ensure directories exist
mkdirSync(BASELINE_DIR, { recursive: true });
mkdirSync(LIGHTHOUSE_DIR, { recursive: true });

console.log('🚀 Starting Performance Baseline Analysis...\n');
console.log(`📁 Project root: ${PROJECT_ROOT}`);
console.log(`📁 Frontend dir: ${FRONTEND_DIR}\n`);

// 1. Build project and generate bundle analysis
console.log('📦 Step 1: Building project with bundle analysis...');
try {
  execSync('npm run build:perf', { stdio: 'inherit', cwd: FRONTEND_DIR });
  console.log('✅ Build complete\n');
} catch (error) {
  console.error('❌ Build failed:', error.message);
  process.exit(1);
}

// 2. Move bundle analysis to baseline
try {
  const bundlePath = join(FRONTEND_DIR, 'dist_performance', 'bundle.html');
  if (existsSync(bundlePath)) {
    const destPath = join(BASELINE_DIR, 'bundle.html');
    execSync(`cp "${bundlePath}" "${destPath}"`, { stdio: 'inherit' });
  }
} catch (error) {
  console.warn('⚠️  Bundle analysis file not found');
}

// 3. Run Puppeteer coverage (JS/CSS unused bytes)
console.log('📊 Step 2: Running Puppeteer coverage analysis...');
try {
  execSync('node scripts/puppeteer_coverage.js', { stdio: 'inherit', cwd: FRONTEND_DIR });
  const coveragePath = join(FRONTEND_DIR, 'perf', 'coverage_report.json');
  if (existsSync(coveragePath)) {
    const destPath = join(BASELINE_DIR, 'js_css_coverage.json');
    execSync(`cp "${coveragePath}" "${destPath}"`, { stdio: 'inherit' });
  }
} catch (error) {
  console.warn('⚠️  Coverage analysis failed (requires dev server running)');
}

// 4. Run Lighthouse CI for key pages
console.log('🏗️  Step 3: Running Lighthouse CI analysis...');
const pages = [
  { name: 'homepage', path: '/' },
  { name: 'marketplace', path: '/#/' },
  { name: 'dashboard', path: '/#/dashboard' },
  { name: 'create-event', path: '/#/create-event' },
];

// Note: Lighthouse CI requires the server to be running
console.log('ℹ️  Lighthouse tests require dev server. Run: npm run perf:lighthouse');

// 5. Generate baseline summary
const baselineSummary = {
  timestamp: new Date().toISOString(),
  bundleAnalysis: existsSync(join(BASELINE_DIR, 'bundle.html')),
  coverageAnalysis: existsSync(join(BASELINE_DIR, 'js_css_coverage.json')),
  lighthouseReports: pages.map(p => ({
    name: p.name,
    path: p.path,
    report: existsSync(join(LIGHTHOUSE_DIR, `${p.name}.json`)),
  })),
};

writeFileSync(
  join(BASELINE_DIR, 'baseline_summary.json'),
  JSON.stringify(baselineSummary, null, 2)
);

console.log('\n✅ Baseline analysis complete!');
console.log(`📁 Results saved to: ${BASELINE_DIR}`);
console.log('\n📋 Summary:');
console.log(JSON.stringify(baselineSummary, null, 2));

