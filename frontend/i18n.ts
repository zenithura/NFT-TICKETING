// File header: i18n configuration for multilingual support (English and Azerbaijani).
// Sets up react-i18next with language detection and translation resources.

import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import LanguageDetector from 'i18next-browser-languagedetector';

import enTranslation from './locales/en/translation.json';
import azTranslation from './locales/az/translation.json';

// Purpose: Initialize i18n with language detection and translation resources.
// Side effects: Configures i18n, sets default language, enables language detection.
i18n
  .use(LanguageDetector) // Detects user's browser language
  .use(initReactI18next) // Passes i18n down to react-i18next
  .init({
    resources: {
      en: {
        translation: enTranslation,
      },
      az: {
        translation: azTranslation,
      },
    },
    fallbackLng: 'en', // Default to English if translation missing
    debug: false, // Set to true for development debugging
    
    interpolation: {
      escapeValue: false, // React already escapes values
    },
    
    detection: {
      // Order of language detection
      order: ['localStorage', 'navigator', 'htmlTag'],
      // Cache user language preference
      caches: ['localStorage'],
      // Look for language in localStorage key
      lookupLocalStorage: 'i18nextLng',
    },
  });

// Purpose: Update HTML lang attribute when language changes.
// Side effects: Updates document.documentElement.lang attribute.
i18n.on('languageChanged', (lng) => {
  document.documentElement.lang = lng;
  // Update HTML direction for RTL languages if needed (Azerbaijani is LTR)
  document.documentElement.dir = 'ltr';
});

// Set initial HTML lang attribute
document.documentElement.lang = i18n.language;

export default i18n;

