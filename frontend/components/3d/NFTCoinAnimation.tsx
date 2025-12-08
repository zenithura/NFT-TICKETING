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

// Singleton pattern to prevent multiple WebGL contexts
let globalCoinRenderer: THREE.WebGLRenderer | null = null;
let globalCoinScene: THREE.Scene | null = null;
let globalCoinCamera: THREE.PerspectiveCamera | null = null;
let globalCoinGroup: THREE.Group | null = null;
let globalAnimationId: number | null = null;
let coinInstanceCount = 0;
let coinAnimationRunning = false;

// Fallback component when WebGL is not available
const CoinFallback: React.FC = () => (
  <div className="w-[300px] h-[300px] flex items-center justify-center bg-background-elevated rounded-lg border border-border" data-cy="coin-fallback">
    <div className="text-center text-foreground-secondary">
      <div className="text-4xl mb-2">🎫</div>
      <div className="text-sm">NFT</div>
    </div>
  </div>
);

export const NFTCoinAnimation: React.FC = React.memo(() => {
  const containerRef = useRef<HTMLDivElement>(null);
  const coinGroupRef = useRef<THREE.Group | null>(null);
  const [webglSupported, setWebglSupported] = useState<boolean | null>(null);
  
  // Enhanced Interaction State with momentum physics
  const isDragging = useRef(false);
  const previousMousePosition = useRef({ x: 0, y: 0 });
  const dragStartPos = useRef({ x: 0, y: 0 });
  const spinBoost = useRef(0); // Extra speed added on click
  const dragVelocity = useRef({ x: 0, y: 0 }); // Velocity tracking for momentum
  const lastDragTime = useRef(Date.now());

  useEffect(() => {
    // Early exit: Check Cypress/test environment first (before any Three.js operations)
    if (isTestEnvironment || isCypressEnvironment() || isHeadlessBrowser()) {
      setWebglSupported(false);
      return;
    }

    // Check WebGL support before initializing
    if (!isWebGLSupported()) {
      setWebglSupported(false);
      return;
    }
    
    setWebglSupported(true);
    
    if (!containerRef.current) return;
    
    coinInstanceCount++;
    const isMobile = window.innerWidth < 768;

    try {
      // Double-check we're not in Cypress (safety check)
      if (isCypressEnvironment() || isHeadlessBrowser() || isTestEnvironment) {
        setWebglSupported(false);
        return;
      }

      // Initialize global scene, camera, renderer (only once)
      if (!globalCoinScene) {
        globalCoinScene = new THREE.Scene();
      }
      
      if (!globalCoinCamera) {
        globalCoinCamera = new THREE.PerspectiveCamera(45, 1, 0.1, 1000);
        globalCoinCamera.position.z = 8;
      }

      if (!globalCoinRenderer) {
        // Test WebGL context before creating renderer
        const testCanvas = document.createElement('canvas');
        const testGl = testCanvas.getContext('webgl') || testCanvas.getContext('experimental-webgl');
        
        if (!testGl) {
          throw new Error('WebGL context not available');
        }

        globalCoinRenderer = new THREE.WebGLRenderer({ 
          antialias: !isMobile,
          alpha: true,
          powerPreference: 'high-performance',
          preserveDrawingBuffer: false,
          failIfMajorPerformanceCaveat: false, // Don't fail in test environments
        });
        
        if (!globalCoinRenderer || !globalCoinRenderer.domElement) {
          throw new Error('Failed to create WebGL renderer canvas');
        }
        
        globalCoinRenderer.setSize(300, 300);
        globalCoinRenderer.setClearColor(0x000000, 0);
        globalCoinRenderer.setPixelRatio(Math.min(window.devicePixelRatio, isMobile ? 1 : 2));
        globalCoinRenderer.toneMapping = THREE.ACESFilmicToneMapping;
        globalCoinRenderer.toneMappingExposure = 3.0;
        containerRef.current.appendChild(globalCoinRenderer.domElement);
      } else {
        // Reuse existing renderer
        containerRef.current.appendChild(globalCoinRenderer.domElement);
      }
    } catch (e: any) {
      // Silently fail in Cypress - log only in development
      if (!isCypressEnvironment() && !isHeadlessBrowser()) {
        console.warn('WebGL initialization failed for coin animation, using fallback:', e);
      }
      setWebglSupported(false);
      return;
    }

    // --- Coin Group --- (only create once)
    if (!globalCoinGroup) {
      globalCoinGroup = new THREE.Group();
      globalCoinGroup.rotation.x = 0.2; 
      globalCoinGroup.rotation.y = -0.5;
      globalCoinScene.add(globalCoinGroup);
    }
    coinGroupRef.current = globalCoinGroup;

    // --- Materials (High Shine Bitcoin Style) ---
    const bitcoinOrange = 0xF7931A; 
    
    const goldMaterial = new THREE.MeshStandardMaterial({
      color: bitcoinOrange,
      roughness: 0.05, // Mirror-like reflection
      metalness: 1.0,
      emissive: 0xAA5500, // Inner glow
      emissiveIntensity: 0.5,
    });

    const sideMaterial = new THREE.MeshStandardMaterial({
      color: 0xEA580C,
      roughness: 0.2,
      metalness: 1.0,
    });

    const textMaterial = new THREE.MeshStandardMaterial({ 
        color: bitcoinOrange, 
        metalness: 0.9, 
        roughness: 0.1,
        emissive: 0xAA5500,
        emissiveIntensity: 0.3
    });

    // --- Geometry --- (only create once)
    if (globalCoinGroup.children.length === 0) {
      // Coin Base
      const geometry = new THREE.CylinderGeometry(2, 2, 0.2, 64, 1);
      const coin = new THREE.Mesh(geometry, [sideMaterial, goldMaterial, goldMaterial]);
      coin.rotation.x = Math.PI / 2;
      globalCoinGroup.add(coin);

      // 3D Ticket Shape
      const ticketShape = new THREE.Shape();
      const w = 0.8, h = 0.5, r = 0.2;
      ticketShape.moveTo(-w, h);
      ticketShape.lineTo(0, h);
      ticketShape.lineTo(w, h);
      ticketShape.lineTo(w, r);
      ticketShape.absarc(w, 0, r, Math.PI/2, -Math.PI/2, true);
      ticketShape.lineTo(w, -h);
      ticketShape.lineTo(-w, -h);
      ticketShape.lineTo(-w, -r);
      ticketShape.absarc(-w, 0, r, -Math.PI/2, Math.PI/2, true);
      ticketShape.lineTo(-w, h);

      const ticketGeom = new THREE.ExtrudeGeometry(ticketShape, {
        steps: 1, depth: 0.1, bevelEnabled: true, bevelThickness: 0.05, bevelSize: 0.05, bevelSegments: 3
      });
      ticketGeom.center();

      const ticketMat = new THREE.MeshStandardMaterial({
        color: 0xFFFFFF, roughness: 0.2, metalness: 0.8, emissive: 0xFFFFFF, emissiveIntensity: 0.2
      });

      const frontTicket = new THREE.Mesh(ticketGeom, ticketMat);
      frontTicket.position.z = 0.12;
      globalCoinGroup.add(frontTicket);

      const backTicket = frontTicket.clone();
      backTicket.rotation.y = Math.PI;
      backTicket.position.z = -0.12;
      globalCoinGroup.add(backTicket);

    // 3D Text "NFT"
    const createLetter = (l: string) => {
        const s = new THREE.Shape();
        if (l === 'N') {
            s.moveTo(0,0); s.lineTo(0.15,0); s.lineTo(0.15,0.35); s.lineTo(0.35,0); s.lineTo(0.5,0); s.lineTo(0.5,0.6); s.lineTo(0.35,0.6); s.lineTo(0.35,0.25); s.lineTo(0.15,0.6); s.lineTo(0,0.6);
        } else if (l === 'F') {
            s.moveTo(0,0); s.lineTo(0.15,0); s.lineTo(0.15,0.25); s.lineTo(0.35,0.25); s.lineTo(0.35,0.38); s.lineTo(0.15,0.38); s.lineTo(0.15,0.48); s.lineTo(0.4,0.48); s.lineTo(0.4,0.6); s.lineTo(0,0.6);
        } else if (l === 'T') {
             s.moveTo(0.12,0); s.lineTo(0.28,0); s.lineTo(0.28,0.48); s.lineTo(0.4,0.48); s.lineTo(0.4,0.6); s.lineTo(0,0.6); s.lineTo(0,0.48); s.lineTo(0.12,0.48);
        }
        return s;
    };
    const textSettings = { steps: 1, depth: 0.05, bevelEnabled: false };
    
      const n = new THREE.Mesh(new THREE.ExtrudeGeometry(createLetter('N'), textSettings), textMaterial);
      n.position.set(-0.5, -0.3, 0.22);
      globalCoinGroup.add(n);

      const f = new THREE.Mesh(new THREE.ExtrudeGeometry(createLetter('F'), textSettings), textMaterial);
      f.position.set(-0.15, -0.3, 0.22);
      globalCoinGroup.add(f);

      const t = new THREE.Mesh(new THREE.ExtrudeGeometry(createLetter('T'), textSettings), textMaterial);
      t.position.set(0.3, -0.3, 0.22);
      globalCoinGroup.add(t);

      // Back text
      const backText = new THREE.Group();
      backText.add(n.clone(), f.clone(), t.clone());
      backText.rotation.y = Math.PI;
      backText.children.forEach(c => c.position.z = 0.22); // fix Z after flip
      globalCoinGroup.add(backText);
    }

    // --- Lighting (Intense for sparkles) --- (only add once)
    if (globalCoinScene.children.filter(c => c.type === 'AmbientLight').length === 0) {
      const ambient = new THREE.AmbientLight(0xffffff, 0.5);
      globalCoinScene.add(ambient);

      const mainLight = new THREE.PointLight(0xFFFFFF, 10, 50);
      mainLight.position.set(5, 5, 10);
      globalCoinScene.add(mainLight);

      const warmLight = new THREE.PointLight(0xF7931A, 8, 50);
      warmLight.position.set(-5, -5, 10);
      globalCoinScene.add(warmLight);

      const rimLight = new THREE.PointLight(0xFFD700, 10, 50);
      rimLight.position.set(0, 5, -5);
      globalCoinScene.add(rimLight);
    }

    // --- Enhanced Animation Loop with Physics-Based Motion ---
    // Only start animation if not already running
    try {
      if (!coinAnimationRunning && globalCoinRenderer && globalCoinScene && globalCoinCamera) {
        coinAnimationRunning = true;
        const animate = () => {
          if (!coinAnimationRunning) return;
          
          try {
            globalAnimationId = requestAnimationFrame(animate);
            
            if (globalCoinGroup) {
              if (!isDragging.current) {
                // 1. Apply Spin Boost (from click) with smoother, longer decay
                if (Math.abs(spinBoost.current) > 0.0005) {
                   globalCoinGroup.rotation.y += spinBoost.current;
                   // Exponential decay: 0.985 gives ~3x longer spin than 0.95
                   // This creates a smooth, natural deceleration like a real spinning coin
                   spinBoost.current *= 0.985;
                } else {
                   spinBoost.current = 0; // Clean stop to prevent micro-jitters
                }
                
                // 2. Apply drag momentum with realistic physics decay
                if (Math.abs(dragVelocity.current.x) > 0.0005 || Math.abs(dragVelocity.current.y) > 0.0005) {
                  globalCoinGroup.rotation.y += dragVelocity.current.x;
                  globalCoinGroup.rotation.x += dragVelocity.current.y;
                  // Friction-based decay: feels like the coin is spinning in air
                  dragVelocity.current.x *= 0.96;
                  dragVelocity.current.y *= 0.96;
                } else {
                  dragVelocity.current = { x: 0, y: 0 };
                }
                
                // 3. Apply Base Auto Spin (subtle continuous rotation for idle state)
                globalCoinGroup.rotation.y += 0.005;

                // 4. Smooth restoration of X axis with easing (float back to neutral position)
                const targetX = 0.2;
                const diff = targetX - globalCoinGroup.rotation.x;
                // Only restore when no active spinning/momentum to avoid conflicts
                if (Math.abs(spinBoost.current) < 0.001 && Math.abs(dragVelocity.current.y) < 0.001) {
                  // Subtle spring-like restoration
                  globalCoinGroup.rotation.x += diff * 0.015;
                }
              }
            }

            if (globalCoinRenderer && globalCoinScene && globalCoinCamera) {
              globalCoinRenderer.render(globalCoinScene, globalCoinCamera);
            }
          } catch (e: any) {
            // Silently handle errors in Cypress
            if (!isCypressEnvironment() && !isHeadlessBrowser()) {
              console.warn('Error in animation loop:', e);
            }
            coinAnimationRunning = false;
            setWebglSupported(false);
          }
        };

        animate();
      }
    } catch (e: any) {
      // Silently handle errors in Cypress
      if (!isCypressEnvironment() && !isHeadlessBrowser()) {
        console.warn('Failed to start animation loop:', e);
      }
      setWebglSupported(false);
    }

    return () => {
      coinInstanceCount--;
      if (coinInstanceCount <= 0) {
        // Only cleanup when last instance unmounts
        coinAnimationRunning = false;
        if (globalAnimationId !== null) {
          cancelAnimationFrame(globalAnimationId);
          globalAnimationId = null;
        }
        if (containerRef.current && globalCoinRenderer?.domElement) {
          try {
            containerRef.current.removeChild(globalCoinRenderer.domElement);
          } catch (e) {
            // Element may have been removed already
          }
        }
        // Don't dispose renderer/scene - keep for reuse
      } else if (containerRef.current && globalCoinRenderer?.domElement) {
        // Remove from this container but keep renderer alive
        try {
          containerRef.current.removeChild(globalCoinRenderer.domElement);
        } catch (e) {
          // Element may have been removed already
        }
      }
    };
  }, []);

  // --- Enhanced Event Handlers with Touch Support ---

  const handleMouseDown = (e: React.MouseEvent | React.TouchEvent) => {
    const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
    const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY;
    
    isDragging.current = true;
    previousMousePosition.current = { x: clientX, y: clientY };
    dragStartPos.current = { x: clientX, y: clientY };
    lastDragTime.current = Date.now();
    spinBoost.current = 0; // Stop existing boost
    dragVelocity.current = { x: 0, y: 0 }; // Reset momentum
  };

  const handleMouseMove = (e: React.MouseEvent | React.TouchEvent) => {
    if (isDragging.current && coinGroupRef.current) {
      const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
      const clientY = 'touches' in e ? e.touches[0].clientY : e.clientY;
      
      const deltaX = clientX - previousMousePosition.current.x;
      const deltaY = clientY - previousMousePosition.current.y;

      // Enhanced sensitivity for more responsive control
      const moveSpeed = 0.01; // Increased from 0.008
      const now = Date.now();
      const deltaTime = Math.max(now - lastDragTime.current, 1);

      // Apply immediate rotation
      const rotationY = deltaX * moveSpeed;
      const rotationX = deltaY * moveSpeed;
      
      if (globalCoinGroup) {
        globalCoinGroup.rotation.y += rotationY;
        globalCoinGroup.rotation.x += rotationX;
      }

      // Calculate velocity for momentum (pixels per millisecond scaled for good feel)
      // This preserves the "throw" motion when user releases
      dragVelocity.current = {
        x: (deltaX / deltaTime) * moveSpeed * 5,
        y: (deltaY / deltaTime) * moveSpeed * 5
      };

      previousMousePosition.current = { x: clientX, y: clientY };
      lastDragTime.current = now;
    }
  };

  const handleMouseUp = (e: React.MouseEvent | React.TouchEvent) => {
    const clientX = 'changedTouches' in e ? e.changedTouches[0].clientX : e.clientX;
    const clientY = 'changedTouches' in e ? e.changedTouches[0].clientY : e.clientY;
    
    isDragging.current = false;
    
    // Detect click vs drag by distance traveled
    const moveDist = Math.sqrt(
        Math.pow(clientX - dragStartPos.current.x, 2) + 
        Math.pow(clientY - dragStartPos.current.y, 2)
    );

    // If moved less than 5 pixels, treat as click -> Enhanced Spin Boost
    if (moveDist < 5) {
        // Powerful burst with slight randomization for dynamic, organic feel
        const randomFactor = 0.3 + Math.random() * 0.2; // Range: 0.8 to 1.2
        spinBoost.current = 0.5 * randomFactor; // Increased from 0.5 to 0.8
        
        // Optional: Add slight upward tilt on click for dynamic "pop" effect
        if (globalCoinGroup) {
          globalCoinGroup.rotation.x -= 0.1;
        }
    }
    // If it was a drag, momentum is already stored in dragVelocity and will continue
  };

  // Return fallback if WebGL is not supported
  if (webglSupported === false) {
    return <CoinFallback />;
  }

  // Return loading state while checking WebGL support
  if (webglSupported === null) {
    return <CoinFallback />;
  }

  return (
    <div 
      ref={containerRef} 
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={() => { 
        isDragging.current = false;
        // Keep momentum on mouse leave for better UX
      }}
      onTouchStart={handleMouseDown}
      onTouchMove={handleMouseMove}
      onTouchEnd={handleMouseUp}
      className="w-[300px] h-[300px] flex items-center justify-center cursor-grab active:cursor-grabbing touch-none"
      title="Click to spin, Drag to rotate!"
      style={{ touchAction: 'none' }} // Prevent scrolling on touch devices
    />
  );
});