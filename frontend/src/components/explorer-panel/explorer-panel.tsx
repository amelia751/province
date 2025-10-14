"use client";

import React, { useState } from "react";
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
  CheckCircle,
  Circle,
  Briefcase,
  Calculator,
  Shield,
  FileText,
  ArrowLeft
} from "lucide-react";

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import DocumentIngest from './document-ingest';

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
  ChatRequestEvent
} from './types';
import { mockFilterOptions } from './mock-data';

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

const priorityColors = {
  high: 'text-red-600',
  medium: 'text-yellow-600',
  low: 'text-green-600'
};

// (Optional) Filter panel kept for future use
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
              practiceArea: (e.target.value as PracticeArea) || undefined
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
              status: (e.target.value as MatterStatus) || undefined
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
              priority: (e.target.value as MatterPriority) || undefined
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

// --- Project Panel ---
const EnhancedExplorerPanel: React.FC<EnhancedExplorerPanelProps> = ({
  selectedProject,
  onDocumentSelect,
  onAIAction,
  onChatRequest,
  onBackToProjects
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set(['folder-returns', 'folder-documents', 'folder-forms-to-fill', 'folder-w2', 'folder-1099-forms']));
  const [ingestDialogOpen, setIngestDialogOpen] = useState(false);
  const [selectedIngestFolder, setSelectedIngestFolder] = useState<{ id: string; name: string } | null>(null);

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

  const PracticeIcon = practiceAreaIcons[selectedProject.practiceArea];

  const handleDocumentSelect = (document: AIDocument, matterId: string) => {
    onDocumentSelect?.(document, matterId);
  };

  const toggleFolder = (folderId: string) => {
    setExpandedFolders(prev => {
      const next = new Set(prev);
      if (next.has(folderId)) next.delete(folderId);
      else next.add(folderId);
      return next;
    });
  };

  // Filter documents and folders based on search
  const filteredFolders = selectedProject.structure.folders.filter(folder =>
    !searchQuery || folder.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredDocuments = selectedProject.structure.documents.filter(document => {
    // Apply search filter
    if (searchQuery && !document.name.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false;
    }
    
    // Only show documents that are at the root level (not in any folder)
    const pathParts = document.path.split('/').filter(part => part);
    return pathParts.length === 2; // Only /project/file.ext (no folders)
  });

  const handleOpenIngestDialog = (folderId: string, folderName: string) => {
    setSelectedIngestFolder({ id: folderId, name: folderName });
    setIngestDialogOpen(true);
  };

  const handleUploadComplete = (files: File[], folderId: string) => {
    console.log('Files uploaded to folder:', folderId, files);
    // TODO: Implement actual file upload logic
  };

  return (
    <div className="explorer-panel-container flex bg-background h-full w-full">
      {/* min-h-0 lets the inner scroll region actually shrink & scroll */}
      <div className="flex flex-col h-full flex-1 min-h-0">
        {/* Header */}
        <div className="flex items-center justify-between px-2 py-1.5 border-b">
          <div className="flex items-center space-x-1.5 min-w-0">
            {onBackToProjects && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onBackToProjects}
                className="h-6 w-6 p-0 flex-shrink-0"
              >
                <ArrowLeft className="h-3.5 w-3.5" />
              </Button>
            )}
            <PracticeIcon className="h-3.5 w-3.5 flex-shrink-0" />
            <div className="min-w-0">
              <h3 className="text-xs font-medium truncate">{selectedProject.name}</h3>
              <p className="text-[10px] text-muted-foreground truncate">{selectedProject.client}</p>
            </div>
          </div>
          <div className="flex items-center space-x-0.5">
            <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
              <Plus className="h-3.5 w-3.5" />
            </Button>
            <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
              <MoreHorizontal className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>

        {/* Search Bar */}
        <div className="px-2 py-1.5 border-b">
          <div className="relative">
            <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
            <Input
              placeholder="Search files and folders..."
              className="pl-7 h-7 text-xs"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>

        {/* Scrollable Project Structure */}
        <div className="relative flex-1 min-h-0">
          <div className="absolute inset-0 overflow-y-auto">
            <div className="py-2">
              {/* Folders */}
              {filteredFolders.map(folder => (
                <ProjectFolderNode
                  key={folder.id}
                  folder={folder}
                  isExpanded={expandedFolders.has(folder.id)}
                  onToggle={() => toggleFolder(folder.id)}
                  onDocumentSelect={handleDocumentSelect}
                  onOpenIngest={handleOpenIngestDialog}
                  matterId={selectedProject.id}
                  depth={0}
                  parentPath=""
                  allDocuments={selectedProject.structure.documents}
                  expandedFolders={expandedFolders}
                  onToggleFolder={toggleFolder}
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
          </div>
        </div>

        {/* Status Bar (fixed at bottom, outside scroll region) */}
        <div className="px-2 py-1.5 border-t">
          {selectedProject.progress && (
            <div className="space-y-1.5">
              <div className="flex items-center justify-between text-[10px]">
                <span>Progress</span>
                <span>{selectedProject.progress.percentage}%</span>
              </div>
              <Progress value={selectedProject.progress.percentage} className="h-1" />
              <div className="text-[10px] text-muted-foreground">
                {selectedProject.progress.completedTasks}/{selectedProject.progress.totalTasks} tasks completed
              </div>
            </div>
          )}
        </div>

        {/* Document Ingest Dialog */}
        {selectedIngestFolder && (
          <DocumentIngest
            folderId={selectedIngestFolder.id}
            folderName={selectedIngestFolder.name}
            open={ingestDialogOpen}
            onOpenChange={setIngestDialogOpen}
            onUpload={handleUploadComplete}
          />
        )}
      </div>
    </div>
  );
};

// --- Project Folder Node (uses padding for depth indentation) ---
const ProjectFolderNode: React.FC<{
  folder: AIFolder;
  isExpanded: boolean;
  onToggle: () => void;
  onDocumentSelect: (document: AIDocument, matterId: string) => void;
  onOpenIngest: (folderId: string, folderName: string) => void;
  matterId: string;
  depth: number;
  parentPath?: string;
  allDocuments: AIDocument[];
  expandedFolders: Set<string>;
  onToggleFolder: (folderId: string) => void;
}> = ({ folder, isExpanded, onToggle, onDocumentSelect, onOpenIngest, matterId, depth, parentPath = '', allDocuments, expandedFolders, onToggleFolder }) => {
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div>
      <div
        className="flex items-center py-1 px-3 hover:bg-muted cursor-pointer text-sm group relative"
        style={{ paddingLeft: `${depth * 12 + 12}px` }}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        <div className="w-4 h-4 flex items-center justify-center mr-2" onClick={onToggle}>
          {isExpanded ? (
            <ChevronDown className="h-3 w-3" />
          ) : (
            <ChevronRight className="h-3 w-3" />
          )}
        </div>
        <Folder className="h-4 w-4 mr-2 text-muted-foreground" onClick={onToggle} />
        <div className="flex-1 min-w-0" onClick={onToggle}>
          <div className="flex items-center space-x-2">
            <span className="truncate">{folder.name}</span>
          </div>
          {folder.purpose && (
            <div className="text-xs text-muted-foreground truncate">{folder.purpose}</div>
          )}
        </div>
        {/* Add document button - shown on hover if folder needs ingest */}
        {folder.needsDocumentIngest && isHovered && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onOpenIngest(folder.id, folder.name);
            }}
            className="flex-shrink-0 p-1 rounded hover:bg-gray-200 transition-colors"
            title="Add documents"
          >
            <Plus className="h-3.5 w-3.5 text-gray-600" />
          </button>
        )}
      </div>

      {isExpanded && (
        <div>
          {/* Nested folders */}
          {folder.children.map(child => (
            <ProjectFolderNode
              key={child.id}
              folder={child}
              isExpanded={expandedFolders.has(child.id)}
              onToggle={() => onToggleFolder(child.id)}
              onDocumentSelect={onDocumentSelect}
              onOpenIngest={onOpenIngest}
              matterId={matterId}
              depth={depth + 1}
              parentPath={parentPath ? `${parentPath}/${folder.name}` : folder.name}
              allDocuments={allDocuments}
              expandedFolders={expandedFolders}
              onToggleFolder={onToggleFolder}
            />
          ))}

          {/* Documents in this folder */}
          {(() => {
            const fullFolderPath = parentPath ? `${parentPath}/${folder.name}` : folder.name;
            
            const documentsInFolder = allDocuments.filter(doc => {
              const pathParts = doc.path.split('/').filter(part => part); // Remove empty parts
              if (pathParts.length < 2) return false;
              
              // Remove project name from path
              const docPathWithoutProject = pathParts.slice(1).join('/');
              
              // Check if document is directly in this folder (not in subfolders)
              const folderPathParts = fullFolderPath.split('/').filter(part => part);
              const docPathParts = docPathWithoutProject.split('/');
              
              
              // Document should be in this exact folder
              if (docPathParts.length !== folderPathParts.length + 1) return false;
              
              // Check if all folder path parts match
              for (let i = 0; i < folderPathParts.length; i++) {
                if (docPathParts[i] !== folderPathParts[i]) return false;
              }
              
              return true;
            });
            
            
            return documentsInFolder.map(document => (
              <ProjectDocumentNode
                key={document.id}
                document={document}
                matterId={matterId}
                onSelect={onDocumentSelect}
                depth={depth + 1}
              />
            ));
          })()}
        </div>
      )}
    </div>
  );
};

// --- Project Document Node ---
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
          <StatusIcon
            className={cn(
              "h-3 w-3",
              document.status === 'final'
                ? 'text-green-600'
                : document.status === 'review'
                ? 'text-yellow-600'
                : 'text-muted-foreground'
            )}
          />
        </div>
        <div className="text-xs text-muted-foreground">
          {document.status} • {new Date(document.lastModified).toLocaleDateString()}
        </div>
      </div>
    </div>
  );
};

export { EnhancedExplorerPanel };
export default EnhancedExplorerPanel;
