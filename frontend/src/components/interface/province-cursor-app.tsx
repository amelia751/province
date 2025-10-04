"use client";

import React, { useState } from 'react';
import { StartScreen, RecentProject, ProjectTemplate } from '@/components/start-screen';
import { EnhancedExplorerPanel } from '@/components/explorer-panel';
import Chat from '@/components/chat/chat';
import MainEditor from '@/components/main-editor/main-editor';
import { AIMatter, AIDocument, AIActionEvent, ChatRequestEvent } from '@/components/explorer-panel/types';

type AppView = 'start' | 'project';

interface ProvinceCursorAppProps {
  organizationName?: string;
}

const ProvinceCursorApp: React.FC<ProvinceCursorAppProps> = ({ organizationName }) => {
  const [currentView, setCurrentView] = useState<AppView>('start');
  const [selectedProject, setSelectedProject] = useState<AIMatter | null>(null);
  const [selectedDocument, setSelectedDocument] = useState<AIDocument | null>(null);

  // Convert RecentProject to AIMatter for compatibility
  const convertProjectToMatter = (project: RecentProject): AIMatter => {
    return {
      id: project.id,
      name: project.name,
      type: project.practiceArea === 'legal' ? 'personal-injury' : 'tax-return',
      practiceArea: project.practiceArea,
      client: project.client,
      description: project.description,
      status: project.status,
      priority: 'medium',
      aiGenerated: project.aiGenerated,
      generationPrompt: `Generated project: ${project.name}`,
      structure: {
        folders: [
          {
            id: 'folder-1',
            name: 'Documents',
            purpose: 'Main project documents',
            requiredDocuments: [],
            suggestedTemplates: [],
            children: [],
            expanded: true,
            aiGenerated: true,
            createdAt: new Date()
          }
        ],
        documents: [
          {
            id: 'doc-1',
            name: 'Project Overview.md',
            type: 'legal-brief',
            path: '/project-overview.md',
            status: 'draft',
            lastModified: project.lastOpened,
            aiGenerated: true,
            collaborators: project.teamMembers,
            size: 1024
          }
        ],
        workflows: [],
        templates: []
      },
      progress: project.progress ? {
        completedTasks: project.progress.completed,
        totalTasks: project.progress.total,
        percentage: project.progress.percentage
      } : { completedTasks: 0, totalTasks: 1, percentage: 0 },
      deadlines: [],
      suggestedActions: [
        {
          id: 'action-1',
          type: 'generate-document',
          label: 'Generate Document',
          description: 'Create a new document for this project',
          practiceArea: project.practiceArea,
          enabled: true
        }
      ],
      chatContext: {
        sessionId: `session-${project.id}`,
        lastInteraction: project.lastOpened,
        conversationSummary: `Working on ${project.name}`,
        relatedDocuments: []
      },
      createdAt: new Date(project.lastOpened.getTime() - 7 * 24 * 60 * 60 * 1000), // 7 days ago
      lastModified: project.lastOpened,
      assignedTo: project.teamMembers,
      jurisdiction: 'General',
      tags: project.tags
    };
  };

  const handleProjectSelect = (project: RecentProject) => {
    const matter = convertProjectToMatter(project);
    setSelectedProject(matter);
    setCurrentView('project');
  };

  const handleNewProject = (template?: ProjectTemplate, prompt?: string) => {
    // Here you would typically create a new project
    // For now, we'll just show a placeholder
    console.log('Creating new project:', { template, prompt });
    
    // Create a mock new project
    const newProject: RecentProject = {
      id: `new-${Date.now()}`,
      name: template ? `New ${template.name}` : 'New Project',
      practiceArea: template?.practiceArea || 'legal',
      client: 'New Client',
      lastOpened: new Date(),
      path: '/new-project',
      description: template?.description || 'A new project created with AI assistance',
      status: 'active',
      aiGenerated: true,
      tags: ['new', 'ai-generated'],
      teamMembers: ['current.user@firm.com']
    };
    
    handleProjectSelect(newProject);
  };

  const handleOpenProject = () => {
    // Here you would typically open a file dialog
    console.log('Opening project from computer...');
    // For demo purposes, we'll just log this
    alert('File dialog would open here to select a project folder');
  };

  const handleBackToProjects = () => {
    setCurrentView('start');
    setSelectedProject(null);
    setSelectedDocument(null);
  };

  const handleDocumentSelect = (document: AIDocument, matterId: string) => {
    setSelectedDocument(document);
    console.log('Opening document:', document.name, 'from matter:', matterId);
  };

  const handleAIAction = (action: AIActionEvent) => {
    console.log('AI Action:', action);
    // Here you would handle the AI action
  };

  const handleChatRequest = (request: ChatRequestEvent) => {
    console.log('Chat Request:', request);
    // Here you would send the request to the chat system
  };

  if (currentView === 'start') {
    return (
      <StartScreen
        onProjectSelect={handleProjectSelect}
        onNewProject={handleNewProject}
        onOpenProject={handleOpenProject}
      />
    );
  }

  // Project view with three-panel layout (Cursor style)
  return (
    <div className="h-full flex bg-background">
      {/* Explorer Panel */}
      <div className="w-80">
        <EnhancedExplorerPanel
          selectedProject={selectedProject}
          onDocumentSelect={handleDocumentSelect}
          onAIAction={handleAIAction}
          onChatRequest={handleChatRequest}
          onBackToProjects={handleBackToProjects}
        />
      </div>

      {/* Main Editor */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="h-12 border-b flex items-center px-4">
          <h1 className="text-sm font-medium">
            {selectedDocument ? selectedDocument.name : 'Province Cursor'}
          </h1>
          {organizationName && (
            <span className="ml-4 text-xs text-muted-foreground">• {organizationName}</span>
          )}
        </div>
        
        {/* Editor Content */}
        <div className="flex-1">
          {selectedDocument ? (
            <MainEditor />
          ) : (
            <div className="h-full flex items-center justify-center">
              <div className="text-center">
                <div className="text-6xl mb-4">📄</div>
                <h3 className="text-lg font-medium mb-2">No document selected</h3>
                <p className="text-muted-foreground">Select a file from the explorer to start editing</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Chat Panel */}
      <div className="w-80 border-l">
        <Chat />
      </div>
    </div>
  );
};

export default ProvinceCursorApp;