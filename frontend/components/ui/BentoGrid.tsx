/**
 * Bento Grid Component
 * Modern grid layout with varying card sizes
 */

import React from 'react';
import { cn } from '../../lib/utils';

export interface BentoGridProps {
  children: React.ReactNode;
  className?: string;
  columns?: 2 | 3 | 4;
}

export const BentoGrid: React.FC<BentoGridProps> = ({
  children,
  className,
  columns = 3,
}) => {
  const gridCols = {
    2: 'grid-cols-1 md:grid-cols-2',
    3: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3',
    4: 'grid-cols-1 md:grid-cols-2 lg:grid-cols-4',
  };

  return (
    <div className={cn('grid gap-4', gridCols[columns], className)}>
      {children}
    </div>
  );
};

export interface BentoCardProps {
  children: React.ReactNode;
  className?: string;
  span?: 1 | 2; // Column span
  rowSpan?: 1 | 2; // Row span
}

export const BentoCard: React.FC<BentoCardProps> = ({
  children,
  className,
  span = 1,
  rowSpan = 1,
}) => {
  const colSpan = span === 2 ? 'md:col-span-2' : '';
  const rowSpanClass = rowSpan === 2 ? 'md:row-span-2' : '';

  return (
    <div
      className={cn(
        'bg-background-elevated rounded-xl border border-border p-6',
        'hover:border-primary/50 transition-all duration-300',
        colSpan,
        rowSpanClass,
        className
      )}
    >
      {children}
    </div>
  );
};

