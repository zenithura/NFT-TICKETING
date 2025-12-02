// File header: Web3/NFT ticketing chatbot assistant component.
// Provides interactive chat interface for answering questions about NFT ticketing, blockchain, and Web3.

import React, { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { MessageCircle, X, Send, Bot, User } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { cn } from '../lib/utils';

// Purpose: Message type definition for chat messages.
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

// Purpose: Web3/NFT ticketing knowledge base responses.
// Returns: Response string based on user query.
// Side effects: None (pure function).
const getChatbotResponse = (userMessage: string, language: string = 'en'): string => {
  const message = userMessage.toLowerCase().trim();
  
  // Greeting responses
  if (message.match(/^(hi|hello|hey|greetings|good morning|good afternoon|good evening)/)) {
    return language === 'az' 
      ? "Salam! NFT biletləmə və blokçeyn məsləhətçisiniz. Nə haqqında bilmək istəyirsiniz?"
      : "Welcome! I'm your blockchain and NFT ticketing assistant. What would you like to know?";
  }

  // NFT Ticketing topics
  if (message.match(/nft.*ticket|ticket.*nft|how.*mint|mint.*ticket/)) {
    return language === 'az'
      ? "NFT biletləri ERC-721 və ya ERC-1155 standartlarından istifadə edərək yaradılır. Biletlər ağıllı müqavilədə zərb edilir (mint edilir) və hər bilet unikal token ID-yə malikdir. Metadata IPFS-də saxlanılır və bilet məlumatlarını (tədbir adı, tarix, yer və s.) ehtiva edir."
      : "NFT tickets are created using ERC-721 or ERC-1155 standards. Tickets are minted in a smart contract, with each ticket having a unique token ID. Metadata is stored on IPFS and contains ticket information (event name, date, venue, etc.).";
  }

  if (message.match(/verify|ownership|check.*ticket|scan.*ticket/)) {
    return language === 'az'
      ? "Bilet sahibliyini yoxlamaq üçün, skaner ağıllı müqavilədə ownerOf(tokenId) funksiyasını çağırır. QR kod wallet imzası ilə birləşdirilə bilər. Hər skan zamanı biletin istifadə olunub-olunmadığını yoxlamaq üçün on-chain vəziyyət yoxlanılır."
      : "To verify ticket ownership, the scanner calls the ownerOf(tokenId) function in the smart contract. QR codes can be combined with wallet signatures. Each scan checks the on-chain state to verify if the ticket has been used.";
  }

  if (message.match(/fraud|anti.*fraud|security|prevent.*fraud/)) {
    return language === 'az'
      ? "NFT biletlərdə anti-fraud xüsusiyyətləri: 1) Soulbound tokenlər (transfer edilə bilməz), 2) KYC inteqrasiyası, 3) Hər bilet yalnız bir dəfə skan edilə bilər, 4) On-chain istifadə statusu, 5) ML əsaslı anomaliya aşkarlama. Bu platformada hər bilet yalnız bir dəfə istifadə edilə bilər."
      : "Anti-fraud features in NFT tickets: 1) Soulbound tokens (non-transferable), 2) KYC integration, 3) Each ticket can only be scanned once, 4) On-chain usage status, 5) ML-based anomaly detection. On this platform, each ticket can only be used once.";
  }

  if (message.match(/resale|resell|sell.*ticket|marketplace/)) {
    return language === 'az'
      ? "NFT biletləri ikinci əl bazarında satıla bilər. Ağıllı müqavilə listTicket() funksiyası ilə biletləri bazar üçün siyahıya alır. buyTicket() funksiyası satın alma prosesini idarə edir. Təşkilatçılar hər satışdan royalty (məsələn, 5%) ala bilər. Bütün satışlar blokçeyndə qeydə alınır."
      : "NFT tickets can be resold on the secondary marketplace. The smart contract lists tickets for sale using listTicket(). The buyTicket() function handles purchases. Organizers can receive royalties (e.g., 5%) on each sale. All sales are recorded on-chain.";
  }

  if (message.match(/gas|fee|cost|expensive/)) {
    return language === 'az'
      ? "Gas xərcləri blokçeyn şəbəkəsindən asılıdır. Polygon kimi Layer 2 həlləri Ethereum-dan daha ucuzdur. Bu platforma Polygon istifadə edir. Bilet zərb etmək təxminən $0.01-0.05, satış isə $0.02-0.10 arası ola bilər. Batch minting bir neçə bilet üçün xərcləri azaldır."
      : "Gas fees depend on the blockchain network. Layer 2 solutions like Polygon are cheaper than Ethereum. This platform uses Polygon. Minting a ticket costs approximately $0.01-0.05, while resale costs $0.02-0.10. Batch minting reduces costs for multiple tickets.";
  }

  // Blockchain technology topics
  if (message.match(/erc-721|erc-1155|erc-20|standard/)) {
    return language === 'az'
      ? "ERC-721: Hər token unikaldır (NFT). ERC-1155: Çox token standartı, eyni müqavilədə NFT və FT. ERC-20: Fungible tokenlər (kriptovalyuta). NFT biletləri üçün ERC-721 və ya ERC-1155 istifadə olunur. ERC-1155 daha çevikdir çünki eyni müqavilədə müxtəlif bilet növləri ola bilər."
      : "ERC-721: Each token is unique (NFT). ERC-1155: Multi-token standard, NFTs and FTs in the same contract. ERC-20: Fungible tokens (cryptocurrency). NFT tickets use ERC-721 or ERC-1155. ERC-1155 is more flexible as it allows different ticket types in the same contract.";
  }

  if (message.match(/layer.*2|l2|polygon|arbitrum|optimism|rollup/)) {
    return language === 'az'
      ? "Layer 2 həlləri Ethereum-un miqyasını artırır və xərcləri azaldır. Polygon: Sidechain, çox aşağı gas xərcləri. Arbitrum & Optimism: Optimistic rollups. zkSync: Zero-knowledge rollup. Bu platforma Polygon istifadə edir çünki bilet əməliyyatları üçün sürətli və ucuzdur."
      : "Layer 2 solutions scale Ethereum and reduce costs. Polygon: Sidechain with very low gas fees. Arbitrum & Optimism: Optimistic rollups. zkSync: Zero-knowledge rollup. This platform uses Polygon because it's fast and cheap for ticket operations.";
  }

  if (message.match(/ipfs|metadata|arweave|storage/)) {
    return language === 'az'
      ? "NFT metadata IPFS (InterPlanetary File System) və ya Arweave-də saxlanılır. IPFS: P2P şəbəkə, content-addressed. Arweave: Daimi, bir dəfə ödəniş. Metadata JSON formatındadır və bilet məlumatlarını (ad, təsvir, şəkil, atributlar) ehtiva edir. Ağıllı müqavilədə yalnız tokenURI saxlanılır."
      : "NFT metadata is stored on IPFS (InterPlanetary File System) or Arweave. IPFS: P2P network, content-addressed. Arweave: Permanent, one-time payment. Metadata is in JSON format and contains ticket information (name, description, image, attributes). Only the tokenURI is stored in the smart contract.";
  }

  // Wallet topics
  if (message.match(/wallet|metamask|connect.*wallet|walletconnect/)) {
    return language === 'az'
      ? "Cüzdanlar (MetaMask, WalletConnect, Phantom) istifadəçilərin kriptovalyuta və NFT-ləri idarə etməsinə imkan verir. Bu platforma MetaMask və WalletConnect dəstəkləyir. Cüzdan qoşulduqda, frontend Web3 provider vasitəsilə ağıllı müqavilə ilə qarşılıqlı əlaqə qurur. İstifadəçi əməliyyatları imzalamaq üçün cüzdanından təsdiq istəyir."
      : "Wallets (MetaMask, WalletConnect, Phantom) allow users to manage cryptocurrency and NFTs. This platform supports MetaMask and WalletConnect. When a wallet connects, the frontend interacts with smart contracts via a Web3 provider. Users must approve transactions from their wallet.";
  }

  // Developer topics
  if (message.match(/smart.*contract|solidity|deploy|contract/)) {
    return language === 'az'
      ? "Ağıllı müqavilələr Solidity-də yazılır və Hardhat, Truffle və ya Foundry ilə yerləşdirilir. Bu platforma TicketManager.sol müqaviləsindən istifadə edir. Əsas funksiyalar: mintTicket(), listTicket(), buyTicket(), scanTicket(). Müqavilə ERC-721 standartından miras alır və AccessControl, ReentrancyGuard istifadə edir."
      : "Smart contracts are written in Solidity and deployed with Hardhat, Truffle, or Foundry. This platform uses the TicketManager.sol contract. Key functions: mintTicket(), listTicket(), buyTicket(), scanTicket(). The contract inherits from ERC-721 and uses AccessControl, ReentrancyGuard.";
  }

  if (message.match(/api|backend|integration|how.*integrate/)) {
    return language === 'az'
      ? "Backend API-lər ağıllı müqavilə ilə qarşılıqlı əlaqə üçün Web3.js və ya Ethers.js istifadə edir. Frontend wallet qoşur və istifadəçi əməliyyatları təsdiqləyir. Backend yalnız oxu əməliyyatları (bilet məlumatlarını almaq) üçün istifadə olunur. Mint və satış kimi yazma əməliyyatları birbaşa cüzdandan edilir."
      : "Backend APIs use Web3.js or Ethers.js to interact with smart contracts. The frontend connects wallets and users approve transactions. The backend is used only for read operations (fetching ticket info). Write operations like minting and selling are done directly from the wallet.";
  }

  // Default response
  return language === 'az'
    ? "NFT biletləmə, blokçeyn texnologiyası, ağıllı müqavilələr, cüzdan inteqrasiyası və ya platforma funksionallığı haqqında sual verə bilərsiniz. Məsələn: 'NFT biletləri necə zərb edilir?', 'Bilet sahibliyini necə yoxlamaq olar?', 'Gas xərcləri nə qədərdir?'"
    : "You can ask about NFT ticketing, blockchain technology, smart contracts, wallet integration, or platform functionality. For example: 'How are NFT tickets minted?', 'How to verify ticket ownership?', 'What are the gas fees?'";
};

// Purpose: ChatBot component with floating button and chat window.
// Returns: JSX with chat interface.
// Side effects: Manages chat state, handles user messages, generates responses.
export const ChatBot: React.FC = () => {
  const { t, i18n } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
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

  // Purpose: Handle sending a message.
  // Side effects: Adds user message, generates and adds bot response.
  const handleSend = () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputValue.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsTyping(true);

    // Purpose: Simulate typing delay and generate response.
    // Side effects: Adds bot response after delay.
    setTimeout(() => {
      const response = getChatbotResponse(userMessage.content, i18n.language);
      const botMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, botMessage]);
      setIsTyping(false);
    }, 500);
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
    }
  };

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
                  disabled={!inputValue.trim()}
                  className={cn(
                    "px-4 py-2.5 rounded-lg",
                    "bg-primary hover:bg-primary-hover text-white",
                    "disabled:opacity-50 disabled:cursor-not-allowed",
                    "transition-colors",
                    "flex items-center justify-center"
                  )}
                  aria-label={t('chat.send')}
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

