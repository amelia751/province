"use client";

import React, { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import {
  Folder,
  File,
  ChevronRight,
  ChevronDown,
  Search,
  MoreHorizontal,
  Plus,
  Clock,
  AlertTriangle,
  CheckCircle,
  Circle,
  Bot,
  Briefcase,
  Calculator,
  Shield,
  FileText,
  Sparkles,
  ArrowLeft
} from "lucide-react";

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';

// Import types and mock data
import {
  AIMatter,
  AIFolder,
  AIDocument,
  PracticeArea,
  MatterStatus,
  MatterPriority,
  ExplorerFilter,
  AIActionEvent,
  MatterSelectionEvent,
  DocumentSelectionEvent,
  ChatRequestEvent
} from './types';
import { mockAIMatters, mockFilterOptions } from './mock-data';

interface EnhancedExplorerPanelProps {
  selectedProject?: AIMatter | null;
  onDocumentSelect?: (document: AIDocument, matterId: string) => void;
  onAIAction?: (action: AIActionEvent) => void;
  onChatRequest?: (request: ChatRequestEvent) => void;
  onBackToProjects?: () => void;
}

// Practice area icons
const practiceAreaIcons = {
  legal: Briefcase,
  accounting: Calculator,
  tax: FileText,
  compliance: Shield
};

// Status indicators
const statusColors = {
  active: 'text-green-600 bg-green-50',
  pending: 'text-yellow-600 bg-yellow-50',
  completed: 'text-blue-600 bg-blue-50',
  archived: 'text-gray-600 bg-gray-50'
};

const priorityColors = {
  high: 'text-red-600',
  medium: 'text-yellow-600',
  low: 'text-green-600'
};

// Matter Tree Node Component
const MatterTreeNode: React.FC<{
  matter: AIMatter;
  onSelect: (matter: AIMatter) => void;
  onDocumentSelect: (document: AIDocument, matterId: string) => void;
  onAIAction: (action: AIActionEvent) => void;
  onChatRequest: (request: ChatRequestEvent) => void;
}> = ({ matter, onSelect, onDocumentSelect, onAIAction, onChatRequest }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showActions, setShowActions] = useState(false);

  const PracticeIcon = practiceAreaIcons[matter.practiceArea];
  const hasUpcomingDeadlines = matter.deadlines.some(d =>
    !d.completed && new Date(d.dueDate) <= new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)
  );

  const handleToggle = () => {
    setIsExpanded(!isExpanded);
    if (!isExpanded) {
      onSelect(matter);
    }
  };

  const handleRightClick = (e: React.MouseEvent) => {
    e.preventDefault();
    setShowActions(!showActions);
  };

  const handleAIAction = (actionId: string) => {
    const action = matter.suggestedActions.find(a => a.id === actionId);
    if (action) {
      onAIAction({
        type: 'ai-action-triggered',
        action,
        matterId: matter.id,
        context: { matter }
      });
    }
    setShowActions(false);
  };

  const handleChatRequest = (request: string) => {
    onChatRequest({
      type: 'chat-request',
      request,
      context: {
        matterId: matter.id,
        practiceArea: matter.practiceArea,
        selectedItems: [matter.id]
      }
    });
  };

  return (
    <div className="relative">
      {/* Matter Header */}
      <div
        className={cn(
          "flex items-center py-2 px-3 hover:bg-gray-50 cursor-pointer text-sm border-l-2",
          isExpanded ? "bg-blue-50 border-blue-500" : "border-transparent"
        )}
        onClick={handleToggle}
        onContextMenu={handleRightClick}
      >
        <div className="w-4 h-4 flex items-center justify-center mr-2">
          {isExpanded ? (
            <ChevronDown className="h-3 w-3" />
          ) : (
            <ChevronRight className="h-3 w-3" />
          )}
        </div>

        <PracticeIcon className="h-4 w-4 mr-2 text-blue-600" />

        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2">
            <span className="truncate font-medium text-gray-900">{matter.name}</span>
            {matter.aiGenerated && (
              <Sparkles className="h-3 w-3 text-purple-500" />
            )}
            {hasUpcomingDeadlines && (
              <AlertTriangle className="h-3 w-3 text-red-500" />
            )}
          </div>
          <div className="flex items-center space-x-2 mt-1">
            <span className={cn(
              "px-2 py-0.5 rounded-full text-xs font-medium",
              statusColors[matter.status]
            )}>
              {matter.status}
            </span>
            <span className={cn("text-xs", priorityColors[matter.priority])}>
              {matter.priority} priority
            </span>
            <span className="text-xs text-gray-500">
              {matter.progress.percentage}% complete
            </span>
          </div>
        </div>
      </div>

      {/* AI Actions Context Menu */}
      {showActions && (
        <div className="absolute top-full left-4 z-10 bg-white border border-gray-200 rounded-md shadow-lg py-1 min-w-48">
          <div className="px-3 py-2 text-xs font-medium text-gray-500 border-b">
            AI Suggested Actions
          </div>
          {matter.suggestedActions.map(action => (
            <button
              key={action.id}
              className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 flex items-center space-x-2"
              onClick={() => handleAIAction(action.id)}
            >
              <Bot className="h-4 w-4 text-purple-500" />
              <span>{action.label}</span>
            </button>
          ))}
          <div className="border-t mt-1 pt-1">
            <button
              className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 flex items-center space-x-2"
              onClick={() => handleChatRequest(`What should I do next for ${matter.name}?`)}
            >
              <Bot className="h-4 w-4 text-blue-500" />
              <span>Ask AI for guidance</span>
            </button>
          </div>
        </div>
      )}

      {/* Expanded Matter Content */}
      {isExpanded && (
        <div className="ml-6 border-l border-gray-200">
          {/* Folders */}
          {matter.structure.folders.map(folder => (
            <FolderTreeNode
              key={folder.id}
              folder={folder}
              matterId={matter.id}
              onDocumentSelect={onDocumentSelect}
            />
          ))}

          {/* Documents */}
          {matter.structure.documents.map(document => (
            <DocumentTreeNode
              key={document.id}
              document={document}
              matterId={matter.id}
              onSelect={onDocumentSelect}
            />
          ))}
        </div>
      )}
    </div>
  );
};

// Folder Tree Node Component
const FolderTreeNode: React.FC<{
  folder: AIFolder;
  matterId: string;
  onDocumentSelect: (document: AIDocument, matterId: string) => void;
}> = ({ folder, matterId, onDocumentSelect }) => {
  const [isExpanded, setIsExpanded] = useState(folder.expanded || false);

  return (
    <div>
      <div
        className="flex items-center py-1 px-3 hover:bg-gray-50 cursor-pointer text-sm"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="w-4 h-4 flex items-center justify-center mr-2">
          {isExpanded ? (
            <ChevronDown className="h-3 w-3" />
          ) : (
            <ChevronRight className="h-3 w-3" />
          )}
        </div>
        <Folder className="h-4 w-4 mr-2 text-blue-500" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2">
            <span className="truncate text-gray-700">{folder.name}</span>
            {folder.aiGenerated && (
              <Sparkles className="h-3 w-3 text-purple-500" />
            )}
          </div>
          <div className="text-xs text-gray-500 truncate">{folder.purpose}</div>
        </div>
      </div>

      {isExpanded && folder.children && (
        <div className="ml-6">
          {folder.children.map(child => (
            <FolderTreeNode
              key={child.id}
              folder={child}
              matterId={matterId}
              onDocumentSelect={onDocumentSelect}
            />
          ))}
        </div>
      )}
    </div>
  );
};

// Document Tree Node Component
const DocumentTreeNode: React.FC<{
  document: AIDocument;
  matterId: string;
  onSelect: (document: AIDocument, matterId: string) => void;
}> = ({ document, matterId, onSelect }) => {
  const statusIcon = {
    draft: Circle,
    review: Clock,
    final: CheckCircle,
    archived: Circle
  }[document.status];

  const StatusIcon = statusIcon;

  return (
    <div
      className="flex items-center py-1 px-3 hover:bg-gray-50 cursor-pointer text-sm"
      onClick={() => onSelect(document, matterId)}
    >
      <div className="w-4 h-4 mr-2" />
      <File className="h-4 w-4 mr-2 text-gray-500" />
      <div className="flex-1 min-w-0">
        <div className="flex items-center space-x-2">
          <span className="truncate text-gray-700">{document.name}</span>
          {document.aiGenerated && (
            <Sparkles className="h-3 w-3 text-purple-500" />
          )}
          <StatusIcon className={cn(
            "h-3 w-3",
            document.status === 'final' ? 'text-green-500' :
              document.status === 'review' ? 'text-yellow-500' : 'text-gray-400'
          )} />
        </div>
        <div className="text-xs text-gray-500">
          {document.status} • {new Date(document.lastModified).toLocaleDateString()}
        </div>
      </div>
    </div>
  );
};

// Filter Component
const FilterPanel: React.FC<{
  filter: ExplorerFilter;
  onFilterChange: (filter: ExplorerFilter) => void;
  onClose: () => void;
}> = ({ filter, onFilterChange, onClose }) => {
  return (
    <div className="absolute top-full left-0 right-0 z-10 bg-white border border-gray-200 rounded-md shadow-lg p-4 m-2">
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-medium text-gray-900">Filter Matters</h4>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
          ×
        </button>
      </div>

      <div className="space-y-3">
        {/* Practice Area Filter */}
        <div>
          <label className="text-xs font-medium text-gray-700 block mb-1">Practice Area</label>
          <select
            className="w-full text-xs border border-gray-300 rounded px-2 py-1"
            value={filter.practiceArea || ''}
            onChange={(e) => onFilterChange({
              ...filter,
              practiceArea: e.target.value as PracticeArea || undefined
            })}
          >
            <option value="">All Areas</option>
            {mockFilterOptions.practiceAreas.map(area => (
              <option key={area} value={area}>{area}</option>
            ))}
          </select>
        </div>

        {/* Status Filter */}
        <div>
          <label className="text-xs font-medium text-gray-700 block mb-1">Status</label>
          <select
            className="w-full text-xs border border-gray-300 rounded px-2 py-1"
            value={filter.status || ''}
            onChange={(e) => onFilterChange({
              ...filter,
              status: e.target.value as MatterStatus || undefined
            })}
          >
            <option value="">All Statuses</option>
            {mockFilterOptions.statuses.map(status => (
              <option key={status} value={status}>{status}</option>
            ))}
          </select>
        </div>

        {/* Priority Filter */}
        <div>
          <label className="text-xs font-medium text-gray-700 block mb-1">Priority</label>
          <select
            className="w-full text-xs border border-gray-300 rounded px-2 py-1"
            value={filter.priority || ''}
            onChange={(e) => onFilterChange({
              ...filter,
              priority: e.target.value as MatterPriority || undefined
            })}
          >
            <option value="">All Priorities</option>
            {mockFilterOptions.priorities.map(priority => (
              <option key={priority} value={priority}>{priority}</option>
            ))}
          </select>
        </div>

        {/* AI Generated Filter */}
        <div className="flex items-center space-x-2">
          <input
            type="checkbox"
            id="ai-generated"
            checked={filter.aiGenerated || false}
            onChange={(e) => onFilterChange({
              ...filter,
              aiGenerated: e.target.checked || undefined
            })}
            className="rounded border-gray-300"
          />
          <label htmlFor="ai-generated" className="text-xs text-gray-700">
            AI Generated Only
          </label>
        </div>
      </div>
    </div>
  );
};

// Main Enhanced Explorer Panel Component (Project Mode)
const EnhancedExplorerPanel: React.FC<EnhancedExplorerPanelProps> = ({
  selectedProject,
  onDocumentSelect,
  onAIAction,
  onChatRequest,
  onBackToProjects
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());

  // If no project is selected, show empty state
  if (!selectedProject) {
    return (
      <div className="explorer-panel-container flex bg-white h-full w-full">
        <div className="flex flex-col h-full flex-1 items-center justify-center text-gray-500">
          <Folder className="h-12 w-12 mb-4" />
          <p>Select a project to view its files</p>
        </div>
      </div>
    );
  }

  const config = practiceAreaIcons[selectedProject.practiceArea];
  const PracticeIcon = config;

  const handleDocumentSelect = (document: AIDocument, matterId: string) => {
    onDocumentSelect?.(document, matterId);
  };

  const handleAIAction = (actionEvent: AIActionEvent) => {
    onAIAction?.(actionEvent);
  };

  const handleChatRequest = (requestEvent: ChatRequestEvent) => {
    onChatRequest?.(requestEvent);
  };

  const toggleFolder = (folderId: string) => {
    const newExpanded = new Set(expandedFolders);
    if (newExpanded.has(folderId)) {
      newExpanded.delete(folderId);
    } else {
      newExpanded.add(folderId);
    }
    setExpandedFolders(newExpanded);
  };

  // Filter documents and folders based on search
  const filteredFolders = selectedProject.structure.folders.filter(folder =>
    !searchQuery || folder.name.toLowerCase().includes(searchQuery.toLowerCase())
  );
  
  const filteredDocuments = selectedProject.structure.documents.filter(document =>
    !searchQuery || document.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="explorer-panel-container flex bg-background h-full w-full border-r">
      <div className="flex flex-col h-full flex-1">
        {/* Header */}
        <div className="flex items-center justify-between p-3 border-b">
          <div className="flex items-center space-x-2">
            {onBackToProjects && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onBackToProjects}
                className="h-8 w-8 p-0"
              >
                <ArrowLeft className="h-4 w-4" />
              </Button>
            )}
            <PracticeIcon className="h-4 w-4" />
            <div>
              <h3 className="text-sm font-medium truncate">
                {selectedProject.name}
              </h3>
              <p className="text-xs text-muted-foreground">{selectedProject.client}</p>
            </div>
          </div>
          <div className="flex items-center space-x-1">
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
              <Plus className="h-4 w-4" />
            </Button>
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
              <MoreHorizontal className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Search Bar */}
        <div className="p-3 border-b">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search files and folders..."
              className="pl-10"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>

        {/* Project Structure */}
        <ScrollArea className="flex-1">
          <div className="py-2">
            {/* Folders */}
            {filteredFolders.map(folder => (
              <ProjectFolderNode
                key={folder.id}
                folder={folder}
                isExpanded={expandedFolders.has(folder.id)}
                onToggle={() => toggleFolder(folder.id)}
                onDocumentSelect={handleDocumentSelect}
                matterId={selectedProject.id}
                depth={0}
              />
            ))}
            
            {/* Root Documents */}
            {filteredDocuments.map(document => (
              <ProjectDocumentNode
                key={document.id}
                document={document}
                matterId={selectedProject.id}
                onSelect={handleDocumentSelect}
                depth={0}
              />
            ))}
            
            {filteredFolders.length === 0 && filteredDocuments.length === 0 && (
              <div className="p-4 text-center text-muted-foreground text-sm">
                {searchQuery ? 'No files found matching your search.' : 'This project is empty.'}
              </div>
            )}
          </div>
        </ScrollArea>

        {/* Status Bar */}
        <div className="p-3 border-t">
          {selectedProject.progress && (
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span>Progress</span>
                <span>{selectedProject.progress.percentage}%</span>
              </div>
              <Progress value={selectedProject.progress.percentage} className="h-1" />
              <div className="text-xs text-muted-foreground">
                {selectedProject.progress.completedTasks}/{selectedProject.progress.totalTasks} tasks completed
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
};

// Project Folder Node Component (for project mode)
const ProjectFolderNode: React.FC<{
  folder: AIFolder;
  isExpanded: boolean;
  onToggle: () => void;
  onDocumentSelect: (document: AIDocument, matterId: string) => void;
  matterId: string;
  depth: number;
}> = ({ folder, isExpanded, onToggle, onDocumentSelect, matterId, depth }) => {
  return (
    <div>
      <div
        className="flex items-center py-1 px-3 hover:bg-muted cursor-pointer text-sm"
        style={{ paddingLeft: `${depth * 12 + 12}px` }}
        onClick={onToggle}
      >
        <div className="w-4 h-4 flex items-center justify-center mr-2">
          {isExpanded ? (
            <ChevronDown className="h-3 w-3" />
          ) : (
            <ChevronRight className="h-3 w-3" />
          )}
        </div>
        <Folder className="h-4 w-4 mr-2 text-muted-foreground" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center space-x-2">
            <span className="truncate">{folder.name}</span>
            {folder.aiGenerated && (
              <Badge variant="secondary" className="h-4 px-1 text-xs">
                <Sparkles className="h-2 w-2" />
              </Badge>
            )}
          </div>
          {folder.purpose && (
            <div className="text-xs text-muted-foreground truncate">{folder.purpose}</div>
          )}
        </div>
      </div>
      
      {isExpanded && (
        <div>
          {folder.children.map(child => (
            <ProjectFolderNode
              key={child.id}
              folder={child}
              isExpanded={false} // Child folders start collapsed
              onToggle={() => {}} // TODO: Implement nested folder expansion
              onDocumentSelect={onDocumentSelect}
              matterId={matterId}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
};

// Project Document Node Component (for project mode)
const ProjectDocumentNode: React.FC<{
  document: AIDocument;
  matterId: string;
  onSelect: (document: AIDocument, matterId: string) => void;
  depth: number;
}> = ({ document, matterId, onSelect, depth }) => {
  const statusIcon = {
    draft: Circle,
    review: Clock,
    final: CheckCircle,
    archived: Circle
  }[document.status];

  const StatusIcon = statusIcon;

  return (
    <div
      className="flex items-center py-1 px-3 hover:bg-muted cursor-pointer text-sm"
      style={{ paddingLeft: `${depth * 12 + 12}px` }}
      onClick={() => onSelect(document, matterId)}
    >
      <div className="w-4 h-4 mr-2" />
      <File className="h-4 w-4 mr-2 text-muted-foreground" />
      <div className="flex-1 min-w-0">
        <div className="flex items-center space-x-2">
          <span className="truncate">{document.name}</span>
          {document.aiGenerated && (
            <Badge variant="secondary" className="h-4 px-1 text-xs">
              <Sparkles className="h-2 w-2" />
            </Badge>
          )}
          <StatusIcon className={cn(
            "h-3 w-3",
            document.status === 'final' ? 'text-green-600' :
              document.status === 'review' ? 'text-yellow-600' : 'text-muted-foreground'
          )} />
        </div>
        <div className="text-xs text-muted-foreground">
          {document.status} • {new Date(document.lastModified).toLocaleDateString()}
        </div>
      </div>
    </div>
  );
};

// Export both the enhanced version and keep the original for backward compatibility
export { EnhancedExplorerPanel };
export default EnhancedExplorerPanel;