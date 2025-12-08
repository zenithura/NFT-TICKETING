#!/usr/bin/env node
/**
 * Puppeteer Coverage Script
 * Analyzes JavaScript and CSS coverage to identify unused bytes
 */

import puppeteer from 'puppeteer';
import { writeFileSync, mkdirSync } from 'fs';
import { join } from 'path';

const PERF_DIR = join(process.cwd(), 'perf');
mkdirSync(PERF_DIR, { recursive: true });

const BASE_URL = process.env.BASE_URL || 'http://localhost:5173';
const PAGES = [
  { name: 'homepage', path: '/' },
  { name: 'marketplace', path: '/#/' },
];

async function analyzeCoverage() {
  console.log('🔍 Starting Puppeteer coverage analysis...\n');
  
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
  });

  const results = [];

  for (const page of PAGES) {
    try {
      console.log(`📄 Analyzing ${page.name} (${page.path})...`);
      const pageInstance = await browser.newPage();
      
      // Start coverage collection
      await Promise.all([
        pageInstance.coverage.startJSCoverage(),
        pageInstance.coverage.startCSSCoverage(),
      ]);

      // Navigate and wait for page load
      await pageInstance.goto(`${BASE_URL}${page.path}`, {
        waitUntil: 'networkidle2',
        timeout: 30000,
      });

      // Wait a bit for dynamic content
      await pageInstance.waitForTimeout(2000);

      // Stop coverage collection
      const [jsCoverage, cssCoverage] = await Promise.all([
        pageInstance.coverage.stopJSCoverage(),
        pageInstance.coverage.stopCSSCoverage(),
      ]);

      // Calculate coverage statistics
      const jsStats = calculateCoverage(jsCoverage);
      const cssStats = calculateCoverage(cssCoverage);

      results.push({
        page: page.name,
        path: page.path,
        js: jsStats,
        css: cssStats,
        timestamp: new Date().toISOString(),
      });

      console.log(`  ✅ JS: ${jsStats.totalBytes} bytes total, ${jsStats.unusedBytes} unused (${jsStats.unusedPercent}%)`);
      console.log(`  ✅ CSS: ${cssStats.totalBytes} bytes total, ${cssStats.unusedBytes} unused (${cssStats.unusedPercent}%)`);

      await pageInstance.close();
    } catch (error) {
      console.error(`  ❌ Failed to analyze ${page.name}:`, error.message);
    }
  }

  await browser.close();

  // Save results
  const reportPath = join(PERF_DIR, 'coverage_report.json');
  writeFileSync(reportPath, JSON.stringify(results, null, 2));
  console.log(`\n✅ Coverage report saved to: ${reportPath}`);
}

function calculateCoverage(coverageArray) {
  let totalBytes = 0;
  let usedBytes = 0;

  for (const entry of coverageArray) {
    totalBytes += entry.text.length;
    for (const range of entry.ranges) {
      usedBytes += range.end - range.start - 1;
    }
  }

  const unusedBytes = totalBytes - usedBytes;
  const unusedPercent = totalBytes > 0 ? ((unusedBytes / totalBytes) * 100).toFixed(2) : 0;

  return {
    totalBytes,
    usedBytes,
    unusedBytes,
    unusedPercent: parseFloat(unusedPercent),
    entries: coverageArray.length,
  };
}

analyzeCoverage().catch(console.error);

