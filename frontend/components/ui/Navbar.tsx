// File header: Redesigned navigation bar component with improved UX, accessibility, and responsiveness.
// Provides main navigation links, role-based menu, wallet connection, theme toggle, and language selection.
// Features: Keyboard navigation, ARIA labels, smooth animations, mobile-first design, and proper focus management.

import React, { useRef, useEffect, useLayoutEffect, useState, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Wallet, Menu, X, ChevronDown, Shield, Users, Ticket, ScanLine, Zap, LogIn, LogOut, User, Copy, Settings, ShoppingBag, List, Info, Mail, Sparkles, TrendingUp } from 'lucide-react';
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
      const viewportWidth = window.innerWidth;
      const menuWidth = 192; // w-48 = 192px (matches dropdown width)
      
      // Check if dropdown would overflow on the right
      let left: number | undefined;
      let right: number | undefined;
      
      if (triggerRect.right + menuWidth > viewportWidth) {
        // Align to right edge of trigger
        right = viewportWidth - triggerRect.right;
      } else {
        // Align to left edge of trigger
        left = triggerRect.left;
      }
      
      return {
        top: triggerRect.bottom,  // Start with 0 gap, overlap handled in style (4px overlap)
        left,
        right,
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
          // Overlap by 4px to completely eliminate gap flickering
          top: currentPosition.top !== undefined ? `${Math.max(0, currentPosition.top - 4)}px` : undefined,
          bottom: currentPosition.bottom !== undefined ? `${currentPosition.bottom}px` : undefined,
          left: currentPosition.left !== undefined ? `${currentPosition.left}px` : undefined,
          right: currentPosition.right !== undefined ? `${currentPosition.right}px` : undefined,
          visibility: 'visible',
          opacity: 1,
          display: 'block',
          pointerEvents: 'auto',
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
          // Clear any pending close timeout
          const timeoutId = (menuRef.current as any)?._closeTimeout;
          if (timeoutId) {
            clearTimeout(timeoutId);
            (menuRef.current as any)._closeTimeout = null;
          }
        }}
        onMouseLeave={(e) => {
          // Only close if mouse is not moving back to trigger button
          const relatedTarget = e.relatedTarget as HTMLElement;
          
          // Check if mouse is moving to trigger button
          const triggerButton = triggerRef?.current;
          if (relatedTarget && triggerButton && (triggerButton.contains(relatedTarget) || relatedTarget === triggerButton)) {
            return; // Don't close if moving to trigger
          }
          
          // Check if mouse is moving to any element within the trigger button's container
          if (relatedTarget?.closest(`button[aria-controls="${id}"], button[aria-haspopup="true"]`)) {
            return; // Don't close if moving to trigger
          }
          
          // Use elementFromPoint to check current mouse position (more reliable than relatedTarget)
          const mouseX = e.clientX;
          const mouseY = e.clientY;
          const elementAtPoint = document.elementFromPoint(mouseX, mouseY);
          
          // Check if mouse is over trigger or dropdown using elementFromPoint
          if (elementAtPoint) {
            const dropdown = document.querySelector(`#${id}`);
            const trigger = triggerRef?.current;
            
            if ((dropdown && (dropdown === elementAtPoint || dropdown.contains(elementAtPoint))) ||
                (trigger && (trigger === elementAtPoint || trigger.contains(elementAtPoint)))) {
              return; // Don't close if mouse is still over dropdown or trigger
            }
          }
          
          // Increased delay to allow smooth movement through any remaining gap
          const timeoutId = setTimeout(() => {
            // Final check using elementFromPoint
            const currentElement = document.elementFromPoint(mouseX, mouseY);
            const dropdown = document.querySelector(`#${id}`);
            const trigger = triggerRef?.current;
            
            const isHoveringDropdown = dropdown && currentElement && (
              dropdown === currentElement || dropdown.contains(currentElement)
            );
            
            const isHoveringTrigger = trigger && currentElement && (
              trigger === currentElement || trigger.contains(currentElement)
            );
            
            if (!isHoveringDropdown && !isHoveringTrigger) {
              // Preserve scroll position when closing
              const scrollY = window.scrollY;
              const scrollX = window.scrollX;
              onClose();
              // Restore scroll position after closing
              requestAnimationFrame(() => {
                window.scrollTo(scrollX, scrollY);
              });
            }
          }, 150); // Balanced delay for smooth UX
          
          // Store timeout ID for cleanup if needed
          (e.currentTarget as any)._closeTimeout = timeoutId;
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
  isScroll?: boolean;
  onScrollToSection?: (sectionId: string) => void;
  iconOnly?: boolean; // Show only icon on smaller screens
  tooltip?: string; // Tooltip text for icon-only mode
}

const NavLink: React.FC<NavLinkProps> = ({ to, children, isActive, onClick, icon, className, isScroll, onScrollToSection, iconOnly, tooltip }) => {
  const handleClick = (e: React.MouseEvent) => {
    if (isScroll && onScrollToSection) {
      e.preventDefault();
      const sectionId = to.replace('#', '');
      onScrollToSection(sectionId);
    }
    if (onClick) {
      onClick();
    }
  };

  const linkClasses = cn(
    "relative flex items-center rounded-lg text-sm font-medium transition-all duration-300 group",
    "focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-background",
    // Responsive padding and gap: compact for icon-only, expands when text shows
    iconOnly 
      ? "px-2.5 py-2.5 gap-1.5 xl:px-3 xl:gap-2" 
      : "px-3 py-2.5 gap-2 xl:px-4",
    isActive
      ? "bg-primary/15 text-primary font-semibold shadow-[0_0_0_1px_rgba(var(--color-primary-rgb),0.2),0_0_12px_rgba(var(--color-primary-rgb),0.15)]"
      : "text-foreground-secondary hover:text-foreground hover:bg-background-hover/80 hover:shadow-[0_0_0_1px_rgba(var(--color-border-rgb),0.5)]",
    className
  );

  const iconElement = icon && (
    <span className={cn("flex-shrink-0", isActive ? "opacity-100" : "opacity-70 group-hover:opacity-100")}>
      {icon}
    </span>
  );

  if (isScroll && onScrollToSection) {
    return (
      <button
        onClick={handleClick}
        className={linkClasses}
        title={tooltip || (typeof children === 'string' ? children : undefined)}
        aria-label={tooltip || (typeof children === 'string' ? children : undefined)}
      >
        {iconElement}
        <span className={cn("whitespace-nowrap", iconOnly && "hidden xl:inline")}>{children}</span>
        {isActive && (
          <>
            <span className="absolute left-0 top-0 bottom-0 w-1 bg-primary rounded-r-full" aria-hidden="true" />
            <span className="absolute inset-0 bg-primary/5 rounded-lg -z-10" aria-hidden="true" />
          </>
        )}
      </button>
    );
  }

  return (
    <Link
      to={to}
      onClick={handleClick}
      className={linkClasses}
      aria-current={isActive ? 'page' : undefined}
      title={tooltip || (typeof children === 'string' ? children : undefined)}
      aria-label={tooltip || (typeof children === 'string' ? children : undefined)}
    >
      {iconElement}
      <span className={cn("whitespace-nowrap", iconOnly && "hidden xl:inline")}>{children}</span>
      {isActive && (
        <>
          <span className="absolute left-0 top-0 bottom-0 w-1 bg-primary rounded-r-full" aria-hidden="true" />
          <span className="absolute inset-0 bg-primary/5 rounded-lg -z-10" aria-hidden="true" />
        </>
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
      const pos = calculateDropdownPosition(triggerRect, menuWidth, menuHeight, 2);
      setWalletMenuPosition(pos);

      // Throttle scroll/resize handlers to prevent scroll jank
      let rafId: number | null = null;
      const handleResize = () => {
        if (rafId) return;
        rafId = requestAnimationFrame(() => {
          if (walletTriggerRef.current) {
            const newTriggerRect = walletTriggerRef.current.getBoundingClientRect();
            const newMenuHeight = walletMenuRef.current?.offsetHeight || 100;
            const newPos = calculateDropdownPosition(newTriggerRect, menuWidth, newMenuHeight, 2);
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
      // Use requestAnimationFrame to ensure DOM is updated and accurate positioning
      requestAnimationFrame(() => {
        if (!userTriggerRef.current) return;
        
        const triggerRect = userTriggerRef.current.getBoundingClientRect();
        const menuWidth = 192; // w-48 = 192px (matches dropdown className)
        // Use actual height if available, otherwise estimate
        const menuHeight = userMenuRef.current?.offsetHeight || 150;
        const pos = calculateDropdownPosition(triggerRect, menuWidth, menuHeight, 2);
        setUserMenuPosition(pos);
      });

      // Throttle scroll/resize handlers to prevent scroll jank
      let rafId: number | null = null;
      const handleResize = () => {
        if (rafId) return;
        rafId = requestAnimationFrame(() => {
          if (userTriggerRef.current) {
            const newTriggerRect = userTriggerRef.current.getBoundingClientRect();
            const menuWidth = 192; // w-48 = 192px
            const newMenuHeight = userMenuRef.current?.offsetHeight || 150;
            const newPos = calculateDropdownPosition(newTriggerRect, menuWidth, newMenuHeight, 2);
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
    // Note: No dependency array needed here as we want this to run whenever isUserMenuOpen changes
  }, [isUserMenuOpen]);

  // Purpose: Handle smooth scrolling to sections on homepage
  const handleScrollToSection = useCallback((sectionId: string) => {
    if (location.pathname !== '/') {
      navigate('/');
      // Wait for navigation, then scroll
      setTimeout(() => {
        const element = document.getElementById(sectionId);
        if (element) {
          const headerOffset = 100; // Navbar height (h-20 = 80px) + padding
          const elementPosition = element.getBoundingClientRect().top;
          const offsetPosition = elementPosition + window.pageYOffset - headerOffset;
          window.scrollTo({
            top: offsetPosition,
            behavior: 'smooth'
          });
        }
      }, 300);
    } else {
      const element = document.getElementById(sectionId);
      if (element) {
        const headerOffset = 100; // Navbar height (h-20 = 80px) + padding
        const elementPosition = element.getBoundingClientRect().top;
        const offsetPosition = elementPosition + window.pageYOffset - headerOffset;
        window.scrollTo({
          top: offsetPosition,
          behavior: 'smooth'
        });
      }
    }
    setIsMenuOpen(false);
  }, [location.pathname, navigate]);

  // Purpose: Get navigation links organized by groups.
  // Returns: Separate arrays for core navigation, tools, and additional links.
  const getNavigationGroups = useCallback(() => {
    // Group 1: Core Navigation (Left side) - Concise labels with icons
    const coreNav = [
      { path: '/', label: t('nav.marketplace', 'Marketplace'), shortLabel: 'Market', icon: <ShoppingBag size={16} />, isScroll: false, tooltip: t('nav.marketplace', 'Marketplace') },
      { path: '/dashboard', label: t('nav.myTickets', 'Tickets'), shortLabel: 'Tickets', icon: <Ticket size={16} />, isScroll: false, tooltip: t('nav.myTickets', 'My Tickets') },
      { path: '#browse-events', label: t('nav.browseEvents', 'Browse'), shortLabel: 'Browse', icon: <List size={16} />, isScroll: true, tooltip: t('nav.browseEvents', 'Browse Events') },
    ];

    // Group 2: Tools & Locales (Center/Right) - Icon-first with concise labels
    const toolsNav = [
      { path: '#reselling', label: t('nav.reselling', 'Resale'), shortLabel: 'Resale', icon: <TrendingUp size={16} />, isScroll: true, tooltip: t('nav.reselling', 'Reselling') },
      { path: '/features', label: t('nav.features', 'Features'), shortLabel: 'Features', icon: <Sparkles size={16} />, isScroll: false, tooltip: t('nav.features', 'Features') },
      { path: '/about', label: t('nav.about', 'About'), shortLabel: 'About', icon: <Info size={16} />, isScroll: false, tooltip: t('nav.about', 'About') },
      { path: '/contact', label: t('nav.contact', 'Contact'), shortLabel: 'Contact', icon: <Mail size={16} />, isScroll: false, tooltip: t('nav.contact', 'Contact') },
    ];

    // Additional role-based links
    const roleNav: Array<{ path: string; label: string; shortLabel?: string; icon: React.ReactNode; isScroll: boolean; tooltip?: string }> = [];
    switch (userRole) {
      case UserRole.ORGANIZER:
        roleNav.push({ path: '/create-event', label: t('nav.createEvent'), shortLabel: 'Create', icon: <Zap size={16} />, isScroll: false, tooltip: t('nav.createEvent') });
        break;
      case UserRole.SCANNER:
        return {
          coreNav: [{ path: '/scanner', label: t('nav.launchScanner'), shortLabel: 'Scanner', icon: <ScanLine size={16} />, isScroll: false, tooltip: t('nav.launchScanner') }],
          toolsNav: [],
          roleNav: [],
        };
      case UserRole.ADMIN:
        roleNav.push({ path: '/admin', label: t('nav.adminPanel'), shortLabel: 'Admin', icon: <Shield size={16} />, isScroll: false, tooltip: t('nav.adminPanel') });
        break;
    }

    return { coreNav, toolsNav, roleNav };
  }, [userRole, t]);

  const { coreNav, toolsNav, roleNav } = getNavigationGroups();

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
      className="sticky top-0 z-50 bg-background/95 backdrop-blur-xl border-b border-border/80 shadow-lg shadow-black/5"
      role="navigation"
      aria-label={t('nav.mainNavigation')}
    >
      <div className="max-w-[1920px] mx-auto px-6 sm:px-8 lg:px-10">
        <div className="flex items-center justify-between h-20">
          
          {/* Group 1: Logo & Core Navigation (Left) */}
          <div className="flex items-center gap-6 lg:gap-10">
            {/* Logo */}
            <Link 
              to="/" 
              className="flex items-center gap-3 group focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-background rounded-lg px-2 -ml-2"
              aria-label={t('nav.home')}
            >
              <div className="w-10 h-10 bg-gradient-to-br from-primary/20 to-primary/10 rounded-xl flex items-center justify-center border border-primary/30 group-hover:border-primary/60 group-hover:bg-primary/20 transition-all duration-300 shadow-sm group-hover:shadow-md group-hover:shadow-primary/20">
                <Zap size={20} className="text-primary" />
              </div>
              <span className="font-bold text-xl text-foreground tracking-tight hidden sm:block">
                NFTix
              </span>
            </Link>
            
            {/* Vertical Separator */}
            <div className="hidden lg:block w-px h-8 bg-border/60" />
            
            {/* Core Navigation Links - Icon-first design with concise labels */}
            <nav 
              className="hidden lg:flex items-center gap-1.5"
              aria-label={t('nav.mainLinks')}
            >
              {coreNav.map((link) => (
                <NavLink
                  key={link.path}
                  to={link.path}
                  isActive={link.isScroll ? false : isActive(link.path)}
                  icon={link.icon}
                  isScroll={link.isScroll}
                  onScrollToSection={handleScrollToSection}
                  iconOnly={true}
                  tooltip={link.tooltip}
                >
                  <span className="hidden xl:inline">{link.shortLabel || link.label}</span>
                </NavLink>
              ))}
            </nav>
          </div>

          {/* Group 2 & 3: Tools/Locales & User/Wallet (Center/Right) */}
          <div className="hidden lg:flex items-center gap-4">
            {/* Group 2: Tools & Locales */}
            <div className="flex items-center gap-3 pr-4">
              {/* Tools Navigation - Icon-first with tooltips */}
              <nav className="flex items-center gap-1.5">
                {toolsNav.map((link) => (
                  <NavLink
                    key={link.path}
                    to={link.path}
                    isActive={link.isScroll ? false : isActive(link.path)}
                    icon={link.icon}
                    isScroll={link.isScroll}
                    onScrollToSection={handleScrollToSection}
                    iconOnly={true}
                    tooltip={link.tooltip}
                  >
                    <span className="hidden xl:inline">{link.shortLabel || link.label}</span>
                  </NavLink>
                ))}
                {roleNav.map((link) => (
                  <NavLink
                    key={link.path}
                    to={link.path}
                    isActive={link.isScroll ? false : isActive(link.path)}
                    icon={link.icon}
                    isScroll={link.isScroll}
                    onScrollToSection={handleScrollToSection}
                    iconOnly={true}
                    tooltip={link.tooltip}
                  >
                    <span className="hidden xl:inline">{link.shortLabel || link.label}</span>
                  </NavLink>
                ))}
              </nav>
              
              {/* Vertical Separator */}
              <div className="w-px h-8 bg-border/60" />
              
              {/* Theme Toggle */}
              <div className="px-2">
                <ThemeToggle />
              </div>
              
              {/* Language Switcher */}
              <div className="px-2">
                <LanguageSwitcher />
              </div>
            </div>
            
            {/* Vertical Separator between Tools and User/Wallet */}
            <div className="w-px h-10 bg-border/60 mx-2" />
            
            {/* Group 3: User & Wallet (Far Right) */}
            <div className="flex items-center gap-3 pl-2">
            {/* Wallet Section */}
            {isConnected ? (
              <div className="flex items-center gap-3">
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
                      // Only close if mouse is not moving to the dropdown menu or back to button
                      const relatedTarget = e.relatedTarget as HTMLElement;
                      
                      // Check if moving to dropdown
                      if (relatedTarget?.closest('#wallet-menu')) {
                        return;
                      }
                      
                      // Check if moving back to this button
                      if (relatedTarget === walletTriggerRef.current || walletTriggerRef.current?.contains(relatedTarget)) {
                        return;
                      }
                      
                      // Use elementFromPoint for reliable detection
                      const mouseX = e.clientX;
                      const mouseY = e.clientY;
                      
                      // Small delay to allow smooth movement
                      setTimeout(() => {
                        const currentElement = document.elementFromPoint(mouseX, mouseY);
                        const dropdown = document.querySelector('#wallet-menu');
                        const trigger = walletTriggerRef.current;
                        
                        const isHoveringDropdown = dropdown && currentElement && (
                          dropdown === currentElement || dropdown.contains(currentElement)
                        );
                        
                        const isHoveringTrigger = trigger && currentElement && (
                          trigger === currentElement || trigger.contains(currentElement)
                        );
                        
                        if (!isHoveringDropdown && !isHoveringTrigger) {
                          setIsWalletMenuOpen(false);
                        }
                      }, 150);
                    }}
                    className="flex items-center gap-2.5 bg-background-elevated/80 border border-border/60 px-4 py-2.5 rounded-xl text-sm font-mono text-foreground hover:border-primary/40 hover:bg-background-elevated hover:shadow-[0_0_0_1px_rgba(var(--color-primary-rgb),0.3),0_0_16px_rgba(var(--color-primary-rgb),0.1)] transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 shadow-sm"
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
                className="flex items-center gap-2.5 bg-primary hover:bg-primary-hover text-white px-5 py-2.5 rounded-xl font-semibold text-sm transition-all duration-300 hover:shadow-[0_0_0_1px_rgba(255,255,255,0.2),0_0_20px_rgba(var(--color-primary-rgb),0.4)] shadow-lg shadow-primary/30 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
                aria-label={t('nav.connectWallet')}
              >
                <Wallet size={16} />
                <span className="hidden xl:inline">{t('nav.connectWallet')}</span>
                <span className="xl:hidden">{t('nav.connect')}</span>
              </button>
            )}

            {/* User Menu (Authentication) */}
            {isAuthenticated ? (
              <div className="relative">
                {/* Vertical Separator */}
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-px h-8 bg-border/60" />
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
                    // Only close if mouse is not moving to the dropdown menu or trigger
                    const relatedTarget = e.relatedTarget as HTMLElement;
                    
                    // Check if moving to dropdown
                    if (relatedTarget?.closest('#user-menu')) {
                      return;
                    }
                    
                    // Check if moving back to this button
                    if (relatedTarget === userTriggerRef.current || userTriggerRef.current?.contains(relatedTarget)) {
                      return;
                    }
                    
                    // Use elementFromPoint for reliable detection
                    const mouseX = e.clientX;
                    const mouseY = e.clientY;
                    
                    // Small delay to allow smooth movement through gap
                    setTimeout(() => {
                      // Final check using elementFromPoint
                      const currentElement = document.elementFromPoint(mouseX, mouseY);
                      const dropdown = document.querySelector('#user-menu');
                      const trigger = userTriggerRef.current;
                      
                      const isHoveringDropdown = dropdown && currentElement && (
                        dropdown === currentElement || dropdown.contains(currentElement)
                      );
                      
                      const isHoveringTrigger = trigger && currentElement && (
                        trigger === currentElement || trigger.contains(currentElement)
                      );
                      
                      if (!isHoveringDropdown && !isHoveringTrigger) {
                        setIsUserMenuOpen(false);
                      }
                    }, 150);
                  }}
                  className="flex items-center gap-2.5 px-4 py-2.5 rounded-xl bg-background-elevated/80 border border-border/60 text-sm font-medium text-foreground-secondary hover:border-primary/40 hover:text-foreground hover:bg-background-elevated hover:shadow-[0_0_0_1px_rgba(var(--color-primary-rgb),0.3),0_0_16px_rgba(var(--color-primary-rgb),0.1)] transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 shadow-sm ml-3"
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
              <div className="flex items-center gap-3 ml-3">
                <Link
                  to="/login"
                  className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium text-foreground-secondary hover:text-foreground hover:bg-background-hover/80 transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
                >
                  <LogIn size={14} />
                  <span className="hidden xl:inline">{t('auth.loginButton')}</span>
                  <span className="xl:hidden">{t('auth.login')}</span>
                </Link>
                <Link
                  to="/register"
                  className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-primary text-primary-foreground text-sm font-semibold hover:bg-primary-hover hover:shadow-[0_0_0_1px_rgba(255,255,255,0.2),0_0_20px_rgba(var(--color-primary-rgb),0.4)] transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 shadow-lg shadow-primary/30"
                >
                  <span className="hidden xl:inline">{t('auth.registerButton')}</span>
                  <span className="xl:hidden">{t('auth.register')}</span>
                </Link>
              </div>
            )}
            </div>
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
            {/* Core Navigation Links */}
            <div className="mb-4">
              <div className="text-xs font-semibold text-foreground-tertiary uppercase tracking-wider px-2 mb-2">
                {t('nav.coreNavigation', 'Core Navigation')}
              </div>
              {coreNav.map((link) => (
                <NavLink
                  key={link.path}
                  to={link.path}
                  isActive={link.isScroll ? false : isActive(link.path)}
                  onClick={() => setIsMenuOpen(false)}
                  icon={link.icon}
                  className="w-full"
                  isScroll={link.isScroll}
                  onScrollToSection={handleScrollToSection}
                >
                  {link.label}
                </NavLink>
              ))}
            </div>
            
            {/* Tools Navigation Links */}
            {(toolsNav.length > 0 || roleNav.length > 0) && (
              <div className="mb-4 pt-4 border-t border-border">
                <div className="text-xs font-semibold text-foreground-tertiary uppercase tracking-wider px-2 mb-2">
                  {t('nav.tools', 'Tools')}
                </div>
                {toolsNav.map((link) => (
                  <NavLink
                    key={link.path}
                    to={link.path}
                    isActive={link.isScroll ? false : isActive(link.path)}
                    onClick={() => setIsMenuOpen(false)}
                    icon={link.icon}
                    className="w-full"
                    isScroll={link.isScroll}
                    onScrollToSection={handleScrollToSection}
                    tooltip={link.tooltip}
                  >
                    {link.label}
                  </NavLink>
                ))}
                {roleNav.map((link) => (
                  <NavLink
                    key={link.path}
                    to={link.path}
                    isActive={link.isScroll ? false : isActive(link.path)}
                    onClick={() => setIsMenuOpen(false)}
                    icon={link.icon}
                    className="w-full"
                    isScroll={link.isScroll}
                    onScrollToSection={handleScrollToSection}
                    tooltip={link.tooltip}
                  >
                    {link.label}
                  </NavLink>
                ))}
              </div>
            )}
            
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
