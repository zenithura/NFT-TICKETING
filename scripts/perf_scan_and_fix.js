#!/usr/bin/env node
/**
 * Performance Scan and Auto-Fix Script
 * Scans codebase for performance issues and applies low-risk automated fixes
 */

import { readFileSync, writeFileSync, readdirSync, statSync, existsSync, mkdirSync } from 'fs';
import { join, extname, resolve } from 'path';
import { execSync } from 'child_process';

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
const SUGGESTIONS_DIR = join(PROJECT_ROOT, 'perf', 'suggestions');
const FRONTEND_DIR = join(PROJECT_ROOT, 'frontend');

// Ensure suggestions directory exists
mkdirSync(SUGGESTIONS_DIR, { recursive: true });

const fixes = [];
const suggestions = [];

console.log('🔍 Starting Performance Scan and Auto-Fix...\n');

/**
 * Auto-fix 1: Add loading="lazy" to img tags
 */
function fixImageLazyLoading() {
  console.log('📸 Fixing image lazy loading...');
  
  const files = getAllFiles(join(FRONTEND_DIR, 'pages'), ['.tsx', '.jsx']);
  let fixedCount = 0;

  files.forEach(filePath => {
    try {
      let content = readFileSync(filePath, 'utf8');
      const original = content;

      // Add loading="lazy" to img tags that don't have it
      content = content.replace(
        /<img([^>]*?)(?<!loading=)([^>]*?)>/gi,
        (match, before, after) => {
          if (!match.includes('loading=') && !match.includes('data-cy')) {
            fixedCount++;
            return `<img${before} loading="lazy"${after}>`;
          }
          return match;
        }
      );

      // Only write if changed
      if (content !== original) {
        writeFileSync(filePath, content, 'utf8');
        fixes.push({
          type: 'image-lazy-loading',
          file: filePath.replace(PROJECT_ROOT, '.'),
          description: 'Added loading="lazy" to img tags',
        });
      }
    } catch (error) {
      console.warn(`  ⚠️  Failed to process ${filePath}: ${error.message}`);
    }
  });

  console.log(`  ✅ Fixed ${fixedCount} images\n`);
}

/**
 * Auto-fix 2: Add defer/async to scripts in index.html
 */
function fixScriptAttributes() {
  console.log('📜 Fixing script attributes...');
  
  const indexPath = join(FRONTEND_DIR, 'index.html');
  try {
    let content = readFileSync(indexPath, 'utf8');
    const original = content;

    // Add defer to non-critical scripts
    content = content.replace(
      /<script([^>]*?)>/gi,
      (match) => {
        if (!match.includes('defer') && !match.includes('async') && !match.includes('type="module"')) {
          return match.replace('<script', '<script defer');
        }
        return match;
      }
    );

    // Add preconnect for external domains
    if (!content.includes('preconnect')) {
      const headEnd = content.indexOf('</head>');
      if (headEnd > -1) {
        const preconnectTags = `
  <!-- Performance: Preconnect to external domains -->
  <link rel="preconnect" href="https://esm.sh" crossorigin>
  <link rel="dns-prefetch" href="https://esm.sh">
`;
        content = content.slice(0, headEnd) + preconnectTags + content.slice(headEnd);
      }
    }

    if (content !== original) {
      writeFileSync(indexPath, content, 'utf8');
      fixes.push({
        type: 'script-optimization',
        file: indexPath.replace(PROJECT_ROOT, '.'),
        description: 'Added defer to scripts and preconnect tags',
      });
      console.log('  ✅ Updated index.html\n');
    } else {
      console.log('  ℹ️  No changes needed\n');
    }
  } catch (error) {
    console.warn(`  ⚠️  Failed to process index.html: ${error.message}\n`);
  }
}

/**
 * Suggestion 1: Library replacement analysis
 */
function analyzeHeavyLibraries() {
  console.log('📚 Analyzing heavy libraries...');
  
  const packageJson = JSON.parse(readFileSync(join(FRONTEND_DIR, 'package.json'), 'utf8'));
  const heavyLibs = {
    'three': 'Consider using lighter 3D alternatives or loading on-demand',
    'recharts': 'Consider lightweight-charts or Chart.js for smaller bundle',
    '@sentry/react': 'Already optimized with dynamic imports',
  };

  const recommendations = [];
  Object.keys(heavyLibs).forEach(lib => {
    if (packageJson.dependencies[lib] || packageJson.devDependencies[lib]) {
      recommendations.push({
        library: lib,
        currentSize: 'Unknown', // Would need bundle analysis
        recommendation: heavyLibs[lib],
        risk: 'medium',
      });
    }
  });

  if (recommendations.length > 0) {
    suggestions.push({
      type: 'library-replacement',
      title: 'Consider Replacing Heavy Libraries',
      recommendations,
      risk: 'medium',
    });
    console.log(`  ⚠️  Found ${recommendations.length} heavy libraries to review\n`);
  } else {
    console.log('  ✅ No heavy libraries detected\n');
  }
}

/**
 * Auto-fix 3: Convert static imports to dynamic imports (safe cases only)
 */
function fixStaticImports() {
  console.log('📦 Analyzing static imports...');
  
  // This is a conservative approach - only suggest, don't auto-fix
  const files = getAllFiles(join(FRONTEND_DIR, 'components'), ['.tsx', '.jsx']);
  
  const heavyImports = [
    'three',
    'recharts',
    '@sentry/react',
  ];

  let foundCount = 0;
  files.forEach(filePath => {
    try {
      const content = readFileSync(filePath, 'utf8');
      
      heavyImports.forEach(lib => {
        // Check for static imports that could be dynamic
        const staticImportRegex = new RegExp(`import\\s+.*?from\\s+['"]${lib}['"]`, 'g');
        if (staticImportRegex.test(content) && !content.includes('lazy') && !content.includes('dynamic')) {
          foundCount++;
          suggestions.push({
            type: 'dynamic-import',
            file: filePath.replace(PROJECT_ROOT, '.'),
            library: lib,
            risk: 'low',
            description: `Consider converting static import of ${lib} to dynamic import`,
          });
        }
      });
    } catch (error) {
      // Skip files we can't read
    }
  });

  if (foundCount > 0) {
    console.log(`  ⚠️  Found ${foundCount} potential dynamic import opportunities\n`);
  } else {
    console.log('  ✅ No static imports to convert\n');
  }
}

/**
 * Helper: Get all files recursively
 */
function getAllFiles(dir, extensions) {
  let results = [];
  try {
    const list = readdirSync(dir);
    list.forEach(file => {
      const filePath = join(dir, file);
      const stat = statSync(filePath);
      if (stat.isDirectory()) {
        results = results.concat(getAllFiles(filePath, extensions));
      } else if (extensions.includes(extname(file))) {
        results.push(filePath);
      }
    });
  } catch (error) {
    // Directory doesn't exist or can't read
  }
  return results;
}

/**
 * Main execution
 */
async function main() {
  // Run auto-fixes
  fixImageLazyLoading();
  fixScriptAttributes();
  
  // Run analysis (suggestions only)
  analyzeHeavyLibraries();
  fixStaticImports();

  // Save suggestions
  if (suggestions.length > 0) {
    writeFileSync(
      join(SUGGESTIONS_DIR, 'suggestions.json'),
      JSON.stringify(suggestions, null, 2)
    );
    console.log(`📝 Saved ${suggestions.length} suggestions to perf/suggestions/suggestions.json\n`);
  }

  // Save fixes log
  if (fixes.length > 0) {
    const fixesDir = join(PROJECT_ROOT, 'perf');
    mkdirSync(fixesDir, { recursive: true });
    writeFileSync(
      join(fixesDir, 'auto_fixes.json'),
      JSON.stringify(fixes, null, 2)
    );
    console.log(`✅ Applied ${fixes.length} automated fixes\n`);
  }

  console.log('✅ Performance scan complete!');
  console.log(`📊 Fixes applied: ${fixes.length}`);
  console.log(`💡 Suggestions generated: ${suggestions.length}`);
}

main().catch(console.error);

