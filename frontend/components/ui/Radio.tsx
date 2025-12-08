/**
 * Radio Component
 * Accessible radio button group
 */

import React from 'react';
import { cn } from '../../lib/utils';

export interface RadioGroupProps {
  value: string;
  onChange: (value: string) => void;
  children: React.ReactNode;
  className?: string;
  name?: string;
}

export const RadioGroup: React.FC<RadioGroupProps> = ({
  value,
  onChange,
  children,
  className,
  name = 'radio-group',
}) => {
  return (
    <div className={cn('space-y-2', className)} role="radiogroup">
      {React.Children.map(children, (child) => {
        if (React.isValidElement(child)) {
          return React.cloneElement(child, {
            ...child.props,
            name,
            checked: child.props.value === value,
            onChange: () => onChange(child.props.value),
          } as any);
        }
        return child;
      })}
    </div>
  );
};

export interface RadioProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  value: string;
}

export const Radio: React.FC<RadioProps> = ({ label, className, ...props }) => {
  return (
    <label className={cn('flex items-center gap-2 cursor-pointer', className)}>
      <input
        type="radio"
        className="w-4 h-4 text-primary border-border focus:ring-primary focus:ring-offset-0"
        {...props}
      />
      {label && <span className="text-foreground">{label}</span>}
    </label>
  );
};

