/**
 * Indexed Search Component
 * Full-text search with indexing and filtering
 */

import React, { useState, useEffect, useMemo } from 'react';
import { Search, X, Filter, SortAsc, SortDesc } from 'lucide-react';
import { cn } from '../lib/utils';

export interface SearchableItem {
  id: string;
  title: string;
  description?: string;
  tags?: string[];
  category?: string;
  [key: string]: any;
}

export interface IndexedSearchProps<T extends SearchableItem> {
  items: T[];
  onSearch?: (results: T[]) => void;
  onSelect?: (item: T) => void;
  searchFields?: (keyof T)[];
  filterFields?: {
    field: keyof T;
    label: string;
    options: string[];
  }[];
  sortOptions?: {
    field: keyof T;
    label: string;
  }[];
  placeholder?: string;
  className?: string;
}

export function IndexedSearch<T extends SearchableItem>({
  items,
  onSearch,
  onSelect,
  searchFields = ['title', 'description'],
  filterFields = [],
  sortOptions = [],
  placeholder = 'Search...',
  className,
}: IndexedSearchProps<T>) {
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState<Record<string, string>>({});
  const [sortField, setSortField] = useState<keyof T | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [showFilters, setShowFilters] = useState(false);

  // Build search index
  const searchIndex = useMemo(() => {
    return items.map(item => ({
      item,
      searchableText: searchFields
        .map(field => {
          const value = item[field];
          if (Array.isArray(value)) {
            return value.join(' ');
          }
          return String(value || '').toLowerCase();
        })
        .join(' '),
    }));
  }, [items, searchFields]);

  // Search and filter
  const results = useMemo(() => {
    let filtered = searchIndex;

    // Text search
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(({ searchableText }) =>
        searchableText.includes(query)
      );
    }

    // Apply filters
    Object.entries(filters).forEach(([field, value]) => {
      if (value) {
        filtered = filtered.filter(({ item }) => {
          const fieldValue = item[field as keyof T];
          if (Array.isArray(fieldValue)) {
            return fieldValue.includes(value);
          }
          return String(fieldValue) === value;
        });
      }
    });

    // Sort
    if (sortField) {
      filtered = [...filtered].sort((a, b) => {
        const aVal = a.item[sortField];
        const bVal = b.item[sortField];
        const comparison = String(aVal || '').localeCompare(String(bVal || ''));
        return sortDirection === 'asc' ? comparison : -comparison;
      });
    }

    return filtered.map(({ item }) => item);
  }, [searchIndex, searchQuery, filters, sortField, sortDirection]);

  // Notify parent of results
  useEffect(() => {
    if (onSearch) {
      onSearch(results);
    }
  }, [results, onSearch]);

  const handleFilterChange = (field: string, value: string) => {
    setFilters(prev => ({
      ...prev,
      [field]: value || undefined,
    }));
  };

  const clearFilters = () => {
    setFilters({});
    setSearchQuery('');
  };

  const hasActiveFilters = Object.values(filters).some(Boolean) || searchQuery.trim();

  return (
    <div className={cn('space-y-4', className)}>
      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-foreground-tertiary" size={20} />
        <input
          type="text"
          placeholder={placeholder}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-10 py-3 rounded-lg border border-border bg-background text-foreground placeholder:text-foreground-tertiary focus:outline-none focus:ring-2 focus:ring-primary"
        />
        {searchQuery && (
          <button
            onClick={() => setSearchQuery('')}
            className="absolute right-3 top-1/2 -translate-y-1/2 p-1 rounded hover:bg-background-hover"
          >
            <X size={18} />
          </button>
        )}
      </div>

      {/* Filters and Sort */}
      <div className="flex items-center gap-2 flex-wrap">
        {filterFields.length > 0 && (
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={cn(
              'flex items-center gap-2 px-4 py-2 rounded-lg border transition-colors',
              showFilters
                ? 'bg-primary text-white border-primary'
                : 'bg-background-elevated border-border hover:bg-background-hover'
            )}
          >
            <Filter size={18} />
            Filters
            {hasActiveFilters && (
              <span className="px-2 py-0.5 text-xs rounded-full bg-primary/20">
                {Object.values(filters).filter(Boolean).length}
              </span>
            )}
          </button>
        )}

        {sortOptions.length > 0 && (
          <div className="flex items-center gap-2">
            <select
              value={sortField?.toString() || ''}
              onChange={(e) => setSortField(e.target.value ? (e.target.value as keyof T) : null)}
              className="px-4 py-2 rounded-lg border border-border bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="">Sort by...</option>
              {sortOptions.map(option => (
                <option key={String(option.field)} value={String(option.field)}>
                  {option.label}
                </option>
              ))}
            </select>
            {sortField && (
              <button
                onClick={() => setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')}
                className="p-2 rounded-lg border border-border hover:bg-background-hover"
              >
                {sortDirection === 'asc' ? <SortAsc size={18} /> : <SortDesc size={18} />}
              </button>
            )}
          </div>
        )}

        {hasActiveFilters && (
          <button
            onClick={clearFilters}
            className="ml-auto px-4 py-2 text-sm text-foreground-secondary hover:text-foreground"
          >
            Clear all
          </button>
        )}
      </div>

      {/* Filter Panel */}
      {showFilters && filterFields.length > 0 && (
        <div className="p-4 rounded-lg border border-border bg-background-elevated space-y-3">
          {filterFields.map(({ field, label, options }) => (
            <div key={String(field)}>
              <label className="block text-sm font-medium text-foreground mb-2">
                {label}
              </label>
              <select
                value={filters[String(field)] || ''}
                onChange={(e) => handleFilterChange(String(field), e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value="">All</option>
                {options.map(option => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </div>
          ))}
        </div>
      )}

      {/* Results Count */}
      <div className="text-sm text-foreground-secondary">
        {results.length} {results.length === 1 ? 'result' : 'results'}
        {searchQuery && ` for "${searchQuery}"`}
      </div>

      {/* Results List */}
      <div className="space-y-2">
        {results.map((item) => (
          <div
            key={item.id}
            onClick={() => onSelect?.(item)}
            className={cn(
              'p-4 rounded-lg border border-border bg-background-elevated',
              'hover:border-primary/50 hover:bg-background-hover',
              'transition-colors cursor-pointer',
              onSelect && 'cursor-pointer'
            )}
          >
            <h3 className="font-semibold text-foreground mb-1">{item.title}</h3>
            {item.description && (
              <p className="text-sm text-foreground-secondary mb-2">{item.description}</p>
            )}
            {item.tags && item.tags.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {item.tags.map((tag, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-0.5 text-xs rounded-md bg-background-hover text-foreground-secondary"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {results.length === 0 && (
        <div className="text-center py-12 text-foreground-secondary">
          <Search size={48} className="mx-auto mb-4 opacity-50" />
          <p>No results found</p>
          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="mt-4 text-primary hover:text-primary-hover"
            >
              Clear filters
            </button>
          )}
        </div>
      )}
    </div>
  );
}

