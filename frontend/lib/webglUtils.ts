/**
 * WebGL utility functions for detecting support and preventing crashes
 */

// Cache WebGL support check to avoid creating multiple contexts
let webglSupportCache: boolean | null = null;

/**
 * Check if WebGL is supported and available
 * Caches result to prevent creating multiple test contexts
 */
export function isWebGLSupported(): boolean {
  // Return cached result if available
  if (webglSupportCache !== null) {
    return webglSupportCache;
  }

  try {
    // Check if running in Cypress or headless browser
    if (typeof navigator !== 'undefined') {
      // Detect Cypress
      if ((window as any).Cypress) {
        webglSupportCache = false;
        return false;
      }
      // Detect headless browsers (common indicators)
      const userAgent = navigator.userAgent.toLowerCase();
      if (
        userAgent.includes('headless') ||
        userAgent.includes('phantom') ||
        userAgent.includes('selenium') ||
        userAgent.includes('webdriver')
      ) {
        webglSupportCache = false;
        return false;
      }
    }

    // Test WebGL support with proper cleanup
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    
    if (!gl) {
      webglSupportCache = false;
      return false;
    }

    // Test creating a shader (basic functionality check)
    const shader = gl.createShader(gl.VERTEX_SHADER);
    if (!shader) {
      // Properly clean up context
      const extension = gl.getExtension('WEBGL_lose_context');
      if (extension) {
        extension.loseContext();
      }
      webglSupportCache = false;
      return false;
    }
    
    // Clean up shader
    gl.deleteShader(shader);
    
    // Properly clean up test context to prevent context leak
    const extension = gl.getExtension('WEBGL_lose_context');
    if (extension) {
      extension.loseContext();
    }
    
    // Cache successful result
    webglSupportCache = true;
    return true;
  } catch (e) {
    webglSupportCache = false;
    return false;
  }
}

// Cache WebGL2 support check
let webgl2SupportCache: boolean | null = null;

/**
 * Check if WebGL2 is supported
 * Caches result to prevent creating multiple test contexts
 */
export function isWebGL2Supported(): boolean {
  // Return cached result if available
  if (webgl2SupportCache !== null) {
    return webgl2SupportCache;
  }

  try {
    if (!isWebGLSupported()) {
      webgl2SupportCache = false;
      return false;
    }
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl2');
    
    if (gl) {
      // Properly clean up test context
      const extension = gl.getExtension('WEBGL_lose_context');
      if (extension) {
        extension.loseContext();
      }
      webgl2SupportCache = true;
      return true;
    }
    
    webgl2SupportCache = false;
    return false;
  } catch (e) {
    webgl2SupportCache = false;
    return false;
  }
}

/**
 * Detect if running in Cypress test environment
 */
export function isCypressEnvironment(): boolean {
  return typeof window !== 'undefined' && !!(window as any).Cypress;
}

/**
 * Detect if running in headless browser environment
 */
export function isHeadlessBrowser(): boolean {
  if (typeof navigator === 'undefined') {
    return false;
  }
  
  const userAgent = navigator.userAgent.toLowerCase();
  return (
    userAgent.includes('headless') ||
    userAgent.includes('phantom') ||
    userAgent.includes('selenium') ||
    userAgent.includes('webdriver') ||
    navigator.webdriver === true
  );
}

