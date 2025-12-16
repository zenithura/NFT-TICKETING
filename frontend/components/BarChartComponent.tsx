/**
 * BarChart Component
 * Direct import of recharts to ensure React context is properly available
 * This file is imported lazily to reduce initial bundle size
 * CRITICAL: Normal imports ensure React is available when recharts components initialize
 * 
 * IMPORTANT: This file uses static imports (not dynamic) so React is guaranteed to be
 * available when recharts components are initialized. The lazy loading happens at the
 * module level (via LazyChart.tsx), not at the import level.
 */
import * as React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

interface BarChartComponentProps {
  data: any[];
}

const BarChartComponent: React.FC<BarChartComponentProps> = ({ data }) => {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data}>
        <XAxis dataKey="name" stroke="#5A5A5A" fontSize={12} tickLine={false} axisLine={false} />
        <YAxis stroke="#5A5A5A" fontSize={12} tickLine={false} axisLine={false} />
        <Tooltip
          contentStyle={{ 
            backgroundColor: 'var(--color-background-elevated)', 
            border: '1px solid var(--color-border)', 
            borderRadius: '8px', 
            color: 'var(--color-foreground)' 
          }}
          cursor={{ fill: 'var(--color-background-hover)' }}
        />
        <Bar dataKey="sales" fill="#F7931A" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
};

export default BarChartComponent;

