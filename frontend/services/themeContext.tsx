// File header: Theme context provider for light/dark mode management.
// Provides theme state, persistence, and system preference detection.

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';

// Purpose: Define theme type (light, dark, or system).
type Theme = 'light' | 'dark' | 'system';

// Purpose: Define theme context type with theme state and toggle function.
interface ThemeContextType {
  theme: Theme;
  resolvedTheme: 'light' | 'dark';
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

// Purpose: Create theme context with undefined default.
const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

// Purpose: Storage key for theme preference in localStorage.
const THEME_STORAGE_KEY = 'theme-preference';

// Purpose: Get system color scheme preference.
// Returns: 'light' or 'dark' based on system preference.
// Side effects: None (pure function).
const getSystemTheme = (): 'light' | 'dark' => {
  if (typeof window === 'undefined') return 'dark';
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
};

// Purpose: Get resolved theme (user preference or system default).
// Returns: 'light' or 'dark' based on theme setting and system preference.
// Side effects: None (pure function).
const getResolvedTheme = (theme: Theme): 'light' | 'dark' => {
  if (theme === 'system') {
    return getSystemTheme();
  }
  return theme;
};

// Purpose: Apply theme to document root element.
// Side effects: Sets data-theme attribute and class on html element.
const applyTheme = (theme: 'light' | 'dark') => {
  if (typeof document === 'undefined') return;
  
  const html = document.documentElement;
  html.setAttribute('data-theme', theme);
  html.classList.remove('light', 'dark');
  html.classList.add(theme);
  
  // Update meta theme-color for mobile browsers
  const metaThemeColor = document.querySelector('meta[name="theme-color"]');
  if (metaThemeColor) {
    metaThemeColor.setAttribute('content', theme === 'dark' ? '#191919' : '#ffffff');
  }
};

// Purpose: Load theme from localStorage or return system default.
// Returns: Theme preference from storage or 'system'.
// Side effects: None (pure function).
const loadTheme = (): Theme => {
  if (typeof window === 'undefined') return 'system';
  
  try {
    const stored = localStorage.getItem(THEME_STORAGE_KEY);
    if (stored === 'light' || stored === 'dark' || stored === 'system') {
      return stored as Theme;
    }
  } catch (error) {
    console.warn('Failed to load theme from localStorage:', error);
  }
  
  return 'system';
};

// Purpose: Save theme preference to localStorage.
// Side effects: Stores theme in localStorage.
const saveTheme = (theme: Theme) => {
  if (typeof window === 'undefined') return;
  
  try {
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch (error) {
    console.warn('Failed to save theme to localStorage:', error);
  }
};

// Purpose: Theme provider component that manages theme state and persistence.
// Props: children - React children to wrap with theme context.
// Returns: JSX with ThemeContext.Provider.
// Side effects: Manages theme state, applies theme to document, listens to system preference changes.
export const ThemeProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [theme, setThemeState] = useState<Theme>(() => {
    // Initialize theme immediately to prevent flicker
    if (typeof window !== 'undefined') {
      const loadedTheme = loadTheme();
      const resolved = getResolvedTheme(loadedTheme);
      applyTheme(resolved);
      return loadedTheme;
    }
    return 'system';
  });

  const [resolvedTheme, setResolvedTheme] = useState<'light' | 'dark'>(() => {
    if (typeof window !== 'undefined') {
      return getResolvedTheme(theme);
    }
    return 'dark';
  });

  // Purpose: Update resolved theme when theme or system preference changes.
  // Side effects: Updates resolvedTheme state and applies theme to document.
  useEffect(() => {
    const resolved = getResolvedTheme(theme);
    setResolvedTheme(resolved);
    applyTheme(resolved);
    saveTheme(theme);
  }, [theme]);

  // Purpose: Listen to system preference changes when theme is 'system'.
  // Side effects: Updates resolved theme when system preference changes.
  useEffect(() => {
    if (theme !== 'system' || typeof window === 'undefined') return;

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    // Purpose: Handle system preference change.
    // Side effects: Updates resolved theme and applies it.
    const handleChange = (e: MediaQueryListEvent | MediaQueryList) => {
      const newResolved = e.matches ? 'dark' : 'light';
      setResolvedTheme(newResolved);
      applyTheme(newResolved);
    };

    // Modern browsers
    if (mediaQuery.addEventListener) {
      mediaQuery.addEventListener('change', handleChange);
      return () => mediaQuery.removeEventListener('change', handleChange);
    } else {
      // Fallback for older browsers
      mediaQuery.addListener(handleChange);
      return () => mediaQuery.removeListener(handleChange);
    }
  }, [theme]);

  // Purpose: Set theme and persist to localStorage.
  // Side effects: Updates theme state, which triggers useEffect to apply and save.
  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
  };

  // Purpose: Toggle between light and dark themes (skips system).
  // Side effects: Sets theme to opposite of current resolved theme.
  const toggleTheme = () => {
    const currentResolved = getResolvedTheme(theme);
    setTheme(currentResolved === 'dark' ? 'light' : 'dark');
  };

  return (
    <ThemeContext.Provider value={{ theme, resolvedTheme, setTheme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

// Purpose: Hook to access theme context.
// Returns: ThemeContextType with theme state and functions.
// Side effects: Throws error if used outside ThemeProvider.
export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

