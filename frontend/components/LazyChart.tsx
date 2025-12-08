/**
 * LazyChart Component
 * Dynamically imports recharts to reduce initial bundle size
 */
import React, { Suspense, lazy } from 'react';

// Lazy load recharts - it's a heavy library (~500KB)
const BarChartComponent = lazy(() => 
  import('recharts').then(module => ({
    default: ({ data }: { data: any[] }) => {
      const { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } = module;
      return (
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <XAxis dataKey="name" stroke="#5A5A5A" fontSize={12} tickLine={false} axisLine={false} />
            <YAxis stroke="#5A5A5A" fontSize={12} tickLine={false} axisLine={false} />
            <Tooltip
              contentStyle={{ backgroundColor: '#202020', border: '1px solid #2F2F2F', borderRadius: '8px', color: '#EFEFEF' }}
              cursor={{ fill: '#252525' }}
            />
            <Bar dataKey="sales" fill="#F7931A" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      );
    },
  }))
);

interface LazyChartProps {
    data: any[];
}

const LazyChart: React.FC<LazyChartProps> = ({ data }) => {
    return (
        <Suspense 
          fallback={
            <div 
              className="flex items-center justify-center w-full h-full"
              style={{ minHeight: '300px' }}
              data-cy="chart-loading"
            >
              <div className="text-foreground-secondary">Loading chart...</div>
            </div>
          }
        >
          <BarChartComponent data={data} />
        </Suspense>
    );
};

export default LazyChart;
