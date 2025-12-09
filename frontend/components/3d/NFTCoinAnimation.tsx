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
// These are reset on page load/refresh via window.beforeunload handler
let globalCoinRenderer: THREE.WebGLRenderer | null = null;
let globalCoinScene: THREE.Scene | null = null;
let globalCoinCamera: THREE.PerspectiveCamera | null = null;
let globalCoinGroup: THREE.Group | null = null;
let globalAnimationId: number | null = null;
let coinInstanceCount = 0;
let coinAnimationRunning = false;

// Reset all globals on page unload to ensure clean state on refresh
if (typeof window !== 'undefined') {
  const resetGlobals = () => {
    if (globalAnimationId !== null) {
      cancelAnimationFrame(globalAnimationId);
      globalAnimationId = null;
    }
    coinAnimationRunning = false;
    coinInstanceCount = 0;
    
    // Dispose WebGL resources
    if (globalCoinRenderer) {
      try {
        globalCoinRenderer.dispose();
        const canvas = globalCoinRenderer.domElement;
        if (canvas && canvas.parentNode) {
          canvas.parentNode.removeChild(canvas);
        }
      } catch (e) {
        // Ignore disposal errors
      }
      globalCoinRenderer = null;
    }
    
    // Dispose geometries and materials if needed
    if (globalCoinGroup) {
      globalCoinGroup.clear();
      globalCoinGroup = null;
    }
    
    globalCoinScene = null;
    globalCoinCamera = null;
  };
  
  // Reset on page unload/refresh
  window.addEventListener('beforeunload', resetGlobals);
  
  // Also reset on visibility change (some browsers preserve state)
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      // Page is being hidden, don't reset yet
    } else {
      // Page is visible again - ensure animation is running
      if (globalCoinRenderer && globalCoinScene && globalCoinCamera && !coinAnimationRunning) {
        // Animation will restart in useEffect
      }
    }
  });
}

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

    // Check WebGL support before initializing (cached, won't create multiple contexts)
    const webglSupported = isWebGLSupported();
    if (!webglSupported) {
      setWebglSupported(false);
      return;
    }
    
    setWebglSupported(true);
    
    // Wait for container to be ready - retry if not immediately available
    if (!containerRef.current) {
      // Try again on next frame
      const checkContainer = () => {
        if (containerRef.current) {
          initializeCoin();
        } else {
          requestAnimationFrame(checkContainer);
        }
      };
      requestAnimationFrame(checkContainer);
      return;
    }
    
    initializeCoin();
    
    return () => {
      coinInstanceCount--;
      if (coinInstanceCount <= 0) {
        // Only cleanup animation when last instance unmounts
        coinAnimationRunning = false;
        if (globalAnimationId !== null) {
          cancelAnimationFrame(globalAnimationId);
          globalAnimationId = null;
        }
        // Don't remove canvas or dispose renderer - keep for reuse on remount
        // The beforeunload handler will clean up on page refresh
      }
      // Don't remove canvas from container on unmount - it will be reused
    };
  }, []); // Empty deps - only run on mount
  
  const initializeCoin = React.useCallback(() => {
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
        // Don't create another test context - isWebGLSupported() already checked
        // WebGL support was verified earlier in the component

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
        
        const canvas = globalCoinRenderer.domElement;
        
        // Explicitly set canvas dimensions and styling
        canvas.style.width = '100%';
        canvas.style.height = '100%';
        canvas.style.display = 'block';
        canvas.style.position = 'absolute';
        canvas.style.top = '0';
        canvas.style.left = '0';
        canvas.style.pointerEvents = 'auto';
        canvas.style.outline = 'none';
        canvas.setAttribute('width', '300');
        canvas.setAttribute('height', '300');
        
        globalCoinRenderer.setSize(300, 300);
        globalCoinRenderer.setClearColor(0x000000, 0);
        globalCoinRenderer.setPixelRatio(Math.min(window.devicePixelRatio, isMobile ? 1 : 2));
        globalCoinRenderer.toneMapping = THREE.ACESFilmicToneMapping;
        globalCoinRenderer.toneMappingExposure = 3.0;
        
        // Ensure container is ready
        if (!containerRef.current) {
          throw new Error('Container ref is not available');
        }
        
        // Clear container before appending (always clear to ensure clean state on refresh)
        if (containerRef.current) {
          containerRef.current.innerHTML = '';
          containerRef.current.appendChild(canvas);
        }
        
        // Force initial render to ensure visibility immediately
        requestAnimationFrame(() => {
          if (globalCoinScene && globalCoinCamera && globalCoinRenderer) {
            globalCoinRenderer.render(globalCoinScene, globalCoinCamera);
          }
        });
      } else {
        // Reuse existing renderer - ensure canvas is visible and properly attached
        const canvas = globalCoinRenderer.domElement;
        canvas.style.width = '100%';
        canvas.style.height = '100%';
        canvas.style.display = 'block';
        canvas.style.position = 'absolute';
        canvas.style.top = '0';
        canvas.style.left = '0';
        canvas.style.pointerEvents = 'auto';
        canvas.style.outline = 'none';
        
        // Ensure canvas is in the container (might have been removed on refresh)
        if (containerRef.current) {
          // Check if canvas is already in container
          if (!containerRef.current.contains(canvas)) {
            containerRef.current.innerHTML = '';
            containerRef.current.appendChild(canvas);
          }
          // Force a render to ensure visibility
          requestAnimationFrame(() => {
            if (globalCoinScene && globalCoinCamera && globalCoinRenderer) {
              globalCoinRenderer.render(globalCoinScene, globalCoinCamera);
            }
          });
        }
      }
    } catch (e: any) {
      // Silently fail in Cypress - log only in development
      if (!isCypressEnvironment() && !isHeadlessBrowser()) {
        console.warn('WebGL initialization failed for coin animation, using fallback:', e);
      }
      setWebglSupported(false);
      return;
    }

    // --- Lighting (Intense for sparkles) --- (only add once)
    // Set up lighting BEFORE creating coin so materials render correctly
    if (globalCoinScene.children.filter(c => c.type === 'AmbientLight').length === 0) {
      const ambient = new THREE.AmbientLight(0xffffff, 0.8);
      globalCoinScene.add(ambient);

      const mainLight = new THREE.DirectionalLight(0xFFFFFF, 1.5);
      mainLight.position.set(5, 5, 10);
      globalCoinScene.add(mainLight);

      const warmLight = new THREE.PointLight(0xF7931A, 2, 50);
      warmLight.position.set(-5, -5, 10);
      globalCoinScene.add(warmLight);

      const rimLight = new THREE.PointLight(0xFFD700, 2, 50);
      rimLight.position.set(0, 5, -5);
      globalCoinScene.add(rimLight);
      
      // Additional fill light for better visibility
      const fillLight = new THREE.DirectionalLight(0xFFFFFF, 0.5);
      fillLight.position.set(-5, 0, 5);
      globalCoinScene.add(fillLight);
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


    // --- Enhanced Animation Loop with Physics-Based Motion ---
    // Always restart animation on mount/refresh to ensure it runs
    try {
      // Stop any existing animation first
      if (globalAnimationId !== null) {
        cancelAnimationFrame(globalAnimationId);
        globalAnimationId = null;
      }
      
      if (globalCoinRenderer && globalCoinScene && globalCoinCamera) {
        coinAnimationRunning = true;
        const animate = () => {
          // Check if we should continue animating
          if (!coinAnimationRunning || !globalCoinRenderer || !globalCoinScene || !globalCoinCamera) {
            coinAnimationRunning = false;
            return;
          }
          
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
              // Update camera aspect ratio if container size changes
              if (containerRef.current) {
                const containerWidth = containerRef.current.clientWidth || 300;
                const containerHeight = containerRef.current.clientHeight || 300;
                if (globalCoinCamera.aspect !== containerWidth / containerHeight) {
                  globalCoinCamera.aspect = containerWidth / containerHeight;
                  globalCoinCamera.updateProjectionMatrix();
                  globalCoinRenderer.setSize(containerWidth, containerHeight);
                }
              }
              
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
    // Note: Cleanup is handled in the first useEffect return function
  }, []); // Empty deps - initializeCoin is defined inside the first useEffect

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
      className="w-[300px] h-[300px] relative flex items-center justify-center cursor-grab active:cursor-grabbing touch-none"
      title="Click to spin, Drag to rotate!"
      style={{ 
        touchAction: 'none',
        overflow: 'hidden',
        position: 'relative',
        minWidth: '300px',
        minHeight: '300px'
      }}
    >
      {/* Canvas will be appended here by Three.js renderer */}
    </div>
  );
});