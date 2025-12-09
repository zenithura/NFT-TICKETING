/**
 * Workspace Management Page
 * Admin page for managing workspaces, projects, and resources
 */

import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { 
  Folder, 
  Plus, 
  Search, 
  Filter, 
  MoreVertical,
  Edit,
  Trash2,
  Settings,
  Users,
  Calendar
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Modal } from '../components/ui/Modal';
import { Input } from '../components/ui/Input';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../components/ui/Tabs';
import { BentoGrid, BentoCard } from '../components/ui/BentoGrid';
import { cn } from '../lib/utils';

interface Workspace {
  id: string;
  name: string;
  description: string;
  members: number;
  projects: number;
  createdAt: string;
  updatedAt: string;
  tags: string[];
}

export const WorkspaceManagement: React.FC = () => {
  const { t } = useTranslation();
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedWorkspace, setSelectedWorkspace] = useState<Workspace | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [loading, setLoading] = useState(false);

  // Mock data - replace with API call
  useEffect(() => {
    setWorkspaces([
      {
        id: '1',
        name: 'Production Workspace',
        description: 'Main production environment',
        members: 12,
        projects: 8,
        createdAt: '2024-01-15',
        updatedAt: '2025-01-30',
        tags: ['production', 'critical'],
      },
      {
        id: '2',
        name: 'Development Workspace',
        description: 'Development and testing environment',
        members: 6,
        projects: 15,
        createdAt: '2024-02-01',
        updatedAt: '2025-01-29',
        tags: ['development', 'testing'],
      },
    ]);
  }, []);

  const filteredWorkspaces = workspaces.filter(ws =>
    ws.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    ws.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
    ws.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const handleCreateWorkspace = (data: Partial<Workspace>) => {
    const newWorkspace: Workspace = {
      id: Date.now().toString(),
      name: data.name || '',
      description: data.description || '',
      members: 0,
      projects: 0,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
      tags: data.tags || [],
    };
    setWorkspaces([...workspaces, newWorkspace]);
    setIsCreateModalOpen(false);
  };

  const handleEditWorkspace = (data: Partial<Workspace>) => {
    if (!selectedWorkspace) return;
    setWorkspaces(workspaces.map(ws =>
      ws.id === selectedWorkspace.id
        ? { ...ws, ...data, updatedAt: new Date().toISOString() }
        : ws
    ));
    setIsEditModalOpen(false);
    setSelectedWorkspace(null);
  };

  const handleDeleteWorkspace = (id: string) => {
    if (confirm('Are you sure you want to delete this workspace?')) {
      setWorkspaces(workspaces.filter(ws => ws.id !== id));
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-foreground mb-2">Workspace Management</h1>
          <p className="text-foreground-secondary">Manage workspaces, projects, and team resources</p>
        </div>
        <Button onClick={() => setIsCreateModalOpen(true)}>
          <Plus size={20} className="mr-2" />
          Create Workspace
        </Button>
      </div>

      {/* Search and Filters */}
      <div className="mb-6 flex gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-foreground-tertiary" size={20} />
          <input
            type="text"
            placeholder="Search workspaces..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-lg border border-border bg-background text-foreground placeholder:text-foreground-tertiary focus:outline-none focus:ring-2 focus:ring-primary"
          />
        </div>
        <Button variant="outline">
          <Filter size={20} className="mr-2" />
          Filters
        </Button>
      </div>

      {/* Workspaces Grid */}
      <BentoGrid columns={3}>
        {filteredWorkspaces.map((workspace) => (
          <BentoCard key={workspace.id} span={1}>
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-primary/10">
                  <Folder className="text-primary" size={24} />
                </div>
                <div>
                  <h3 className="font-semibold text-foreground">{workspace.name}</h3>
                  <p className="text-sm text-foreground-secondary">{workspace.description}</p>
                </div>
              </div>
              <button
                onClick={() => {
                  setSelectedWorkspace(workspace);
                  setIsEditModalOpen(true);
                }}
                className="p-2 rounded-lg hover:bg-background-hover text-foreground-secondary"
              >
                <MoreVertical size={20} />
              </button>
            </div>

            <div className="flex items-center gap-4 mb-4 text-sm text-foreground-secondary">
              <div className="flex items-center gap-1">
                <Users size={16} />
                <span>{workspace.members} members</span>
              </div>
              <div className="flex items-center gap-1">
                <Folder size={16} />
                <span>{workspace.projects} projects</span>
              </div>
            </div>

            <div className="flex flex-wrap gap-2 mb-4">
              {workspace.tags.map((tag) => (
                <span
                  key={tag}
                  className="px-2 py-1 text-xs rounded-md bg-background-hover text-foreground-secondary"
                >
                  {tag}
                </span>
              ))}
            </div>

            <div className="flex items-center justify-between pt-4 border-t border-border">
              <div className="text-xs text-foreground-tertiary">
                Updated {new Date(workspace.updatedAt).toLocaleDateString()}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    setSelectedWorkspace(workspace);
                    setIsEditModalOpen(true);
                  }}
                  className="p-2 rounded-lg hover:bg-background-hover text-foreground-secondary"
                >
                  <Edit size={16} />
                </button>
                <button
                  onClick={() => handleDeleteWorkspace(workspace.id)}
                  className="p-2 rounded-lg hover:bg-error/10 text-error"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          </BentoCard>
        ))}
      </BentoGrid>

      {/* Create Workspace Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Create Workspace"
        size="lg"
      >
        <WorkspaceForm
          onSubmit={handleCreateWorkspace}
          onCancel={() => setIsCreateModalOpen(false)}
        />
      </Modal>

      {/* Edit Workspace Modal */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => {
          setIsEditModalOpen(false);
          setSelectedWorkspace(null);
        }}
        title="Edit Workspace"
        size="lg"
      >
        {selectedWorkspace && (
          <WorkspaceForm
            workspace={selectedWorkspace}
            onSubmit={handleEditWorkspace}
            onCancel={() => {
              setIsEditModalOpen(false);
              setSelectedWorkspace(null);
            }}
          />
        )}
      </Modal>
    </div>
  );
};

interface WorkspaceFormProps {
  workspace?: Workspace;
  onSubmit: (data: Partial<Workspace>) => void;
  onCancel: () => void;
}

const WorkspaceForm: React.FC<WorkspaceFormProps> = ({ workspace, onSubmit, onCancel }) => {
  const [name, setName] = useState(workspace?.name || '');
  const [description, setDescription] = useState(workspace?.description || '');
  const [tags, setTags] = useState(workspace?.tags.join(', ') || '');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit({
      name,
      description,
      tags: tags.split(',').map(t => t.trim()).filter(Boolean),
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium text-foreground mb-2">
          Workspace Name
        </label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          className="w-full px-4 py-2 rounded-lg border border-border bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-foreground mb-2">
          Description
        </label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={4}
          className="w-full px-4 py-2 rounded-lg border border-border bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-foreground mb-2">
          Tags (comma-separated)
        </label>
        <input
          type="text"
          value={tags}
          onChange={(e) => setTags(e.target.value)}
          placeholder="production, critical, development"
          className="w-full px-4 py-2 rounded-lg border border-border bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
        />
      </div>

      <div className="flex justify-end gap-3 pt-4">
        <Button type="button" variant="outline" onClick={onCancel}>
          Cancel
        </Button>
        <Button type="submit">
          {workspace ? 'Update' : 'Create'} Workspace
        </Button>
      </div>
    </form>
  );
};

