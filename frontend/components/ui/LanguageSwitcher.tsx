// File header: Language switcher component for changing between English and Azerbaijani.
// Provides dropdown menu to switch languages with visual indicators.

import React, { useRef, useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { useTranslation } from 'react-i18next';
import { Globe, ChevronDown } from 'lucide-react';
import { cn } from '../../lib/utils';
import { calculateDropdownPosition } from '../../lib/viewportUtils';

export const LanguageSwitcher: React.FC = () => {
  const { i18n } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const [position, setPosition] = useState<{ top: number; left?: number; right?: number; side: string } | null>(null);

  // Purpose: Listen for close events from other navbar dropdowns.
  // Side effects: Closes language switcher when other dropdowns open.
  useEffect(() => {
    const handleCloseEvent = () => {
      setIsOpen(false);
    };
    window.addEventListener('closeLanguageSwitcher', handleCloseEvent);
    return () => window.removeEventListener('closeLanguageSwitcher', handleCloseEvent);
  }, []);

  const languages = [
    { code: 'en', name: 'English', flag: '🇬🇧' },
    { code: 'az', name: 'Azərbaycan', flag: '🇦🇿' },
  ];

  const currentLanguage = languages.find(lang => lang.code === i18n.language) || languages[0];

  const changeLanguage = (lng: string) => {
    i18n.changeLanguage(lng);
    setIsOpen(false);
    // Update HTML lang attribute
    document.documentElement.lang = lng;
  };

  // Purpose: Calculate dropdown position when opened or window resized.
  // Side effects: Updates position state based on viewport boundaries.
  useEffect(() => {
    if (isOpen && triggerRef.current && dropdownRef.current) {
      const triggerRect = triggerRef.current.getBoundingClientRect();
      const dropdownWidth = 192; // w-48 = 12rem = 192px
      const dropdownHeight = dropdownRef.current.offsetHeight || 200; // Estimate if not rendered yet
      
      const pos = calculateDropdownPosition(triggerRect, dropdownWidth, dropdownHeight, 8);
      setPosition(pos);

      // Purpose: Recalculate position on window resize or scroll.
      // Side effects: Updates position when viewport changes.
      const handleResize = () => {
        if (triggerRef.current && dropdownRef.current) {
          const newTriggerRect = triggerRef.current.getBoundingClientRect();
          const newDropdownHeight = dropdownRef.current.offsetHeight || 200;
          const newPos = calculateDropdownPosition(newTriggerRect, dropdownWidth, newDropdownHeight, 8);
          setPosition(newPos);
        }
      };

      window.addEventListener('resize', handleResize);
      window.addEventListener('scroll', handleResize, true);

      return () => {
        window.removeEventListener('resize', handleResize);
        window.removeEventListener('scroll', handleResize, true);
      };
    } else {
      setPosition(null);
    }
  }, [isOpen]);

  // Purpose: Close dropdown when clicking outside (desktop only, mobile uses backdrop).
  // CRITICAL: Only closes if click is outside the dropdown, its trigger, and other navbar buttons.
  // This prevents closing when clicking other navbar buttons.
  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      
      // CRITICAL: Check trigger button first - must return early to prevent interference
      if (triggerRef.current && (triggerRef.current === target || triggerRef.current.contains(target))) {
        return; // Don't close when clicking the trigger button
      }
      
      // Don't close if clicking inside the dropdown menu
      if (dropdownRef.current?.contains(target)) {
        return;
      }
      
      // Don't close if clicking on any navbar button (including triggers for other dropdowns)
      // Check multiple ways to ensure we catch all navbar buttons
      const navButton = target.closest('nav button, nav a, button[aria-expanded], button[aria-haspopup]');
      if (navButton && navButton !== triggerRef.current) {
        return; // Let the button's onClick handler manage the state
      }
      
      // Don't close if clicking on other dropdown menus
      if (target.closest('[role="menu"]')) {
        return;
      }
      
      // Don't close if clicking on ThemeToggle or other navbar controls
      if (target.closest('[aria-label*="theme" i]')) {
        return;
      }
      
      // Don't close if clicking anywhere in the navbar
      if (target.closest('nav')) {
        return;
      }
      
      // Only close if clicking completely outside navbar area
      setIsOpen(false);
    };

    // Use mousedown in bubble phase with delay to ensure button handlers run first
    const timeoutId = setTimeout(() => {
      document.addEventListener('mousedown', handleClickOutside);
    }, 10);

    return () => {
      clearTimeout(timeoutId);
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  // Calculate default position if position is not yet set
  const getDefaultPosition = () => {
    if (triggerRef.current) {
      const triggerRect = triggerRef.current.getBoundingClientRect();
      return {
        top: triggerRect.bottom + 8,
        left: triggerRect.left,
        side: 'bottom' as const
      };
    }
    return null;
  };

  const currentPosition = position || getDefaultPosition();

  // Purpose: Handle button click - toggle dropdown state.
  // CRITICAL: Must run before click-outside handler to prevent interference.
  const handleButtonClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    // Don't use preventDefault() as it can interfere with button behavior
    const newState = !isOpen;
    setIsOpen(newState);
    // Close other navbar dropdowns when opening this one
    if (newState) {
      window.dispatchEvent(new CustomEvent('closeOtherDropdowns'));
    }
  };

  return (
    <div className="relative">
      <button
        ref={triggerRef}
        onClick={handleButtonClick}
        onMouseDown={(e) => {
          // Prevent click-outside handler from interfering
          e.stopPropagation();
        }}
        onMouseEnter={() => {
          // Open on hover for better UX (only if no other dropdown is interfering)
          // Check if any other navbar dropdown is open
          const otherDropdowns = document.querySelectorAll('[role="menu"]:not([aria-label*="Language"])');
          if (otherDropdowns.length === 0) {
            setIsOpen(true);
          }
        }}
        onMouseLeave={(e) => {
          // Don't close on mouse leave - let click-outside handler manage closing
          // This prevents dropdown from closing when moving mouse to dropdown
        }}
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-background-elevated border border-border text-xs font-medium text-foreground-secondary hover:border-border-hover hover:text-foreground transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
        aria-label="Change language"
        aria-expanded={isOpen}
        aria-haspopup="true"
        type="button"
      >
        <Globe size={14} />
        <span className="hidden sm:inline">{currentLanguage.flag}</span>
        <span className="hidden md:inline">{currentLanguage.name}</span>
        <ChevronDown size={12} className={cn("transition-transform duration-200", isOpen && "rotate-180")} />
      </button>
      
      {isOpen && typeof document !== 'undefined' && currentPosition && createPortal(
        <>
          {/* Backdrop for mobile only - prevents covering other buttons on desktop */}
          <div 
            className="fixed inset-0 z-[55] md:hidden bg-black/20 backdrop-blur-sm pointer-events-auto" 
            onClick={(e) => {
              e.stopPropagation();
              setIsOpen(false);
            }}
            aria-hidden="true"
          />
          {/* Dropdown Menu - positioned and visible */}
          <div
            ref={dropdownRef}
            role="menu"
            aria-label="Language selection"
            className="fixed w-48 bg-background-elevated border border-border rounded-lg shadow-xl z-[60] animate-fade-in"
            style={{
              top: currentPosition.top !== undefined ? `${currentPosition.top}px` : undefined,
              bottom: currentPosition.bottom !== undefined ? `${currentPosition.bottom}px` : undefined,
              left: currentPosition.left !== undefined ? `${currentPosition.left}px` : undefined,
              right: currentPosition.right !== undefined ? `${currentPosition.right}px` : undefined,
              visibility: 'visible',
              opacity: 1,
              display: 'block',
            }}
            onClick={(e) => {
              // Prevent clicks inside dropdown from closing it
              e.stopPropagation();
            }}
            onMouseEnter={() => setIsOpen(true)}
            onMouseLeave={(e) => {
              // Only close if mouse is not moving back to trigger button
              const relatedTarget = e.relatedTarget as HTMLElement;
              if (!relatedTarget?.closest('button[aria-label*="language" i]')) {
                // Small delay to allow moving between dropdown and trigger
                setTimeout(() => {
                  if (!document.querySelector('[role="menu"][aria-label="Language selection"]:hover') && 
                      !document.querySelector('button[aria-label*="language" i]:hover')) {
                    setIsOpen(false);
                  }
                }, 100);
              }
            }}
          >
            <div className="p-1">
              <div className="px-3 py-2 text-[10px] uppercase font-bold text-foreground-tertiary tracking-wider border-b border-border">
                Language
              </div>
              {languages.map((lang) => (
                <button
                  key={lang.code}
                  onClick={(e) => {
                    e.stopPropagation();
                    changeLanguage(lang.code);
                  }}
                  className={cn(
                    "w-full text-left px-3 py-2 text-sm rounded-lg hover:bg-background-hover flex items-center gap-2 transition-colors duration-150 focus:outline-none focus:bg-background-hover",
                    i18n.language === lang.code 
                      ? "text-primary bg-primary/10 font-medium" 
                      : "text-foreground-secondary"
                  )}
                >
                  <span>{lang.flag}</span>
                  <span>{lang.name}</span>
                  {i18n.language === lang.code && (
                    <span className="ml-auto text-primary">✓</span>
                  )}
                </button>
              ))}
            </div>
          </div>
        </>,
        document.body
      )}
    </div>
  );
};
