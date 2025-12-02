// File header: Web3/NFT ticketing chatbot assistant component.
// Provides interactive chat interface for answering questions about NFT ticketing, blockchain, and Web3.

import React, { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { MessageCircle, X, Send, Bot, User, AlertCircle } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { cn } from '../lib/utils';
import { sendChatMessage, checkChatbotHealth } from '../services/chatbotService';
import { useAuth } from '../services/authContext';

// Purpose: Message type definition for chat messages.
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

// Note: getChatbotResponse function removed - now using Gemini API via backend

// Purpose: ChatBot component with floating button and chat window.
// Returns: JSX with chat interface.
// Side effects: Manages chat state, handles user messages, generates responses.
export const ChatBot: React.FC = () => {
  const { t, i18n } = useTranslation();
  const { user } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [retryCount, setRetryCount] = useState(0);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Purpose: Scroll to bottom when new messages are added.
  // Side effects: Scrolls messages container to bottom.
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Purpose: Focus input when chat opens.
  // Side effects: Focuses input field.
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen]);

  // Purpose: Initialize chat with greeting message on first open.
  // Side effects: Adds greeting message if chat is empty.
  useEffect(() => {
    if (isOpen && messages.length === 0) {
      const greeting = i18n.language === 'az'
        ? "Salam! NFT biletləmə və blokçeyn məsləhətçisiniz. Nə haqqında bilmək istəyirsiniz?"
        : "Welcome! I'm your blockchain and NFT ticketing assistant. What would you like to know?";
      
      setMessages([{
        id: 'greeting',
        role: 'assistant',
        content: greeting,
        timestamp: new Date(),
      }]);
    }
  }, [isOpen, messages.length, i18n.language]);

  // Purpose: Handle sending a message to Gemini API.
  // Side effects: Adds user message, calls API, adds bot response.
  const handleSend = async () => {
    if (!inputValue.trim() || isTyping) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    const messageText = inputValue.trim();
    const currentSessionId = sessionId;
    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);
    setError(null);

    // Retry function
    const sendWithRetry = async (attempt: number = 0): Promise<void> => {
      try {
        // Send message to Gemini API via backend
        const response = await sendChatMessage(
          messageText,
          currentSessionId || undefined,
          user?.user_id?.toString() || undefined
        );

        // Update session ID if provided
        if (response.session_id) {
          setSessionId(response.session_id);
        }

        // Add bot response
        const botMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: response.response,
          timestamp: new Date(response.timestamp),
        };

        setMessages(prev => [...prev, botMessage]);
        setRetryCount(0); // Reset retry count on success
        setIsTyping(false);
      } catch (err) {
        console.error('Error sending message to chatbot:', err);
        
        // Retry logic (max 2 retries)
        if (attempt < 2) {
          setRetryCount(attempt + 1);
          setTimeout(() => {
            sendWithRetry(attempt + 1);
          }, 1000 * (attempt + 1)); // Exponential backoff
          return;
        }

        // Show error message after max retries
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: t('chat.errorMessage') || "I'm sorry, I'm having trouble connecting right now. Please try again in a moment.",
          timestamp: new Date(),
        };
        setMessages(prev => [...prev, errorMessage]);
        setError(t('chat.error') || 'Failed to send message');
        setIsTyping(false);
      }
    };

    // Start sending with retry
    sendWithRetry();
  };

  // Purpose: Handle Enter key press in input.
  // Side effects: Sends message if Enter is pressed.
  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  // Purpose: Toggle chat window open/closed.
  // Side effects: Opens/closes chat, resets messages if closing.
  const toggleChat = () => {
    setIsOpen(!isOpen);
    if (isOpen) {
      setMessages([]);
      setSessionId(null);
      setError(null);
      setRetryCount(0);
    }
  };

  // Purpose: Check chatbot health on mount.
  // Side effects: Logs chatbot service status.
  useEffect(() => {
    if (isOpen) {
      checkChatbotHealth().then(health => {
        if (!health.gemini_available) {
          console.warn('Gemini API not available, using fallback mode');
        }
      }).catch(err => {
        console.error('Error checking chatbot health:', err);
      });
    }
  }, [isOpen]);

  // Purpose: Portal container for chat button to ensure it's always at viewport root.
  // Side effects: Creates portal container if it doesn't exist.
  const [portalContainer, setPortalContainer] = useState<HTMLElement | null>(null);

  useEffect(() => {
    // Purpose: Create or get portal container for chat button.
    // Side effects: Creates div element and appends to document.body.
    let container = document.getElementById('chatbot-portal-root');
    if (!container) {
      container = document.createElement('div');
      container.id = 'chatbot-portal-root';
      container.style.position = 'fixed';
      container.style.top = '0';
      container.style.left = '0';
      container.style.width = '0';
      container.style.height = '0';
      container.style.pointerEvents = 'none';
      container.style.zIndex = '9999';
      document.body.appendChild(container);
    }
    setPortalContainer(container);

    return () => {
      // Cleanup: Portal container persists for performance, only remove on unmount if needed
    };
  }, []);

  // Purpose: Floating chat button - ALWAYS positioned at bottom-right of viewport.
  // Uses React Portal to render at body root, preventing parent container interference.
  // Position: Fixed to viewport bottom-right (16px from edges on mobile, 24px on desktop).
  // Z-Index: 9999 to stay above all other UI elements.
  const chatButton = !isOpen && portalContainer ? (
    <button
      onClick={toggleChat}
      className={cn(
        // Fixed positioning to viewport bottom-right corner
        "fixed bottom-4 right-4 sm:bottom-6 sm:right-6",
        // Size: 56px (14 * 4) on mobile, responsive scaling
        "w-14 h-14 sm:w-16 sm:h-16",
        "rounded-full",
        // Primary color with hover effects
        "bg-primary hover:bg-primary-hover",
        "text-white",
        // Shadow for depth and visibility
        "shadow-lg shadow-primary/30 hover:shadow-xl hover:shadow-primary/40",
        // Flexbox centering
        "flex items-center justify-center",
        // Smooth transitions for all interactions
        "transition-all duration-300 ease-out",
        // Hover animations: scale up slightly, lift shadow
        "hover:scale-110 hover:-translate-y-1",
        // Active state: scale down for tactile feedback
        "active:scale-95",
        // Ensure button is always clickable
        "cursor-pointer",
        // Focus styles for accessibility
        "focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 focus:ring-offset-background"
      )}
      style={{
        // CRITICAL: Fixed positioning relative to viewport, not parent
        position: 'fixed',
        // Bottom-right corner with safe spacing
        bottom: '16px', // 1rem on mobile
        right: '16px',  // 1rem on mobile
        // Z-index: Highest priority to stay above all UI
        zIndex: 9999,
        // Ensure button is never clipped
        pointerEvents: 'auto',
        // Prevent any transform from parent affecting position
        transform: 'none',
      }}
      aria-label={t('chat.openChat')}
      title={t('chat.openChat')}
      type="button"
    >
      <MessageCircle 
        size={24} 
        className="sm:w-6 sm:h-6"
        aria-hidden="true"
      />
    </button>
  ) : null;

  // Purpose: Chat window overlay and container - rendered via portal when open.
  // Side effects: Displays chat interface, prevents body scroll when open.
  useEffect(() => {
    if (isOpen) {
      // Purpose: Prevent body scroll when chat is open.
      // Side effects: Adds overflow-hidden to body.
      document.body.style.overflow = 'hidden';
      return () => {
        document.body.style.overflow = '';
      };
    }
  }, [isOpen]);

  // Purpose: Chat window content - positioned at bottom-right, above chat button.
  // Side effects: Renders chat interface when isOpen is true.
  const chatWindow = isOpen && portalContainer ? (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/20 backdrop-blur-sm"
        onClick={toggleChat}
        aria-hidden="true"
        style={{ 
          pointerEvents: 'auto',
          zIndex: 9998,
        }}
      />

      {/* Chat Window Container - Fixed to bottom-right, above chat button */}
      <div 
        className="fixed flex items-end justify-end pointer-events-none"
        style={{ 
          bottom: '16px',
          right: '16px',
          // On mobile: full width minus padding, on desktop: max-width
          width: 'calc(100vw - 2rem)',
          maxWidth: '28rem', // 448px (max-w-md)
          maxHeight: 'calc(100vh - 2rem - 80px)', // Account for chat button space
          zIndex: 9999,
          pointerEvents: 'none',
        }}
      >
        {/* Chat Window */}
        <div 
          className={cn(
            "relative w-full h-[600px] max-h-[85vh]",
            "bg-background-elevated border border-border rounded-t-2xl md:rounded-2xl",
            "shadow-2xl flex flex-col",
            "animate-slide-up"
          )}
          style={{ 
            pointerEvents: 'auto',
          }}
          onClick={(e) => e.stopPropagation()}
        >
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-border">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center">
                  <Bot className="w-5 h-5 text-primary" />
                </div>
                <div>
                  <h3 className="font-semibold text-foreground">{t('chat.title')}</h3>
                  <p className="text-xs text-foreground-secondary">{t('chat.subtitle')}</p>
                </div>
              </div>
              <button
                onClick={toggleChat}
                className="p-2 rounded-lg hover:bg-background-hover text-foreground-secondary hover:text-foreground transition-colors"
                aria-label={t('chat.closeChat')}
              >
                <X size={20} />
              </button>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={cn(
                    "flex gap-3",
                    message.role === 'user' ? "justify-end" : "justify-start"
                  )}
                >
                  {message.role === 'assistant' && (
                    <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0">
                      <Bot className="w-4 h-4 text-primary" />
                    </div>
                  )}
                  <div
                    className={cn(
                      "max-w-[80%] rounded-2xl px-4 py-2.5",
                      message.role === 'user'
                        ? "bg-primary text-white"
                        : "bg-background-hover text-foreground border border-border"
                    )}
                  >
                    <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                    <p className="text-xs mt-1 opacity-70">
                      {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>
                  {message.role === 'user' && (
                    <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0">
                      <User className="w-4 h-4 text-primary" />
                    </div>
                  )}
                </div>
              ))}

              {/* Typing indicator */}
              {isTyping && (
                <div className="flex gap-3 justify-start">
                  <div className="w-8 h-8 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0">
                    <Bot className="w-4 h-4 text-primary" />
                  </div>
                  <div className="bg-background-hover border border-border rounded-2xl px-4 py-2.5">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 rounded-full bg-foreground-secondary animate-bounce" style={{ animationDelay: '0ms' }} />
                      <div className="w-2 h-2 rounded-full bg-foreground-secondary animate-bounce" style={{ animationDelay: '150ms' }} />
                      <div className="w-2 h-2 rounded-full bg-foreground-secondary animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                </div>
              )}

              {/* Error message */}
              {error && (
                <div className="flex gap-3 justify-start">
                  <div className="w-8 h-8 rounded-full bg-error/20 flex items-center justify-center flex-shrink-0">
                    <AlertCircle className="w-4 h-4 text-error" />
                  </div>
                  <div className="bg-error/10 border border-error/20 rounded-2xl px-4 py-2.5">
                    <p className="text-sm text-error">{error}</p>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-4 border-t border-border">
              <div className="flex gap-2">
                <input
                  ref={inputRef}
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder={t('chat.placeholder')}
                  className={cn(
                    "flex-1 px-4 py-2.5 rounded-lg",
                    "bg-background border border-border",
                    "text-foreground placeholder:text-foreground-tertiary",
                    "focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2",
                    "focus:ring-offset-background-elevated"
                  )}
                />
                <button
                  onClick={handleSend}
                  disabled={!inputValue.trim() || isTyping}
                  className={cn(
                    "px-4 py-2.5 rounded-lg",
                    "bg-primary hover:bg-primary-hover text-white",
                    "disabled:opacity-50 disabled:cursor-not-allowed",
                    "transition-colors",
                    "flex items-center justify-center"
                  )}
                  aria-label={t('chat.send')}
                  type="button"
                >
                  <Send size={18} />
                </button>
              </div>
              <p className="text-xs text-foreground-tertiary mt-2 text-center">
                {t('chat.hint')}
              </p>
            </div>
          </div>
        </div>
      </>
    ) : null;

  // Purpose: Render chat button and window via portal to body root.
  // This ensures they're never clipped by parent containers.
  // Returns: Portal-rendered elements or null.
  if (!portalContainer) return null;

  return (
    <>
      {createPortal(chatButton, portalContainer)}
      {createPortal(chatWindow, portalContainer)}
    </>
  );
};

