// File header: Redesigned navigation bar component with improved UX, accessibility, and responsiveness.
// Provides main navigation links, role-based menu, wallet connection, theme toggle, and language selection.
// Features: Keyboard navigation, ARIA labels, smooth animations, mobile-first design, and proper focus management.

import React, { useRef, useEffect, useLayoutEffect, useState, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Wallet, Menu, X, ChevronDown, Shield, Users, Ticket, ScanLine, Zap, LogIn, LogOut, User, Copy, Settings } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { useWeb3 } from '../../services/web3Context';
import { useAuth } from '../../services/authContext';
import { UserRole } from '../../types';
import { cn, formatAddress } from '../../lib/utils';
import { calculateDropdownPosition } from '../../lib/viewportUtils';
import { LanguageSwitcher } from './LanguageSwitcher';
import { ThemeToggle } from './ThemeToggle';
import { WalletConnectionModal } from '../WalletConnectionModal';

// Purpose: Reusable dropdown menu component with keyboard navigation and accessibility.
// Props: isOpen, onClose, position, children, id, ariaLabel, triggerRef
interface DropdownMenuProps {
  isOpen: boolean;
  onClose: () => void;
  position: { top: number; left?: number; right?: number; side: string } | null;
  children: React.ReactNode;
  id: string;
  ariaLabel: string;
  className?: string;
  triggerRef?: React.RefObject<HTMLElement>;
}

// Purpose: Reusable dropdown menu component with keyboard navigation and accessibility.
// CRITICAL: Uses z-[60] to stay above navbar (z-50) but below modals (z-[100]).
// Backdrop only on mobile to avoid covering other buttons on desktop.
const DropdownMenu: React.FC<DropdownMenuProps> = ({ 
  isOpen, 
  onClose, 
  position, 
  children, 
  id, 
  ariaLabel,
  className,
  triggerRef
}) => {
  const menuRef = useRef<HTMLDivElement>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  // Purpose: Handle keyboard navigation (Escape to close, Tab to navigate).
  // Side effects: Closes menu on Escape, traps focus within menu.
  useEffect(() => {
    if (!isOpen) return;

    // Store previous focus
    previousFocusRef.current = document.activeElement as HTMLElement;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        onClose();
        previousFocusRef.current?.focus();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Purpose: Focus first focusable element when menu opens.
  // Side effects: Sets focus to first button/link in menu.
  useEffect(() => {
    if (isOpen && menuRef.current) {
      const firstFocusable = menuRef.current.querySelector<HTMLElement>(
        'button, a, [tabindex]:not([tabindex="-1"])'
      );
      firstFocusable?.focus();
    }
  }, [isOpen]);

  // Purpose: Close dropdown when clicking outside (desktop only, mobile uses backdrop).
  // CRITICAL: Only closes if click is outside the dropdown, its trigger, and other navbar buttons.
  // This prevents closing when clicking other navbar buttons.
  useEffect(() => {
    if (!isOpen) return;

    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      
      // Don't close if clicking inside the dropdown menu
      if (menuRef.current?.contains(target)) {
        return;
      }
      
      // Don't close if clicking on any navbar button or link (including triggers for other dropdowns)
      // Check multiple ways to ensure we catch all navbar buttons
      const navButton = target.closest('nav button, nav a, button[aria-expanded], button[aria-haspopup]');
      if (navButton) {
        return; // Let the button's onClick handler manage the state
      }
      
      // Don't close if clicking on other dropdown menus
      if (target.closest('[role="menu"]')) {
        return;
      }
      
      // Don't close if clicking on LanguageSwitcher container
      if (target.closest('.language-dropdown') || target.closest('[aria-label*="language" i]')) {
        return;
      }
      
      // Don't close if clicking on ThemeToggle
      if (target.closest('[aria-label*="theme" i]')) {
        return;
      }
      
      // Don't close if clicking anywhere in the navbar
      if (target.closest('nav')) {
        return;
      }
      
      // Only close if clicking completely outside navbar area
      onClose();
    };

    // Use bubble phase (not capture) so button onClick handlers run first
    // Add small delay to ensure button handlers have executed
    const timeoutId = setTimeout(() => {
      document.addEventListener('click', handleClickOutside);
    }, 0);

    return () => {
      clearTimeout(timeoutId);
      document.removeEventListener('click', handleClickOutside);
    };
  }, [isOpen, onClose]);

  // Calculate default position if position is not yet set
  // This allows dropdown to render immediately before position is calculated
  const getDefaultPosition = () => {
    if (triggerRef?.current) {
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

  if (!isOpen || !currentPosition) return null;

  return createPortal(
    <>
      {/* Backdrop for mobile only - prevents covering other buttons on desktop */}
      <div
        className="fixed inset-0 z-[55] md:hidden bg-black/20 backdrop-blur-sm pointer-events-auto"
        onClick={(e) => {
          e.stopPropagation();
          onClose();
        }}
        aria-hidden="true"
      />
      {/* Dropdown Menu - positioned and visible, same structure as LanguageSwitcher */}
      <div
        ref={menuRef}
        id={id}
        role="menu"
        aria-label={ariaLabel}
        className={cn(
          "fixed w-48 bg-background-elevated border border-border rounded-lg shadow-xl z-[60]",
          "animate-fade-in",
          className
        )}
        style={{
          top: currentPosition.top !== undefined ? `${currentPosition.top}px` : undefined,
          bottom: currentPosition.bottom !== undefined ? `${currentPosition.bottom}px` : undefined,
          left: currentPosition.left !== undefined ? `${currentPosition.left}px` : undefined,
          right: currentPosition.right !== undefined ? `${currentPosition.right}px` : undefined,
          visibility: 'visible',
          opacity: 1,
          display: 'block',
        }}
        onKeyDown={(e) => {
          if (e.key === 'Escape') {
            e.preventDefault();
            onClose();
          }
        }}
        onClick={(e) => {
          // Prevent clicks inside dropdown from closing it
          e.stopPropagation();
        }}
        onMouseEnter={() => {
          // Keep dropdown open when mouse enters
          // This prevents closing when moving from trigger to dropdown
        }}
        onMouseLeave={(e) => {
          // Only close if mouse is not moving back to trigger button
          const relatedTarget = e.relatedTarget as HTMLElement;
          if (!relatedTarget?.closest(`button[aria-controls="${id}"], button[aria-haspopup="true"]`)) {
            // Small delay to allow moving between dropdown and trigger
            setTimeout(() => {
              if (!document.querySelector(`#${id}:hover`) && 
                  !document.querySelector(`button[aria-controls="${id}"]:hover, button[aria-haspopup="true"]:hover`)) {
                // Preserve scroll position when closing
                const scrollY = window.scrollY;
                const scrollX = window.scrollX;
                onClose();
                // Restore scroll position after closing
                requestAnimationFrame(() => {
                  window.scrollTo(scrollX, scrollY);
                });
              }
            }, 100);
          }
        }}
      >
        {children}
      </div>
    </>,
    document.body
  );
};

// Purpose: Navigation link component with active state and keyboard support.
interface NavLinkProps {
  to: string;
  children: React.ReactNode;
  isActive: boolean;
  onClick?: () => void;
  icon?: React.ReactNode;
  className?: string;
}

const NavLink: React.FC<NavLinkProps> = ({ to, children, isActive, onClick, icon, className }) => {
  return (
    <Link
      to={to}
      onClick={onClick}
      className={cn(
        "relative flex items-center gap-2 px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200",
        "focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-background",
        isActive
          ? "bg-primary/10 text-primary font-semibold"
          : "text-foreground-secondary hover:text-foreground hover:bg-background-hover",
        className
      )}
      aria-current={isActive ? 'page' : undefined}
    >
      {icon && <span className="flex-shrink-0">{icon}</span>}
      <span>{children}</span>
      {isActive && (
        <span className="absolute left-0 top-0 bottom-0 w-1 bg-primary rounded-r-full" aria-hidden="true" />
      )}
    </Link>
  );
};

export const Navbar: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { isConnected, address, connectMetaMask, connectManual, disconnect, balance, isConnecting, error } = useWeb3();
  const { isAuthenticated, user, logout } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isWalletModalOpen, setIsWalletModalOpen] = useState(false);
  const [isWalletMenuOpen, setIsWalletMenuOpen] = useState(false);
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const location = useLocation();
  
  // Get user's actual role from authentication context
  const userRole = user?.role ? (user.role.toUpperCase() as UserRole) : UserRole.BUYER;
  
  const walletTriggerRef = useRef<HTMLButtonElement>(null);
  const userTriggerRef = useRef<HTMLButtonElement>(null);
  const walletMenuRef = useRef<HTMLDivElement>(null);
  const userMenuRef = useRef<HTMLDivElement>(null);
  const [walletMenuPosition, setWalletMenuPosition] = useState<{ top: number; left?: number; right?: number; side: string } | null>(null);
  const [userMenuPosition, setUserMenuPosition] = useState<{ top: number; left?: number; right?: number; side: string } | null>(null);

  const isActive = useCallback((path: string) => location.pathname === path, [location.pathname]);

  // Purpose: Close mobile menu when route changes.
  // Side effects: Sets isMenuOpen to false on location change.
  useEffect(() => {
    setIsMenuOpen(false);
  }, [location.pathname]);

  // Purpose: Calculate dropdown positions when opened.
  // Side effects: Updates position state based on viewport boundaries.
  useEffect(() => {
    if (isWalletMenuOpen && walletTriggerRef.current) {
      const triggerRect = walletTriggerRef.current.getBoundingClientRect();
      const menuWidth = 192;
      // Use estimated height if menu ref doesn't exist yet
      const menuHeight = walletMenuRef.current?.offsetHeight || 100;
      const pos = calculateDropdownPosition(triggerRect, menuWidth, menuHeight, 8);
      setWalletMenuPosition(pos);

      // Throttle scroll/resize handlers to prevent scroll jank
      let rafId: number | null = null;
      const handleResize = () => {
        if (rafId) return;
        rafId = requestAnimationFrame(() => {
          if (walletTriggerRef.current) {
            const newTriggerRect = walletTriggerRef.current.getBoundingClientRect();
            const newMenuHeight = walletMenuRef.current?.offsetHeight || 100;
            const newPos = calculateDropdownPosition(newTriggerRect, menuWidth, newMenuHeight, 8);
            setWalletMenuPosition(newPos);
          }
          rafId = null;
        });
      };

      window.addEventListener('resize', handleResize);
      window.addEventListener('scroll', handleResize, { passive: true, capture: true });
      return () => {
        window.removeEventListener('resize', handleResize);
        window.removeEventListener('scroll', handleResize, true);
        if (rafId) cancelAnimationFrame(rafId);
      };
    } else {
      setWalletMenuPosition(null);
    }
  }, [isWalletMenuOpen]);

  useEffect(() => {
    if (isUserMenuOpen && userTriggerRef.current) {
      const triggerRect = userTriggerRef.current.getBoundingClientRect();
      const menuWidth = 200;
      // Use estimated height if menu ref doesn't exist yet
      const menuHeight = userMenuRef.current?.offsetHeight || 150;
      const pos = calculateDropdownPosition(triggerRect, menuWidth, menuHeight, 8);
      setUserMenuPosition(pos);

      // Throttle scroll/resize handlers to prevent scroll jank
      let rafId: number | null = null;
      const handleResize = () => {
        if (rafId) return;
        rafId = requestAnimationFrame(() => {
          if (userTriggerRef.current) {
            const newTriggerRect = userTriggerRef.current.getBoundingClientRect();
            const newMenuHeight = userMenuRef.current?.offsetHeight || 150;
            const newPos = calculateDropdownPosition(newTriggerRect, menuWidth, newMenuHeight, 8);
            setUserMenuPosition(newPos);
          }
          rafId = null;
        });
      };

      window.addEventListener('resize', handleResize);
      window.addEventListener('scroll', handleResize, { passive: true, capture: true });
      return () => {
        window.removeEventListener('resize', handleResize);
        window.removeEventListener('scroll', handleResize, true);
        if (rafId) cancelAnimationFrame(rafId);
      };
    } else {
      setUserMenuPosition(null);
    }
  }, [isUserMenuOpen]);

  // Purpose: Get navigation links based on user role.
  // Returns: Array of link objects with path and label.
  const getLinks = useCallback(() => {
    const common = [{ path: '/', label: t('nav.marketplace'), icon: <Zap size={16} /> }];
    switch (userRole) {
      case UserRole.ORGANIZER:
        return [
          ...common,
          { path: '/dashboard', label: t('nav.dashboard'), icon: <Ticket size={16} /> },
          { path: '/create-event', label: t('nav.createEvent'), icon: <Zap size={16} /> }
        ];
      case UserRole.RESELLER:
        return [
          ...common,
          { path: '/dashboard', label: t('nav.resalePortal'), icon: <Ticket size={16} /> }
        ];
      case UserRole.SCANNER:
        return [
          { path: '/scanner', label: t('nav.launchScanner'), icon: <ScanLine size={16} /> }
        ];
      case UserRole.ADMIN:
        return [
          ...common,
          { path: '/admin', label: t('nav.adminPanel'), icon: <Shield size={16} /> }
        ];
      case UserRole.BUYER:
      default:
        return [
          ...common,
          { path: '/dashboard', label: t('nav.myTickets'), icon: <Ticket size={16} /> }
        ];
    }
  }, [userRole, t]);

  const links = getLinks();

  // Purpose: Handle wallet disconnect with cleanup.
  // Side effects: Disconnects wallet and closes menus.
  const handleDisconnect = useCallback(() => {
    disconnect();
    setIsWalletMenuOpen(false);
    setIsMenuOpen(false);
  }, [disconnect]);

  // Purpose: Handle user logout with navigation.
  // Side effects: Logs out user, navigates to home, closes menus.
  const handleLogout = useCallback(async () => {
    await logout();
    navigate('/');
    setIsUserMenuOpen(false);
    setIsMenuOpen(false);
  }, [logout, navigate]);

  return (
    <nav 
      className="sticky top-0 z-50 bg-background/95 backdrop-blur-md border-b border-border shadow-sm"
      role="navigation"
      aria-label={t('nav.mainNavigation')}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Logo and Desktop Navigation */}
          <div className="flex items-center gap-8 flex-1">
            {/* Logo */}
            <Link 
              to="/" 
              className="flex items-center gap-2 group focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-background rounded-lg"
              aria-label={t('nav.home')}
            >
              <div className="w-9 h-9 bg-primary/10 rounded-lg flex items-center justify-center border border-primary/20 group-hover:border-primary/50 group-hover:bg-primary/20 transition-all duration-200">
                <Zap size={18} className="text-primary" />
              </div>
              <span className="font-bold text-lg text-foreground tracking-tight hidden sm:block">
                NFTix
              </span>
            </Link>
            
            {/* Desktop Navigation Links */}
            <nav 
              className="hidden lg:flex items-center gap-1"
              aria-label={t('nav.mainLinks')}
            >
              {links.map((link) => (
                <NavLink
                  key={link.path}
                  to={link.path}
                  isActive={isActive(link.path)}
                  icon={link.icon}
                >
                  {link.label}
                </NavLink>
              ))}
            </nav>
          </div>

          {/* Right Side Actions - Desktop */}
          <div className="hidden lg:flex items-center gap-3">
            {/* Theme Toggle */}
            <ThemeToggle />
            
            {/* Language Switcher */}
            <LanguageSwitcher />
            
            {/* Wallet Section */}
            {isConnected ? (
              <div className="flex items-center gap-2 pl-3 border-l border-border">
                {/* Wallet Badge with Dropdown */}
                <div className="relative">
                  <button
                    ref={walletTriggerRef}
                    onClick={(e) => {
                      e.stopPropagation();
                      const newState = !isWalletMenuOpen;
                      setIsWalletMenuOpen(newState);
                      // Close other dropdowns when opening this one
                      if (newState) {
                        setIsUserMenuOpen(false);
                        // Close language switcher if open
                        window.dispatchEvent(new CustomEvent('closeLanguageSwitcher'));
                      }
                    }}
                    onMouseEnter={() => {
                      // Only open on hover if no other dropdown is open
                      if (!isUserMenuOpen) {
                        setIsWalletMenuOpen(true);
                      }
                    }}
                    onMouseLeave={(e) => {
                      // Only close if mouse is not moving to the dropdown menu
                      const relatedTarget = e.relatedTarget as HTMLElement;
                      if (!relatedTarget?.closest('#wallet-menu')) {
                        setIsWalletMenuOpen(false);
                      }
                    }}
                    className="flex items-center gap-2 bg-background-hover border border-border px-3 py-1.5 rounded-lg text-sm font-mono text-foreground hover:border-border-hover transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
                    aria-label={t('wallet.walletMenu')}
                    aria-expanded={isWalletMenuOpen}
                    aria-haspopup="true"
                  >
                    <div className="w-2 h-2 rounded-full bg-success animate-pulse" />
                    <span className="hidden xl:inline">{formatAddress(address || '')}</span>
                    <span className="xl:hidden">{formatAddress(address || '', 4)}</span>
                    <ChevronDown size={12} className={cn("transition-transform duration-200", isWalletMenuOpen && "rotate-180")} />
                  </button>
                  
                  <DropdownMenu
                    isOpen={isWalletMenuOpen}
                    onClose={() => setIsWalletMenuOpen(false)}
                    position={walletMenuPosition}
                    id="wallet-menu"
                    ariaLabel={t('wallet.walletMenu')}
                    triggerRef={walletTriggerRef}
                  >
                    <div 
                      ref={walletMenuRef} 
                      className="p-1"
                    >
                      {/* Balance Display */}
                      <div className="px-3 py-2 border-b border-border">
                        <div className="text-xs text-foreground-tertiary mb-1">{t('wallet.balance')}</div>
                        <div className="text-sm font-mono font-semibold text-foreground">
                          {balance} <span className="text-foreground-tertiary">ETH</span>
                        </div>
                      </div>
                      
                      {/* Copy Address */}
                      <button
                        role="menuitem"
                        type="button"
                        onClick={async (e) => {
                          e.stopPropagation();
                          e.preventDefault();
                          if (address) {
                            try {
                              await navigator.clipboard.writeText(address);
                              setIsWalletMenuOpen(false);
                            } catch (err) {
                              console.error('Failed to copy address:', err);
                            }
                          }
                        }}
                        onMouseDown={(e) => {
                          e.preventDefault();
                        }}
                        className="w-full text-left px-3 py-2 text-sm text-foreground-secondary hover:bg-background-hover rounded-lg transition-colors duration-150 flex items-center gap-2 focus:outline-none focus:bg-background-hover"
                      >
                        <Copy size={14} />
                        {t('wallet.copyAddress')}
                      </button>
                      
                      {/* Disconnect */}
                      <button
                        role="menuitem"
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          e.preventDefault();
                          handleDisconnect();
                        }}
                        onMouseDown={(e) => {
                          e.preventDefault();
                        }}
                        className="w-full text-left px-3 py-2 text-sm text-error hover:bg-error/10 rounded-lg transition-colors duration-150 flex items-center gap-2 focus:outline-none focus:bg-error/10"
                      >
                        <LogOut size={14} />
                        {t('nav.disconnect')}
                      </button>
                    </div>
                  </DropdownMenu>
                </div>
              </div>
            ) : (
              <button
                onClick={() => setIsWalletModalOpen(true)}
                data-cy="connect-wallet-btn"
                className="flex items-center gap-2 bg-primary hover:bg-primary-hover text-white px-4 py-2 rounded-lg font-medium text-sm transition-all duration-200 hover:-translate-y-0.5 shadow-lg shadow-primary/20 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
                aria-label={t('nav.connectWallet')}
              >
                <Wallet size={16} />
                <span className="hidden xl:inline">{t('nav.connectWallet')}</span>
                <span className="xl:hidden">{t('nav.connect')}</span>
              </button>
            )}

            {/* User Menu (Authentication) */}
            {isAuthenticated ? (
              <div className="relative pl-3 border-l border-border">
                <button
                  ref={userTriggerRef}
                  onClick={(e) => {
                    e.stopPropagation();
                    const newState = !isUserMenuOpen;
                    setIsUserMenuOpen(newState);
                      // Close other dropdowns when opening this one
                      if (newState) {
                        setIsWalletMenuOpen(false);
                        // Close language switcher if open
                        window.dispatchEvent(new CustomEvent('closeLanguageSwitcher'));
                      }
                  }}
                  onMouseEnter={() => {
                    // Only open on hover if no other dropdown is open
                    if (!isWalletMenuOpen) {
                      setIsUserMenuOpen(true);
                    }
                  }}
                  onMouseLeave={(e) => {
                    // Only close if mouse is not moving to the dropdown menu
                    const relatedTarget = e.relatedTarget as HTMLElement;
                    if (!relatedTarget?.closest('#user-menu')) {
                      setIsUserMenuOpen(false);
                    }
                  }}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-background-elevated border border-border text-sm font-medium text-foreground-secondary hover:border-border-hover hover:text-foreground transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
                  aria-label={t('nav.userMenu')}
                  aria-expanded={isUserMenuOpen}
                  aria-haspopup="true"
                >
                  <User size={16} />
                  <span className="hidden xl:inline max-w-[120px] truncate">
                    {user?.email || user?.username}
                  </span>
                  <ChevronDown size={12} className={cn("transition-transform duration-200", isUserMenuOpen && "rotate-180")} />
                </button>
                
                <DropdownMenu
                  isOpen={isUserMenuOpen}
                  onClose={() => setIsUserMenuOpen(false)}
                  position={userMenuPosition}
                  id="user-menu"
                  ariaLabel={t('nav.userMenu')}
                  triggerRef={userTriggerRef}
                >
                  <div 
                    ref={userMenuRef} 
                    className="p-1"
                  >
                    <div className="px-3 py-2 border-b border-border">
                      <div className="text-sm font-medium text-foreground truncate">
                        {user?.email || user?.username}
                      </div>
                      {user?.email && (
                        <div className="text-xs text-foreground-tertiary truncate">
                          {user.email}
                        </div>
                      )}
                    </div>
                    <button
                      role="menuitem"
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        e.preventDefault();
                        handleLogout();
                      }}
                      onMouseDown={(e) => {
                        e.preventDefault();
                      }}
                      className="w-full text-left px-3 py-2 text-sm text-error hover:bg-error/10 rounded-lg transition-colors duration-150 flex items-center gap-2 focus:outline-none focus:bg-error/10 mt-1"
                    >
                      <LogOut size={14} />
                      {t('auth.logout')}
                    </button>
                  </div>
                </DropdownMenu>
              </div>
            ) : (
              <div className="flex items-center gap-2 pl-3 border-l border-border">
                <Link
                  to="/login"
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium text-foreground-secondary hover:text-foreground hover:bg-background-hover transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
                >
                  <LogIn size={14} />
                  <span className="hidden xl:inline">{t('auth.loginButton')}</span>
                  <span className="xl:hidden">{t('auth.login')}</span>
                </Link>
                <Link
                  to="/register"
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary-hover transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
                >
                  <span className="hidden xl:inline">{t('auth.registerButton')}</span>
                  <span className="xl:hidden">{t('auth.register')}</span>
                </Link>
              </div>
            )}
          </div>

          {/* Mobile Menu Toggle */}
          <div className="lg:hidden flex items-center gap-2">
            {/* Theme Toggle - Mobile */}
            <ThemeToggle />
            
            {/* Hamburger Menu Button */}
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="p-2 rounded-lg text-foreground-secondary hover:bg-background-hover hover:text-foreground transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
              aria-label={isMenuOpen ? t('nav.closeMenu') : t('nav.openMenu')}
              aria-expanded={isMenuOpen}
            >
              {isMenuOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu */}
      {isMenuOpen && (
        <div 
          className="lg:hidden bg-background-elevated border-t border-border animate-slide-down"
          role="menu"
          aria-label={t('nav.mobileMenu')}
        >
          <div className="px-4 py-3 space-y-1">
            {/* Navigation Links */}
            {links.map((link) => (
              <NavLink
                key={link.path}
                to={link.path}
                isActive={isActive(link.path)}
                onClick={() => setIsMenuOpen(false)}
                icon={link.icon}
                className="w-full"
              >
                {link.label}
              </NavLink>
            ))}
            
            {/* Divider */}
            <div className="pt-3 border-t border-border mt-3 space-y-1">
              {/* Language Switcher - Mobile */}
              <div className="px-4 py-2">
                <LanguageSwitcher />
              </div>
              
              {/* Wallet Section - Mobile */}
              {isConnected ? (
                <>
                  <div className="px-4 py-2 border-b border-border mb-2">
                    <div className="text-xs text-foreground-tertiary mb-1">{t('wallet.balance')}</div>
                    <div className="text-sm font-mono font-semibold text-foreground">
                      {balance} <span className="text-foreground-tertiary">ETH</span>
                    </div>
                    <div className="text-xs font-mono text-foreground-secondary mt-1">
                      {formatAddress(address || '')}
                    </div>
                  </div>
                  
                  
                  <button
                    onClick={handleDisconnect}
                    className="w-full text-left px-4 py-3 text-sm text-error hover:bg-error/10 rounded-lg transition-colors duration-150 flex items-center gap-2 focus:outline-none focus:bg-error/10"
                  >
                    <LogOut size={16} />
                    {t('nav.disconnect')}
                  </button>
                </>
              ) : (
                <button
                  onClick={() => {
                    setIsWalletModalOpen(true);
                    setIsMenuOpen(false);
                  }}
                  data-cy="connect-wallet-btn-mobile"
                  className="w-full text-left px-4 py-3 text-sm text-primary hover:bg-primary/10 rounded-lg transition-colors duration-150 flex items-center gap-2 focus:outline-none focus:bg-primary/10"
                >
                  <Wallet size={16} />
                  {t('nav.connectWallet')}
                </button>
              )}
              
              {/* Authentication - Mobile */}
              {isAuthenticated ? (
                <>
                  <div className="px-4 py-2 border-t border-border mt-2 pt-3">
                    <div className="text-sm font-medium text-foreground mb-1">
                      {user?.email || user?.username}
                    </div>
                    {user?.email && (
                      <div className="text-xs text-foreground-tertiary">
                        {user.email}
                      </div>
                    )}
                  </div>
                  <button
                    onClick={handleLogout}
                    className="w-full text-left px-4 py-3 text-sm text-error hover:bg-error/10 rounded-lg transition-colors duration-150 flex items-center gap-2 focus:outline-none focus:bg-error/10"
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
                    className="block w-full text-left px-4 py-3 text-sm text-foreground hover:bg-background-hover rounded-lg transition-colors duration-150 flex items-center gap-2 focus:outline-none focus:bg-background-hover"
                  >
                    <LogIn size={16} />
                    {t('auth.loginButton')}
                  </Link>
                  <Link
                    to="/register"
                    onClick={() => setIsMenuOpen(false)}
                    className="block w-full text-left px-4 py-3 text-sm text-primary hover:bg-primary/10 rounded-lg transition-colors duration-150 focus:outline-none focus:bg-primary/10"
                  >
                    {t('auth.registerButton')}
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Wallet Connection Modal */}
      <WalletConnectionModal
        isOpen={isWalletModalOpen}
        onClose={() => setIsWalletModalOpen(false)}
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
