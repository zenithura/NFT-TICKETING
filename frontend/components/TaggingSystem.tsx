/**
 * Tagging System Component
 * UI for managing and applying tags to resources
 */

import React, { useState, useEffect } from 'react';
import { X, Plus, Tag, Search } from 'lucide-react';
import { cn } from '../lib/utils';

export interface TagItem {
  id: string;
  name: string;
  color?: string;
  count?: number;
}

export interface TaggingSystemProps {
  tags: TagItem[];
  selectedTags: string[];
  onTagsChange: (tagIds: string[]) => void;
  onCreateTag?: (name: string, color?: string) => void;
  onDeleteTag?: (tagId: string) => void;
  maxTags?: number;
  className?: string;
}

export const TaggingSystem: React.FC<TaggingSystemProps> = ({
  tags,
  selectedTags,
  onTagsChange,
  onCreateTag,
  onDeleteTag,
  maxTags,
  className,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newTagName, setNewTagName] = useState('');
  const [newTagColor, setNewTagColor] = useState('#F7931A');

  const filteredTags = tags.filter(tag =>
    tag.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const availableTags = filteredTags.filter(tag => !selectedTags.includes(tag.id));
  const selectedTagItems = tags.filter(tag => selectedTags.includes(tag.id));

  const handleToggleTag = (tagId: string) => {
    if (selectedTags.includes(tagId)) {
      onTagsChange(selectedTags.filter(id => id !== tagId));
    } else {
      if (maxTags && selectedTags.length >= maxTags) {
        return;
      }
      onTagsChange([...selectedTags, tagId]);
    }
  };

  const handleCreateTag = () => {
    if (newTagName.trim() && onCreateTag) {
      onCreateTag(newTagName.trim(), newTagColor);
      setNewTagName('');
      setShowCreateForm(false);
    }
  };

  const predefinedColors = [
    '#F7931A', '#EF4444', '#10B981', '#3B82F6',
    '#8B5CF6', '#EC4899', '#F59E0B', '#6B7280',
  ];

  return (
    <div className={cn('space-y-4', className)}>
      {/* Selected Tags */}
      {selectedTagItems.length > 0 && (
        <div>
          <label className="block text-sm font-medium text-foreground mb-2">
            Selected Tags
          </label>
          <div className="flex flex-wrap gap-2">
            {selectedTagItems.map(tag => (
              <div
                key={tag.id}
                className={cn(
                  'inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm',
                  'bg-primary/10 text-primary border border-primary/20'
                )}
                style={tag.color ? { borderColor: tag.color, backgroundColor: `${tag.color}20` } : {}}
              >
                <Tag size={14} />
                <span>{tag.name}</span>
                {tag.count !== undefined && (
                  <span className="text-xs opacity-70">({tag.count})</span>
                )}
                <button
                  onClick={() => handleToggleTag(tag.id)}
                  className="ml-1 hover:opacity-70"
                >
                  <X size={14} />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Search and Filter */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-foreground-tertiary" size={18} />
        <input
          type="text"
          placeholder="Search tags..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-10 pr-4 py-2 rounded-lg border border-border bg-background text-foreground placeholder:text-foreground-tertiary focus:outline-none focus:ring-2 focus:ring-primary"
        />
      </div>

      {/* Available Tags */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="block text-sm font-medium text-foreground">
            Available Tags
          </label>
          {onCreateTag && (
            <button
              onClick={() => setShowCreateForm(!showCreateForm)}
              className="text-sm text-primary hover:text-primary-hover flex items-center gap-1"
            >
              <Plus size={16} />
              Create Tag
            </button>
          )}
        </div>

        {/* Create Tag Form */}
        {showCreateForm && onCreateTag && (
          <div className="mb-4 p-4 rounded-lg border border-border bg-background-elevated">
            <div className="space-y-3">
              <input
                type="text"
                placeholder="Tag name"
                value={newTagName}
                onChange={(e) => setNewTagName(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
              />
              <div className="flex items-center gap-2">
                <span className="text-sm text-foreground-secondary">Color:</span>
                <div className="flex gap-2">
                  {predefinedColors.map(color => (
                    <button
                      key={color}
                      onClick={() => setNewTagColor(color)}
                      className={cn(
                        'w-6 h-6 rounded-full border-2 transition-all',
                        newTagColor === color ? 'border-foreground scale-110' : 'border-border'
                      )}
                      style={{ backgroundColor: color }}
                    />
                  ))}
                </div>
                <input
                  type="color"
                  value={newTagColor}
                  onChange={(e) => setNewTagColor(e.target.value)}
                  className="w-8 h-8 rounded cursor-pointer"
                />
              </div>
              <div className="flex gap-2">
                <button
                  onClick={handleCreateTag}
                  className="px-4 py-2 rounded-lg bg-primary text-white hover:bg-primary-hover"
                >
                  Create
                </button>
                <button
                  onClick={() => {
                    setShowCreateForm(false);
                    setNewTagName('');
                  }}
                  className="px-4 py-2 rounded-lg border border-border hover:bg-background-hover"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Tags List */}
        <div className="flex flex-wrap gap-2 max-h-48 overflow-y-auto p-2 rounded-lg border border-border bg-background-elevated">
          {availableTags.length === 0 ? (
            <p className="text-sm text-foreground-tertiary w-full text-center py-4">
              {searchQuery ? 'No tags found' : 'No tags available'}
            </p>
          ) : (
            availableTags.map(tag => (
              <button
                key={tag.id}
                onClick={() => handleToggleTag(tag.id)}
                className={cn(
                  'inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm',
                  'border border-border hover:border-primary/50',
                  'bg-background hover:bg-background-hover',
                  'text-foreground-secondary hover:text-foreground',
                  'transition-colors'
                )}
              >
                <Tag size={14} style={tag.color ? { color: tag.color } : {}} />
                <span>{tag.name}</span>
                {tag.count !== undefined && (
                  <span className="text-xs opacity-70">({tag.count})</span>
                )}
                {onDeleteTag && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteTag(tag.id);
                    }}
                    className="ml-1 hover:text-error"
                  >
                    <X size={14} />
                  </button>
                )}
              </button>
            ))
          )}
        </div>
      </div>

      {/* Max Tags Warning */}
      {maxTags && selectedTags.length >= maxTags && (
        <p className="text-sm text-warning">
          Maximum {maxTags} tags allowed
        </p>
      )}
    </div>
  );
};

