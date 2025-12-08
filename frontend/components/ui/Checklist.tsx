/**
 * Checklist Component
 * Styled checklist with checkmarks
 */

import React from 'react';
import { Check } from 'lucide-react';
import { cn } from '../../lib/utils';

export interface ChecklistItem {
  id: string;
  label: string;
  checked: boolean;
  disabled?: boolean;
}

export interface ChecklistProps {
  items: ChecklistItem[];
  onChange: (id: string, checked: boolean) => void;
  className?: string;
}

export const Checklist: React.FC<ChecklistProps> = ({ items, onChange, className }) => {
  return (
    <div className={cn('space-y-2', className)}>
      {items.map((item) => (
        <label
          key={item.id}
          className={cn(
            'flex items-center gap-3 p-3 rounded-lg border border-border cursor-pointer transition-colors',
            item.checked && 'bg-primary/10 border-primary/20',
            item.disabled && 'opacity-50 cursor-not-allowed',
            !item.disabled && 'hover:bg-background-hover'
          )}
        >
          <div
            className={cn(
              'flex items-center justify-center w-5 h-5 rounded border-2 transition-all',
              item.checked
                ? 'bg-primary border-primary'
                : 'border-border bg-background'
            )}
          >
            {item.checked && <Check size={14} className="text-white" />}
          </div>
          <input
            type="checkbox"
            checked={item.checked}
            onChange={(e) => onChange(item.id, e.target.checked)}
            disabled={item.disabled}
            className="sr-only"
          />
          <span className="text-foreground flex-1">{item.label}</span>
        </label>
      ))}
    </div>
  );
};

