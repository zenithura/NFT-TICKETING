// File header: Application entry point with i18n initialization.
// Initializes React application and internationalization support.

import React from 'react';
import ReactDOM from 'react-dom/client';
import './i18n'; // Initialize i18n before App
import App from './App';

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error("Could not find root element to mount to");
}

const root = ReactDOM.createRoot(rootElement);
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);