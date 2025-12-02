// File header: Wallet connection modal component with MetaMask and manual address entry.
// Provides UI for connecting wallets via MetaMask extension or manual address input.

import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { X, Wallet, ExternalLink, Copy, Check, AlertCircle } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { cn } from '../lib/utils';

// Purpose: Declare window.ethereum type for TypeScript.
// Side effects: Extends Window interface.
declare global {
  interface Window {
    ethereum?: {
      isMetaMask?: boolean;
      request: (args: { method: string; params?: any[] }) => Promise<any>;
      on: (event: string, callback: (...args: any[]) => void) => void;
      removeListener: (event: string, callback: (...args: any[]) => void) => void;
      selectedAddress?: string;
      chainId?: string;
    };
  }
}

// Purpose: Check if MetaMask is installed and available.
// Returns: Boolean indicating if MetaMask is detected.
// Side effects: None (pure function).
const isMetaMaskInstalled = (): boolean => {
  if (typeof window === 'undefined') return false;
  return typeof window.ethereum !== 'undefined' && window.ethereum.isMetaMask === true;
};

// Purpose: Validate Ethereum address format.
// Params: address (string) - Address to validate.
// Returns: Object with isValid boolean and error message.
// Side effects: None (pure function).
const validateAddress = (address: string): { isValid: boolean; error?: string } => {
  if (!address || address.trim() === '') {
    return { isValid: false, error: 'wallet.addressRequired' };
  }

  const trimmed = address.trim();
  
  // Check format: 0x followed by 40 hex characters
  const ethereumAddressRegex = /^0x[a-fA-F0-9]{40}$/;
  
  if (!ethereumAddressRegex.test(trimmed)) {
    return { isValid: false, error: 'wallet.invalidAddress' };
  }

  return { isValid: true };
};

// Purpose: Copy text to clipboard.
// Params: text (string) - Text to copy.
// Returns: Promise that resolves when copied.
// Side effects: Copies to clipboard, may show browser permission prompt.
const copyToClipboard = async (text: string): Promise<boolean> => {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch (err) {
    // Fallback for older browsers
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.opacity = '0';
    document.body.appendChild(textArea);
    textArea.select();
    try {
      document.execCommand('copy');
      document.body.removeChild(textArea);
      return true;
    } catch {
      document.body.removeChild(textArea);
      return false;
    }
  }
};

// Purpose: Props interface for WalletConnectionModal component.
interface WalletConnectionModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConnectMetaMask: () => Promise<void>;
  onConnectManual: (address: string) => Promise<void>;
  isConnecting: boolean;
  error: string | null;
}

// Purpose: Wallet connection modal with MetaMask and manual entry options.
// Returns: JSX modal component.
// Side effects: Manages form state, validates input, handles connections.
export const WalletConnectionModal: React.FC<WalletConnectionModalProps> = ({
  isOpen,
  onClose,
  onConnectMetaMask,
  onConnectManual,
  isConnecting,
  error,
}) => {
  const { t } = useTranslation();
  const [manualAddress, setManualAddress] = useState('');
  const [addressError, setAddressError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [hasMetaMask, setHasMetaMask] = useState(false);
  const inputRef = React.useRef<HTMLInputElement>(null);

  // Purpose: Check MetaMask availability on mount and when modal opens.
  // Side effects: Updates hasMetaMask state.
  useEffect(() => {
    setHasMetaMask(isMetaMaskInstalled());
  }, [isOpen]);

  // Purpose: Focus input when modal opens and manual tab is active.
  // Side effects: Focuses input field.
  useEffect(() => {
    if (isOpen && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  // Purpose: Reset form state when modal closes.
  // Side effects: Clears input and errors.
  useEffect(() => {
    if (!isOpen) {
      setManualAddress('');
      setAddressError(null);
      setCopied(false);
    }
  }, [isOpen]);

  // Purpose: Handle manual address input change with validation.
  // Side effects: Updates input value and validates format.
  const handleAddressChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setManualAddress(value);
    
    if (value.trim() && addressError) {
      const validation = validateAddress(value);
      if (validation.isValid) {
        setAddressError(null);
      }
    }
  };

  // Purpose: Handle manual address submission.
  // Side effects: Validates address, calls onConnectManual if valid.
  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const validation = validateAddress(manualAddress);
    if (!validation.isValid) {
      setAddressError(validation.error || 'wallet.invalidAddress');
      return;
    }

    setAddressError(null);
    await onConnectManual(manualAddress.trim());
  };

  // Purpose: Handle MetaMask connection with error handling.
  // Side effects: Calls onConnectMetaMask, handles user rejection.
  const handleMetaMaskConnect = async () => {
    try {
      await onConnectMetaMask();
    } catch (err: any) {
      // Error handling is done in parent component
      console.error('MetaMask connection error:', err);
    }
  };

  // Purpose: Copy address to clipboard with visual feedback.
  // Side effects: Copies to clipboard, shows checkmark briefly.
  const handleCopyAddress = async (address: string) => {
    const success = await copyToClipboard(address);
    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  // Purpose: Portal target element for rendering modal outside DOM hierarchy.
  // Side effects: Creates portal container if it doesn't exist.
  const [portalContainer, setPortalContainer] = useState<HTMLElement | null>(null);

  useEffect(() => {
    if (isOpen) {
      // Purpose: Create or get portal container element.
      // Side effects: Creates div element and appends to document.body.
      let container = document.getElementById('modal-portal-root');
      if (!container) {
        container = document.createElement('div');
        container.id = 'modal-portal-root';
        container.style.position = 'fixed';
        container.style.top = '0';
        container.style.left = '0';
        container.style.width = '100%';
        container.style.height = '100%';
        container.style.pointerEvents = 'none';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
      }
      setPortalContainer(container);

      // Purpose: Prevent body scroll when modal is open.
      // Side effects: Adds/removes overflow-hidden class to body.
      document.body.style.overflow = 'hidden';

      return () => {
        document.body.style.overflow = '';
      };
    } else {
      setPortalContainer(null);
    }
  }, [isOpen]);

  if (!isOpen || !portalContainer) return null;

  const modalContent = (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
        aria-hidden="true"
        style={{ pointerEvents: 'auto', zIndex: 9999 }}
      />

      {/* Modal */}
      <div 
        className="fixed inset-0 flex items-center justify-center p-4"
        style={{ pointerEvents: 'none', zIndex: 10000 }}
      >
        <div
          className={cn(
            "relative w-full max-w-md bg-background-elevated border border-border rounded-2xl shadow-2xl",
            "animate-slide-up",
            "max-h-[90vh] overflow-y-auto"
          )}
          style={{ pointerEvents: 'auto' }}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-border">
            <h2 className="text-xl font-bold text-foreground">{t('wallet.connectWallet')}</h2>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-background-hover text-foreground-secondary hover:text-foreground transition-colors"
              aria-label={t('common.close')}
              disabled={isConnecting}
            >
              <X size={20} />
            </button>
          </div>

          {/* Content */}
          <div className="p-6 space-y-4">
            {/* Error Message */}
            {error && (
              <div className="flex items-center gap-2 p-3 bg-error/10 border border-error/20 rounded-lg text-error text-sm">
                <AlertCircle size={16} />
                <span>{t(error)}</span>
              </div>
            )}

            {/* Option A: MetaMask */}
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
                  <Wallet className="w-6 h-6 text-primary" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-foreground">{t('wallet.metaMask')}</h3>
                  <p className="text-sm text-foreground-secondary">{t('wallet.metaMaskSubtitle')}</p>
                </div>
              </div>

              {hasMetaMask ? (
                <button
                  onClick={handleMetaMaskConnect}
                  disabled={isConnecting}
                  className={cn(
                    "w-full px-4 py-3 rounded-lg font-medium text-sm transition-all",
                    "bg-primary hover:bg-primary-hover text-white",
                    "disabled:opacity-50 disabled:cursor-not-allowed",
                    "flex items-center justify-center gap-2"
                  )}
                >
                  {isConnecting ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      <span>{t('wallet.connecting')}</span>
                    </>
                  ) : (
                    <>
                      <Wallet size={18} />
                      <span>{t('wallet.connectWithMetaMask')}</span>
                    </>
                  )}
                </button>
              ) : (
                <div className="space-y-2">
                  <div className="p-3 bg-warning/10 border border-warning/20 rounded-lg text-warning text-sm">
                    {t('wallet.metaMaskNotFound')}
                  </div>
                  <a
                    href="https://metamask.io/download/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className={cn(
                      "w-full px-4 py-3 rounded-lg font-medium text-sm transition-all",
                      "bg-background-hover hover:bg-background-active border border-border",
                      "text-foreground flex items-center justify-center gap-2"
                    )}
                  >
                    <ExternalLink size={18} />
                    <span>{t('wallet.installMetaMask')}</span>
                  </a>
                </div>
              )}
            </div>

            {/* Divider */}
            <div className="flex items-center gap-4 py-2">
              <div className="flex-1 h-px bg-border" />
              <span className="text-xs text-foreground-tertiary uppercase">{t('common.or')}</span>
              <div className="flex-1 h-px bg-border" />
            </div>

            {/* Option B: Manual Entry */}
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-xl bg-background-hover border border-border flex items-center justify-center">
                  <Wallet className="w-6 h-6 text-foreground-secondary" />
                </div>
                <div className="flex-1">
                  <h3 className="font-semibold text-foreground">{t('wallet.manualEntry')}</h3>
                  <p className="text-sm text-foreground-secondary">{t('wallet.manualSubtitle')}</p>
                </div>
              </div>

              <form onSubmit={handleManualSubmit} className="space-y-2">
                <div>
                  <input
                    ref={inputRef}
                    type="text"
                    value={manualAddress}
                    onChange={handleAddressChange}
                    placeholder="0x..."
                    disabled={isConnecting}
                    className={cn(
                      "w-full px-4 py-3 rounded-lg",
                      "bg-background border",
                      addressError ? "border-error" : "border-border",
                      "text-foreground placeholder:text-foreground-tertiary",
                      "font-mono text-sm",
                      "focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2",
                      "focus:ring-offset-background-elevated",
                      "disabled:opacity-50 disabled:cursor-not-allowed"
                    )}
                  />
                  {addressError && (
                    <p className="mt-1 text-sm text-error">{t(addressError)}</p>
                  )}
                </div>
                <button
                  type="submit"
                  disabled={isConnecting || !manualAddress.trim()}
                  className={cn(
                    "w-full px-4 py-3 rounded-lg font-medium text-sm transition-all",
                    "bg-primary hover:bg-primary-hover text-white",
                    "disabled:opacity-50 disabled:cursor-not-allowed",
                    "flex items-center justify-center gap-2"
                  )}
                >
                  {isConnecting ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      <span>{t('wallet.connecting')}</span>
                    </>
                  ) : (
                    <span>{t('wallet.submitAddress')}</span>
                  )}
                </button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </>
  );

  return createPortal(modalContent, portalContainer);
};

