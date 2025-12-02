// File header: Theme toggle component with sun/moon icons.
// Provides accessible theme switching with smooth animations.

import React from 'react';
import { Sun, Moon } from 'lucide-react';
import { useTheme } from '../../services/themeContext';
import { useTranslation } from 'react-i18next';
import { cn } from '../../lib/utils';

// Purpose: Theme toggle button component with icon animation.
// Returns: JSX button element with sun/moon icons.
// Side effects: Toggles theme on click, updates localStorage.
export const ThemeToggle: React.FC<{ className?: string }> = ({ className }) => {
  const { resolvedTheme, toggleTheme } = useTheme();
  const { t } = useTranslation();
  const [isAnimating, setIsAnimating] = React.useState(false);

  // Purpose: Handle theme toggle with animation.
  // Side effects: Toggles theme, triggers animation state.
  const handleToggle = () => {
    setIsAnimating(true);
    toggleTheme();
    setTimeout(() => setIsAnimating(false), 300);
  };

  const isDark = resolvedTheme === 'dark';
  const label = isDark ? t('theme.lightMode') : t('theme.darkMode');
  const ariaLabel = t('theme.toggleTheme', { mode: label });

  return (
    <button
      onClick={handleToggle}
      className={cn(
        "relative flex items-center justify-center w-10 h-10 rounded-lg",
        "bg-background-elevated border border-border",
        "hover:bg-background-hover hover:border-border-hover",
        "text-foreground-secondary hover:text-foreground",
        "transition-all duration-200",
        "focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2",
        "focus:ring-offset-background",
        className
      )}
      aria-label={ariaLabel}
      title={ariaLabel}
      type="button"
    >
      {/* Purpose: Sun icon for light mode (shown when dark mode is active). */}
      <Sun
        className={cn(
          "absolute w-5 h-5 transition-all duration-300",
          isDark
            ? "opacity-100 rotate-0 scale-100"
            : "opacity-0 rotate-90 scale-0",
          isAnimating && "animate-pulse"
        )}
        aria-hidden="true"
      />
      
      {/* Purpose: Moon icon for dark mode (shown when light mode is active). */}
      <Moon
        className={cn(
          "absolute w-5 h-5 transition-all duration-300",
          !isDark
            ? "opacity-100 rotate-0 scale-100"
            : "opacity-0 -rotate-90 scale-0",
          isAnimating && "animate-pulse"
        )}
        aria-hidden="true"
      />
    </button>
  );
};

