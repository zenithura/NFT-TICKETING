// File header: Language switcher component for changing between English and Azerbaijani.
// Provides dropdown menu to switch languages with visual indicators.

import React from 'react';
import { useTranslation } from 'react-i18next';
import { Globe, ChevronDown } from 'lucide-react';
import { cn } from '../../lib/utils';

export const LanguageSwitcher: React.FC = () => {
  const { i18n } = useTranslation();
  const [isOpen, setIsOpen] = React.useState(false);

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

  return (
    <div className="relative group">
      <button
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
      
      {isOpen && (
        <>
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => setIsOpen(false)}
            aria-hidden="true"
          />
          <div className="absolute right-0 top-full mt-2 w-48 bg-background-elevated border border-border rounded-lg shadow-xl z-50">
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
      )}
    </div>
  );
};
