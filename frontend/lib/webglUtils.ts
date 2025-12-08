/**
 * WebGL utility functions for detecting support and preventing crashes
 */

/**
 * Check if WebGL is supported and available
 */
export function isWebGLSupported(): boolean {
  try {
    // Check if running in Cypress or headless browser
    if (typeof navigator !== 'undefined') {
      // Detect Cypress
      if ((window as any).Cypress) {
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
        return false;
      }
    }

    // Test WebGL support
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    
    if (!gl) {
      return false;
    }

    // Test creating a shader (basic functionality check)
    const shader = gl.createShader(gl.VERTEX_SHADER);
    if (!shader) {
      return false;
    }
    
    gl.deleteShader(shader);
    return true;
  } catch (e) {
    return false;
  }
}

/**
 * Check if WebGL2 is supported
 */
export function isWebGL2Supported(): boolean {
  try {
    if (!isWebGLSupported()) {
      return false;
    }
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl2');
    return gl !== null;
  } catch (e) {
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

