#!/usr/bin/env node
/**
 * Image Optimization Script
 * Generates optimized images (WebP, responsive sizes) using sharp
 */

import { readdirSync, statSync, mkdirSync, existsSync } from 'fs';
import { join, extname, basename, dirname } from 'path';
import { execSync } from 'child_process';

const SOURCE_DIR = join(process.cwd(), 'public');
const OUTPUT_DIR = join(process.cwd(), 'public', 'optimized');
const SIZES = [320, 640, 1024, 2048]; // Responsive breakpoints

// Check if sharp is installed
let sharp;
try {
  sharp = await import('sharp');
} catch (error) {
  console.error('❌ sharp is not installed. Installing...');
  execSync('npm install --save-dev sharp', { stdio: 'inherit', cwd: process.cwd() });
  sharp = await import('sharp');
}

// Ensure output directory exists
mkdirSync(OUTPUT_DIR, { recursive: true });

const IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp'];

function getAllImages(dir, fileList = []) {
  const files = readdirSync(dir);

  files.forEach((file) => {
    const filePath = join(dir, file);
    const stat = statSync(filePath);

    if (stat.isDirectory() && !filePath.includes('optimized')) {
      getAllImages(filePath, fileList);
    } else if (stat.isFile() && IMAGE_EXTENSIONS.includes(extname(file).toLowerCase())) {
      fileList.push(filePath);
    }
  });

  return fileList;
}

async function optimizeImage(imagePath) {
  const ext = extname(imagePath);
  const baseName = basename(imagePath, ext);
  const relativePath = imagePath.replace(SOURCE_DIR, '').replace(/^\//, '');
  const outputBaseDir = join(OUTPUT_DIR, dirname(relativePath));

  mkdirSync(outputBaseDir, { recursive: true });

  try {
    const image = sharp.default(imagePath);
    const metadata = await image.metadata();

    console.log(`📸 Optimizing: ${relativePath} (${metadata.width}x${metadata.height})`);

    // Generate responsive sizes
    for (const size of SIZES) {
      if (metadata.width && metadata.width < size) {
        // Skip if original is smaller
        continue;
      }

      // Generate WebP version
      await image
        .clone()
        .resize(size, null, { withoutEnlargement: true })
        .webp({ quality: 85 })
        .toFile(join(outputBaseDir, `${baseName}-${size}w.webp`));

      // Generate original format (optimized)
      await image
        .clone()
        .resize(size, null, { withoutEnlargement: true })
        .jpeg({ quality: 85, mozjpeg: true })
        .toFile(join(outputBaseDir, `${baseName}-${size}w${ext}`));
    }

    // Generate full-size optimized versions
    await image
      .clone()
      .webp({ quality: 85 })
      .toFile(join(outputBaseDir, `${baseName}.webp`));

    console.log(`  ✅ Generated optimized versions`);
  } catch (error) {
    console.error(`  ❌ Error optimizing ${imagePath}:`, error.message);
  }
}

async function optimizeAllImages() {
  console.log('🖼️  Starting image optimization...\n');
  console.log(`📁 Source: ${SOURCE_DIR}`);
  console.log(`📁 Output: ${OUTPUT_DIR}\n`);

  const images = getAllImages(SOURCE_DIR);
  console.log(`Found ${images.length} images to optimize\n`);

  for (const imagePath of images) {
    await optimizeImage(imagePath);
  }

  console.log('\n✅ Image optimization complete!');
  console.log(`📁 Optimized images saved to: ${OUTPUT_DIR}`);
}

optimizeAllImages().catch(console.error);

