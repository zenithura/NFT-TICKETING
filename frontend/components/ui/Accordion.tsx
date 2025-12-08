/**
 * Accordion Component
 * Collapsible content sections
 */

import React, { useState } from 'react';
import { ChevronDown } from 'lucide-react';
import { cn } from '../../lib/utils';

export interface AccordionItemProps {
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}

export const AccordionItem: React.FC<AccordionItemProps> = ({
  title,
  children,
  defaultOpen = false,
}) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="border-b border-border">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 text-left hover:bg-background-hover transition-colors"
        aria-expanded={isOpen}
      >
        <span className="font-medium text-foreground">{title}</span>
        <ChevronDown
          className={cn(
            'text-foreground-secondary transition-transform duration-200',
            isOpen && 'transform rotate-180'
          )}
          size={20}
        />
      </button>
      {isOpen && (
        <div className="p-4 pt-0 text-foreground-secondary">
          {children}
        </div>
      )}
    </div>
  );
};

export interface AccordionProps {
  children: React.ReactNode;
  className?: string;
}

export const Accordion: React.FC<AccordionProps> = ({ children, className }) => {
  return (
    <div className={cn('border border-border rounded-lg overflow-hidden', className)}>
      {children}
    </div>
  );
};

