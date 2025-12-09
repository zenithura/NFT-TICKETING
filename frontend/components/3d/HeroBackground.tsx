import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { isWebGLSupported, isCypressEnvironment, isHeadlessBrowser } from '../../lib/webglUtils';

// Early check: Detect test environment before any WebGL operations
const isTestEnvironment = typeof window !== 'undefined' && (
  !!(window as any).Cypress ||
  (typeof navigator !== 'undefined' && (
    navigator.userAgent.toLowerCase().includes('headless') ||
    navigator.userAgent.toLowerCase().includes('webdriver') ||
    (navigator as any).webdriver === true
  ))
);

// Use a module-level singleton to prevent multiple WebGL contexts
let globalRenderer: THREE.WebGLRenderer | null = null;
let globalAnimationId: number | null = null;
let instanceCount = 0; // Track number of mounted instances
let globalScene: THREE.Scene | null = null;
let globalCamera: THREE.PerspectiveCamera | null = null;
let globalParticlesMesh: THREE.Points | null = null;
let mouseX = 0;
let mouseY = 0;

// Fallback component when WebGL is not available
const WebGLFallback: React.FC = () => (
  <div className="fixed inset-0 -z-10 pointer-events-none" style={{ minHeight: '100vh', background: 'transparent' }} />
);

export const HeroBackground: React.FC = React.memo(() => {
  const containerRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const particlesMeshRef = useRef<THREE.Points | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const handleResizeRef = useRef<((event: Event) => void) | null>(null);
  const handleMouseMoveRef = useRef<((event: MouseEvent) => void) | null>(null);
  const [webglSupported, setWebglSupported] = useState<boolean | null>(null);

  useEffect(() => {
    // Early exit: Check Cypress/test environment first (before any Three.js operations)
    if (isTestEnvironment || isCypressEnvironment() || isHeadlessBrowser()) {
      setWebglSupported(false);
      return;
    }

    // Check WebGL support before initializing (cached, won't create multiple contexts)
    const webglSupported = isWebGLSupported();
    if (!webglSupported) {
      setWebglSupported(false);
      return;
    }
    
    setWebglSupported(true);
    
    if (!containerRef.current) return;
    
    instanceCount++;
    
    // If already initialized, just attach canvas to this container
    if (globalRenderer && globalRenderer.domElement) {
      const existingCanvas = containerRef.current.querySelector('canvas');
      if (!existingCanvas) {
        // Move canvas to this container if it's not already there
        if (globalRenderer.domElement.parentNode) {
          (globalRenderer.domElement.parentNode as Node).removeChild(globalRenderer.domElement);
        }
        containerRef.current.appendChild(globalRenderer.domElement);
      }
      return () => {
        instanceCount--;
        // Only cleanup if this is the last instance
        if (instanceCount === 0 && globalRenderer) {
          try {
            if (globalAnimationId !== null) {
              cancelAnimationFrame(globalAnimationId);
              globalAnimationId = null;
            }
            if (globalParticlesMesh) {
              globalScene?.remove(globalParticlesMesh);
              globalParticlesMesh.geometry.dispose();
              (globalParticlesMesh.material as THREE.Material).dispose();
              globalParticlesMesh = null;
            }
            if (globalRenderer.domElement.parentNode) {
              globalRenderer.domElement.parentNode.removeChild(globalRenderer.domElement);
            }
            globalRenderer.dispose();
            globalRenderer = null;
            globalScene = null;
            globalCamera = null;
          } catch (e) {
            console.warn('Error cleaning up WebGL:', e);
          }
        }
      };
    }
    
    // Check if container already has a canvas - remove it
    const existingCanvas = containerRef.current.querySelector('canvas');
    if (existingCanvas && existingCanvas !== globalRenderer?.domElement) {
      try {
        containerRef.current.removeChild(existingCanvas);
      } catch (e) {
        // Ignore
      }
    }

    // Check if mobile - must be declared before use
    const isMobile = window.innerWidth < 768;

    try {
      // Double-check we're not in Cypress (safety check)
      if (isCypressEnvironment() || isHeadlessBrowser() || isTestEnvironment) {
        setWebglSupported(false);
        return;
      }

      // Initialize global scene, camera, renderer (only once)
      if (!globalScene) {
        globalScene = new THREE.Scene();
        sceneRef.current = globalScene;
      } else {
        sceneRef.current = globalScene;
      }
      
      if (!globalCamera) {
        globalCamera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
        globalCamera.position.z = 30;
        cameraRef.current = globalCamera;
      } else {
        cameraRef.current = globalCamera;
      }

      if (!globalRenderer) {
        // Don't create another test context - isWebGLSupported() already checked
        // WebGL support was verified earlier in the component

        globalRenderer = new THREE.WebGLRenderer({ 
          antialias: !isMobile,
          alpha: true,
          powerPreference: 'high-performance',
          preserveDrawingBuffer: false, // Better performance
          failIfMajorPerformanceCaveat: false, // Don't fail in test environments
        });
        
        if (!globalRenderer || !globalRenderer.domElement) {
          throw new Error('Failed to create WebGL renderer canvas');
        }
        
        globalRenderer.setSize(window.innerWidth, window.innerHeight);
        globalRenderer.setPixelRatio(Math.min(window.devicePixelRatio, isMobile ? 1 : 2));
        containerRef.current.appendChild(globalRenderer.domElement);
      }
    } catch (e: any) {
      // Silently fail in Cypress - log only in development
      if (!isCypressEnvironment() && !isHeadlessBrowser()) {
        console.warn('WebGL initialization failed, using fallback:', e);
      }
      setWebglSupported(false);
      return;
    }

    // Particles - reduce count on mobile for better performance
    const particlesGeometry = new THREE.BufferGeometry();
    const particleCount = isMobile ? 75 : 150; // Reduce particles on mobile
    const posArray = new Float32Array(particleCount * 3);

    for (let i = 0; i < particleCount * 3; i++) {
      posArray[i] = (Math.random() - 0.5) * 60;
    }

    particlesGeometry.setAttribute('position', new THREE.BufferAttribute(posArray, 3));
    const material = new THREE.PointsMaterial({
      size: 0.15,
      color: 0xF7931A, // Bitcoin Orange
      transparent: true,
      opacity: 0.4,
    });

    if (!globalParticlesMesh) {
      globalParticlesMesh = new THREE.Points(particlesGeometry, material);
      particlesMeshRef.current = globalParticlesMesh;
      globalScene.add(globalParticlesMesh);
    } else {
      particlesMeshRef.current = globalParticlesMesh;
    }

    // Throttle animation for better performance
    let lastFrameTime = 0;
    const targetFPS = isMobile ? 30 : 60; // Lower FPS on mobile
    const frameInterval = 1000 / targetFPS;
    let isVisible = true; // Track visibility to pause when off-screen
    
    // Use IntersectionObserver to pause animation when not visible
    const observer = new IntersectionObserver(
      (entries) => {
        isVisible = entries[0].isIntersecting;
      },
      { threshold: 0.1 }
    );
    
    if (containerRef.current) {
      observer.observe(containerRef.current);
    }
    
    // Start animation loop only if not already running
    if (globalAnimationId === null) {
      const animate = (currentTime: number) => {
        globalAnimationId = requestAnimationFrame(animate);
        
        // Skip rendering if not visible to improve scroll performance
        if (!isVisible) return;
        
        const deltaTime = currentTime - lastFrameTime;
        if (deltaTime < frameInterval) return;
        lastFrameTime = currentTime - (deltaTime % frameInterval);
        
        if (globalParticlesMesh && globalRenderer && globalCamera && globalScene) {
          globalParticlesMesh.rotation.y += 0.0005;
          globalParticlesMesh.rotation.x = mouseY * 0.05;
          globalParticlesMesh.rotation.y += mouseX * 0.05;
          globalRenderer.render(globalScene, globalCamera);
        }
      };
      globalAnimationId = requestAnimationFrame(animate);
    }

    // Throttled resize handler (only add once)
    if (!handleResizeRef.current) {
      let resizeTimeout: number | null = null;
      const handleResize = () => {
        if (resizeTimeout) return;
        resizeTimeout = window.setTimeout(() => {
          if (globalCamera && globalRenderer) {
            globalCamera.aspect = window.innerWidth / window.innerHeight;
            globalCamera.updateProjectionMatrix();
            globalRenderer.setSize(window.innerWidth, window.innerHeight);
          }
          resizeTimeout = null;
        }, 100); // Throttle to 100ms
      };
      handleResizeRef.current = handleResize;
      window.addEventListener('resize', handleResize, { passive: true });
    }

    // Throttled mouse move handler (only add once)
    if (!handleMouseMoveRef.current) {
      let mouseMoveTimeout: number | null = null;
      const handleMouseMove = (event: MouseEvent) => {
        if (mouseMoveTimeout) return;
        mouseMoveTimeout = window.setTimeout(() => {
          mouseX = (event.clientX / window.innerWidth) * 2 - 1;
          mouseY = -(event.clientY / window.innerHeight) * 2 + 1;
          mouseMoveTimeout = null;
        }, 16); // Throttle to ~60fps
      };
      handleMouseMoveRef.current = handleMouseMove;
      window.addEventListener('mousemove', handleMouseMove, { passive: true });
    }

    return () => {
      observer.disconnect();
      instanceCount--;
      
      // Only cleanup if this is the last instance
      if (instanceCount === 0) {
        // Remove event listeners (only once)
        if (handleResizeRef.current) {
          window.removeEventListener('resize', handleResizeRef.current);
          handleResizeRef.current = null;
        }
        if (handleMouseMoveRef.current) {
          window.removeEventListener('mousemove', handleMouseMoveRef.current);
          handleMouseMoveRef.current = null;
        }

        // Cancel animation frame
        if (globalAnimationId !== null) {
          cancelAnimationFrame(globalAnimationId);
          globalAnimationId = null;
        }

        // Cleanup particles
        if (globalParticlesMesh) {
          globalScene?.remove(globalParticlesMesh);
          globalParticlesMesh.geometry.dispose();
          (globalParticlesMesh.material as THREE.Material).dispose();
          globalParticlesMesh = null;
        }

        // Cleanup renderer
        if (globalRenderer) {
          try {
            if (globalRenderer.domElement.parentNode) {
              globalRenderer.domElement.parentNode.removeChild(globalRenderer.domElement);
            }
            globalRenderer.dispose();
            globalRenderer = null;
          } catch (e) {
            console.warn('Error disposing renderer:', e);
          }
        }

        // Cleanup scene and camera
        globalScene = null;
        globalCamera = null;
        sceneRef.current = null;
        cameraRef.current = null;
      }
    };
  }, []);

  // Return fallback if WebGL is not supported
  if (webglSupported === false) {
    return <WebGLFallback />;
  }

  // Return loading state while checking WebGL support
  if (webglSupported === null) {
    return <WebGLFallback />;
  }

  return (
    <div
      ref={containerRef}
      className="fixed inset-0 -z-10 pointer-events-none"
      style={{ background: 'transparent', minHeight: '100vh' }}
    />
  );

});
