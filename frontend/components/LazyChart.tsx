/**
 * LazyChart Component
 * Dynamically imports BarChartComponent to reduce initial bundle size
 * FIXED: Properly handles React context by lazy loading a module that imports recharts normally
 * CRITICAL: This approach ensures React is available when recharts initializes
 */
import React, { Suspense, lazy } from 'react';

// Lazy load the chart component module - this ensures React context is properly available
// when recharts components are imported and rendered
// CRITICAL: Import the module file which has normal recharts imports - React will be available
const BarChartComponentLazy = lazy(() => 
  import('./BarChartComponent').then(module => ({
    default: module.default || module.BarChartComponent
  })).catch((error) => {
    console.error('Failed to load BarChartComponent:', error);
    // Return a fallback component
    return {
      default: ({ data }: { data: any[] }) => (
        <div className="flex items-center justify-center w-full h-full text-error text-sm">
          Failed to load chart component
        </div>
      )
    };
  })
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
              <div className="text-foreground-secondary animate-pulse">Loading chart...</div>
            </div>
          }
        >
          <BarChartComponentLazy data={data} />
        </Suspense>
    );
};

export default LazyChart;
