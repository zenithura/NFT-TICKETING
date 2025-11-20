import React from 'react';
import { Skeleton } from './skeleton';
import { NFTCoinAnimation } from '../3d/NFTCoinAnimation';

export const TicketCardSkeleton: React.FC = () => {
  return (
    <div className="group bg-background-elevated rounded-xl border border-border overflow-hidden">
      {/* Image skeleton with 3D animation */}
      <div className="relative aspect-video overflow-hidden bg-background-hover flex items-center justify-center">
        {/* 3D Coin Animation while loading */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="absolute inset-0 bg-gradient-to-t from-background-elevated to-transparent opacity-40" />
          <NFTCoinAnimation />
        </div>
        {/* Price badge skeleton */}
        <div className="absolute top-3 right-3 z-10">
          <Skeleton className="h-6 w-20 rounded" />
        </div>
      </div>
      
      <div className="p-5 space-y-4">
        <div>
          <div className="flex items-center justify-between mb-2">
            <Skeleton className="h-3 w-16" />
            <Skeleton className="h-3 w-12" />
          </div>
          <Skeleton className="h-6 w-3/4 mb-1" />
        </div>

        <div className="space-y-2">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-4 w-40" />
        </div>

        <div className="pt-4 border-t border-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Skeleton className="w-5 h-5 rounded-full" />
            <Skeleton className="h-3 w-24" />
          </div>
        </div>
      </div>
    </div>
  );
};

export const EventDetailsSkeleton: React.FC = () => {
  return (
    <div className="max-w-6xl mx-auto animate-fade-in">
      <Skeleton className="h-6 w-20 mb-6" />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
        {/* Main Column */}
        <div className="lg:col-span-2 space-y-8">
          {/* Hero Image with 3D animation */}
          <div className="relative aspect-video rounded-2xl overflow-hidden border border-border bg-background-hover flex items-center justify-center">
            <div className="absolute inset-0 bg-gradient-to-t from-background-elevated to-transparent opacity-30" />
            <NFTCoinAnimation />
            <div className="absolute top-4 left-4 z-10">
              <Skeleton className="h-6 w-20 rounded-full" />
            </div>
          </div>

          <div className="space-y-6">
            <Skeleton className="h-10 w-3/4" />
            
            <div className="flex flex-wrap gap-6 pb-6 border-b border-border">
              <Skeleton className="h-5 w-32" />
              <Skeleton className="h-5 w-40" />
              <Skeleton className="h-5 w-24" />
            </div>

            <div className="space-y-4">
              <Skeleton className="h-6 w-32 mb-4" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-5/6" />
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="lg:col-span-1">
          <div className="sticky top-24 bg-background-elevated border border-border rounded-xl p-6 space-y-6 shadow-2xl">
            <div>
              <Skeleton className="h-4 w-24 mb-2" />
              <Skeleton className="h-10 w-32" />
            </div>

            <div className="p-4 bg-background-hover rounded-lg border border-border space-y-2">
              <div className="flex justify-between">
                <Skeleton className="h-4 w-20" />
                <Skeleton className="h-4 w-16" />
              </div>
              <Skeleton className="h-2 w-full rounded-full" />
            </div>

            <div className="space-y-4">
              <Skeleton className="h-12 w-full rounded-lg" />
              
              <div className="space-y-2 pt-4 border-t border-border">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-5 w-full" />
              </div>

              <Skeleton className="h-12 w-full rounded-lg" />
              <Skeleton className="h-4 w-48 mx-auto" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};