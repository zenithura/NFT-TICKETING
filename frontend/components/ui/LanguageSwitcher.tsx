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

  const dropdownContent = isOpen && position && (
    <>
      <div 
        className="fixed inset-0 z-40" 
        onClick={() => setIsOpen(false)}
        aria-hidden="true"
      />
      <div
        ref={dropdownRef}
        className="fixed w-48 bg-background-elevated border border-border rounded-lg shadow-xl z-50"
        style={{
          top: position.top !== undefined ? `${position.top}px` : undefined,
          bottom: position.bottom !== undefined ? `${position.bottom}px` : undefined,
          left: position.left !== undefined ? `${position.left}px` : undefined,
          right: position.right !== undefined ? `${position.right}px` : undefined,
        }}
      >
        <div className="p-1">
          <div className="px-3 py-2 text-[10px] uppercase font-bold text-foreground-tertiary tracking-wider">
            Language
          </div>
          {languages.map((lang) => (
            <button
              key={lang.code}
              onClick={() => changeLanguage(lang.code)}
              className={cn(
                "w-full text-left px-3 py-2 text-sm rounded hover:bg-background-hover flex items-center gap-2",
                i18n.language === lang.code 
                  ? "text-primary bg-primary/10" 
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
    </>
  );

  return (
    <div className="relative">
      <button
        ref={triggerRef}
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 rounded bg-background-elevated border border-border text-xs font-medium text-foreground-secondary hover:border-border-hover hover:text-foreground transition-colors"
        aria-label="Change language"
        aria-expanded={isOpen}
      >
        <Globe size={14} />
        <span className="hidden sm:inline">{currentLanguage.flag}</span>
        <span className="hidden md:inline">{currentLanguage.name}</span>
        <ChevronDown size={12} className={cn("transition-transform", isOpen && "rotate-180")} />
      </button>
      
      {isOpen && typeof document !== 'undefined' && createPortal(
        dropdownContent,
        document.body
      )}
    </div>
  );
};
