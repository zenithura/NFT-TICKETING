// File header: Navigation bar component with language switcher and wallet connection.
// Provides main navigation links, role-based menu, and language selection.

import React, { useRef, useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Wallet, Menu, X, ChevronDown, Shield, Users, Ticket, ScanLine, Zap, LogIn, LogOut, User, Copy } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useWeb3 } from '../../services/web3Context';
import { useAuth } from '../../services/authContext';
import { UserRole } from '../../types';
import { cn, formatAddress } from '../../lib/utils';
import { calculateDropdownPosition } from '../../lib/viewportUtils';
import { LanguageSwitcher } from './LanguageSwitcher';
import { ThemeToggle } from './ThemeToggle';
import { WalletConnectionModal } from '../WalletConnectionModal';

export const Navbar: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { isConnected, address, connectMetaMask, connectManual, disconnect, balance, userRole, setUserRole, isConnecting, error } = useWeb3();
  const { isAuthenticated, user, logout } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isWalletModalOpen, setIsWalletModalOpen] = useState(false);
  const [isRoleMenuOpen, setIsRoleMenuOpen] = useState(false);
  const [isWalletMenuOpen, setIsWalletMenuOpen] = useState(false);
  const location = useLocation();
  
  const roleTriggerRef = useRef<HTMLButtonElement>(null);
  const walletTriggerRef = useRef<HTMLButtonElement>(null);
  const roleMenuRef = useRef<HTMLDivElement>(null);
  const walletMenuRef = useRef<HTMLDivElement>(null);
  const [roleMenuPosition, setRoleMenuPosition] = useState<{ top: number; left?: number; right?: number; side: string } | null>(null);
  const [walletMenuPosition, setWalletMenuPosition] = useState<{ top: number; left?: number; right?: number; side: string } | null>(null);

  const isActive = (path: string) => location.pathname === path;

  // Purpose: Calculate dropdown positions when opened.
  // Side effects: Updates position state based on viewport boundaries.
  useEffect(() => {
    if (isRoleMenuOpen && roleTriggerRef.current && roleMenuRef.current) {
      const triggerRect = roleTriggerRef.current.getBoundingClientRect();
      const menuWidth = 192; // w-48
      const menuHeight = roleMenuRef.current.offsetHeight || 200;
      const pos = calculateDropdownPosition(triggerRect, menuWidth, menuHeight, 8);
      setRoleMenuPosition(pos);

      const handleResize = () => {
        if (roleTriggerRef.current && roleMenuRef.current) {
          const newTriggerRect = roleTriggerRef.current.getBoundingClientRect();
          const newMenuHeight = roleMenuRef.current.offsetHeight || 200;
          const newPos = calculateDropdownPosition(newTriggerRect, menuWidth, newMenuHeight, 8);
          setRoleMenuPosition(newPos);
        }
      };

      window.addEventListener('resize', handleResize);
      window.addEventListener('scroll', handleResize, true);
      return () => {
        window.removeEventListener('resize', handleResize);
        window.removeEventListener('scroll', handleResize, true);
      };
    } else {
      setRoleMenuPosition(null);
    }
  }, [isRoleMenuOpen]);

  useEffect(() => {
    if (isWalletMenuOpen && walletTriggerRef.current && walletMenuRef.current) {
      const triggerRect = walletTriggerRef.current.getBoundingClientRect();
      const menuWidth = 192; // w-48
      const menuHeight = walletMenuRef.current.offsetHeight || 100;
      const pos = calculateDropdownPosition(triggerRect, menuWidth, menuHeight, 8);
      setWalletMenuPosition(pos);

      const handleResize = () => {
        if (walletTriggerRef.current && walletMenuRef.current) {
          const newTriggerRect = walletTriggerRef.current.getBoundingClientRect();
          const newMenuHeight = walletMenuRef.current.offsetHeight || 100;
          const newPos = calculateDropdownPosition(newTriggerRect, menuWidth, newMenuHeight, 8);
          setWalletMenuPosition(newPos);
        }
      };

      window.addEventListener('resize', handleResize);
      window.addEventListener('scroll', handleResize, true);
      return () => {
        window.removeEventListener('resize', handleResize);
        window.removeEventListener('scroll', handleResize, true);
      };
    } else {
      setWalletMenuPosition(null);
    }
  }, [isWalletMenuOpen]);

  const getLinks = () => {
    const common = [{ path: '/', label: t('nav.marketplace') }];
    switch (userRole) {
      case UserRole.ORGANIZER:
        return [...common, { path: '/dashboard', label: t('nav.dashboard') }, { path: '/create-event', label: t('nav.createEvent') }];
      case UserRole.RESELLER:
        return [...common, { path: '/dashboard', label: t('nav.resalePortal') }];
      case UserRole.SCANNER:
        return [{ path: '/scanner', label: t('nav.launchScanner') }];
      case UserRole.ADMIN:
        return [...common, { path: '/admin', label: t('nav.adminPanel') }];
      case UserRole.BUYER:
      default:
        return [...common, { path: '/dashboard', label: t('nav.myTickets') }];
    }
  };

  const links = getLinks();

  return (
    <nav className="glass sticky top-0 z-50 border-b border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Logo */}
          <div className="flex items-center gap-8">
            <Link to="/" className="flex items-center gap-2 group">
              <div className="w-8 h-8 bg-primary/10 rounded flex items-center justify-center border border-primary/20 group-hover:border-primary/50 transition-colors">
                <Zap size={16} className="text-primary" />
              </div>
              <span className="font-semibold text-lg text-foreground tracking-tight">NFTix</span>
            </Link>
            
            {/* Desktop Links */}
            <div className="hidden md:flex items-center gap-1">
              {links.map((link) => (
                <Link 
                  key={link.path}
                  to={link.path} 
                  className={cn(
                    "px-3 py-1.5 rounded text-sm font-medium transition-all",
                    isActive(link.path) 
                      ? "bg-background-active text-foreground" 
                      : "text-foreground-secondary hover:text-foreground hover:bg-background-hover"
                  )}
                >
                  {link.label}
                </Link>
              ))}
            </div>
          </div>

          {/* Right Side */}
          <div className="hidden md:flex items-center gap-4">
            {/* Theme Toggle */}
            <ThemeToggle />
            
            {/* Language Switcher */}
            <LanguageSwitcher />
            
            {/* Authentication Buttons */}
            {isAuthenticated ? (
              <div className="flex items-center gap-3">
                <div className="text-sm text-foreground-secondary">
                  {user?.email || user?.username}
                </div>
                <button
                  onClick={async () => {
                    await logout();
                    navigate('/');
                  }}
                  className="flex items-center gap-2 px-3 py-1.5 rounded bg-background-elevated border border-border text-sm font-medium text-foreground-secondary hover:border-border-hover hover:text-foreground transition-colors"
                >
                  <LogOut size={14} />
                  {t('auth.logout')}
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  to="/login"
                  className="flex items-center gap-2 px-3 py-1.5 rounded text-sm font-medium text-foreground-secondary hover:text-foreground transition-colors"
                >
                  <LogIn size={14} />
                  {t('auth.loginButton')}
                </Link>
                <Link
                  to="/register"
                  className="flex items-center gap-2 px-3 py-1.5 rounded bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
                >
                  {t('auth.registerButton')}
                </Link>
              </div>
            )}
            
            {isConnected ? (
              <>
                {/* Role Switcher (Demo) */}
                <div className="relative">
                  <button
                    ref={roleTriggerRef}
                    onMouseEnter={() => setIsRoleMenuOpen(true)}
                    onMouseLeave={() => setIsRoleMenuOpen(false)}
                    className="flex items-center gap-2 px-3 py-1.5 rounded bg-background-elevated border border-border text-xs font-medium text-foreground-secondary hover:border-border-hover hover:text-foreground transition-colors"
                  >
                    {userRole === UserRole.ADMIN && <Shield size={12} className="text-error" />}
                    {userRole === UserRole.ORGANIZER && <Users size={12} className="text-primary" />}
                    {userRole === UserRole.BUYER && <Ticket size={12} className="text-success" />}
                    {t(`roles.${userRole}`)}
                    <ChevronDown size={12} />
                  </button>
                  {isRoleMenuOpen && roleMenuPosition && typeof document !== 'undefined' && createPortal(
                    <div
                      onMouseEnter={() => setIsRoleMenuOpen(true)}
                      onMouseLeave={() => setIsRoleMenuOpen(false)}
                      ref={roleMenuRef}
                      className="fixed w-48 bg-background-elevated border border-border rounded-lg shadow-xl z-50"
                      style={{
                        top: roleMenuPosition.top !== undefined ? `${roleMenuPosition.top}px` : undefined,
                        bottom: roleMenuPosition.bottom !== undefined ? `${roleMenuPosition.bottom}px` : undefined,
                        left: roleMenuPosition.left !== undefined ? `${roleMenuPosition.left}px` : undefined,
                        right: roleMenuPosition.right !== undefined ? `${roleMenuPosition.right}px` : undefined,
                      }}
                    >
                      <div className="p-1">
                        <div className="px-3 py-2 text-[10px] uppercase font-bold text-foreground-tertiary tracking-wider">{t('nav.switchView')}</div>
                        {Object.values(UserRole).map((role) => (
                          <button
                            key={role}
                            onClick={() => {
                              setUserRole(role);
                              setIsRoleMenuOpen(false);
                            }}
                            className={cn(
                              "w-full text-left px-3 py-2 text-sm rounded hover:bg-background-hover flex items-center gap-2",
                              userRole === role ? "text-primary bg-primary/10" : "text-foreground-secondary"
                            )}
                          >
                            {t(`roles.${role}`)}
                          </button>
                        ))}
                      </div>
                    </div>,
                    document.body
                  )}
                </div>

                {/* Wallet Badge */}
                <div className="flex items-center gap-3 pl-4 border-l border-border">
                  <div className="text-sm font-mono text-foreground-secondary">
                    {balance} <span className="text-foreground-tertiary">ETH</span>
                  </div>
                  <div className="relative">
                    <button
                      ref={walletTriggerRef}
                      onMouseEnter={() => setIsWalletMenuOpen(true)}
                      onMouseLeave={() => setIsWalletMenuOpen(false)}
                      className="flex items-center gap-2 bg-background-hover border border-border px-3 py-1.5 rounded text-sm font-mono text-foreground hover:border-border-hover transition-colors"
                    >
                      <div className="w-2 h-2 rounded-full bg-success animate-pulse-slow" />
                      {formatAddress(address || '')}
                    </button>
                    {isWalletMenuOpen && walletMenuPosition && typeof document !== 'undefined' && createPortal(
                      <div
                        onMouseEnter={() => setIsWalletMenuOpen(true)}
                        onMouseLeave={() => setIsWalletMenuOpen(false)}
                        ref={walletMenuRef}
                        className="fixed w-48 bg-background-elevated border border-border rounded-lg shadow-xl z-50 p-1"
                        style={{
                          top: walletMenuPosition.top !== undefined ? `${walletMenuPosition.top}px` : undefined,
                          bottom: walletMenuPosition.bottom !== undefined ? `${walletMenuPosition.bottom}px` : undefined,
                          left: walletMenuPosition.left !== undefined ? `${walletMenuPosition.left}px` : undefined,
                          right: walletMenuPosition.right !== undefined ? `${walletMenuPosition.right}px` : undefined,
                        }}
                      >
                        <button 
                          onClick={async () => {
                            if (address) {
                              try {
                                await navigator.clipboard.writeText(address);
                                setIsWalletMenuOpen(false);
                                // Could show toast notification here
                              } catch (err) {
                                console.error('Failed to copy address:', err);
                              }
                            }
                          }}
                          className="w-full text-left px-3 py-2 text-sm text-foreground-secondary hover:bg-background-hover rounded transition-colors flex items-center gap-2"
                        >
                          <Copy size={14} />
                          {t('wallet.copyAddress')}
                        </button>
                        <button 
                          onClick={() => {
                            disconnect();
                            setIsWalletMenuOpen(false);
                          }} 
                          className="w-full text-left px-3 py-2 text-sm text-error hover:bg-error/10 rounded transition-colors flex items-center gap-2"
                        >
                          <LogOut size={14} />
                          {t('nav.disconnect')}
                        </button>
                      </div>,
                      document.body
                    )}
                  </div>
                </div>
              </>
            ) : (
              <button
                onClick={() => setIsWalletModalOpen(true)}
                className="flex items-center gap-2 bg-primary hover:bg-primary-hover text-white px-4 py-2 rounded font-medium text-sm transition-all hover:-translate-y-0.5 shadow-lg shadow-primary/20"
              >
                <Wallet size={16} />
                {t('nav.connectWallet')}
              </button>
            )}
          </div>

          {/* Mobile Toggle */}
          <div className="md:hidden flex items-center">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="p-2 rounded text-foreground-secondary hover:bg-background-hover hover:text-foreground"
            >
              {isMenuOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      {isMenuOpen && (
        <div className="md:hidden bg-background-elevated border-b border-border animate-fade-in">
          <div className="px-4 pt-2 pb-4 space-y-1">
            {links.map((link) => (
              <Link 
                key={link.path}
                to={link.path} 
                onClick={() => setIsMenuOpen(false)} 
                className={cn(
                  "block px-3 py-3 rounded-lg text-base font-medium",
                  isActive(link.path) ? "bg-background-active text-foreground" : "text-foreground-secondary"
                )}
              >
                {link.label}
              </Link>
            ))}
            <div className="pt-4 border-t border-border mt-4 space-y-1">
              {/* Mobile Theme Toggle */}
              <div className="px-3 py-2 flex items-center justify-between">
                <span className="text-sm text-foreground-secondary">{t('theme.theme')}</span>
                <ThemeToggle />
              </div>
              
              {isAuthenticated ? (
                <>
                  <div className="px-3 py-2 text-sm text-foreground-secondary">
                    {user?.email || user?.username}
                  </div>
                  <button 
                    onClick={async () => {
                      await logout();
                      setIsMenuOpen(false);
                      navigate('/');
                    }} 
                    className="w-full text-left text-error px-3 py-3 font-medium flex items-center gap-2"
                  >
                    <LogOut size={16} />
                    {t('auth.logout')}
                  </button>
                </>
              ) : (
                <>
                  <Link 
                    to="/login" 
                    onClick={() => setIsMenuOpen(false)}
                    className="block text-left text-foreground px-3 py-3 font-medium flex items-center gap-2"
                  >
                    <LogIn size={16} />
                    {t('auth.loginButton')}
                  </Link>
                  <Link 
                    to="/register" 
                    onClick={() => setIsMenuOpen(false)}
                    className="block text-left text-primary px-3 py-3 font-medium"
                  >
                    {t('auth.registerButton')}
                  </Link>
                </>
              )}
              {isConnected ? (
                 <button onClick={disconnect} className="w-full text-left text-foreground-secondary px-3 py-3 font-medium flex items-center gap-2">
                   <Wallet size={16} />
                   {t('nav.disconnect')}
                 </button>
              ) : (
                 <button onClick={() => setIsWalletModalOpen(true)} className="w-full text-left text-primary px-3 py-3 font-medium flex items-center gap-2">
                   <Wallet size={16} />
                   {t('nav.connectWallet')}
                 </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Wallet Connection Modal */}
      <WalletConnectionModal
        isOpen={isWalletModalOpen}
        onClose={() => {
          setIsWalletModalOpen(false);
        }}
        onConnectMetaMask={async () => {
          try {
            await connectMetaMask();
            setIsWalletModalOpen(false);
          } catch (err) {
            // Error is handled in context
          }
        }}
        onConnectManual={async (address: string) => {
          try {
            await connectManual(address);
            setIsWalletModalOpen(false);
          } catch (err) {
            // Error is handled in context
          }
        }}
        isConnecting={isConnecting}
        error={error}
      />
    </nav>
  );
};
