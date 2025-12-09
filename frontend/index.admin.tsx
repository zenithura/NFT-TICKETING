import React from 'react';
import ReactDOM from 'react-dom/client';
import { HashRouter } from 'react-router-dom';
import { I18nextProvider } from 'react-i18next';
import { Toaster } from 'react-hot-toast';
import i18n from './i18n';
import AdminApp from './AdminApp';
import { ErrorBoundary } from './components/ErrorBoundary';
import { ThemeProvider } from './services/themeContext';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <ThemeProvider>
        <I18nextProvider i18n={i18n}>
          <HashRouter>
            <AdminApp />
            <Toaster
              position="top-right"
              toastOptions={{
                duration: 3500,
                style: {
                  borderRadius: '12px',
                  background: 'var(--color-background-elevated)',
                  color: 'var(--color-foreground)',
                  border: '1px solid var(--color-border)',
                  padding: '12px 16px',
                },
              }}
            />
          </HashRouter>
        </I18nextProvider>
      </ThemeProvider>
    </ErrorBoundary>
  </React.StrictMode>
);

