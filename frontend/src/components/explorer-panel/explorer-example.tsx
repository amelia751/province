// Example usage of the AI-Enhanced Explorer Panel

"use client";

import React from 'react';
import { EnhancedExplorerPanel, useExplorerState } from './index';
import type { 
  AIMatter, 
  AIDocument, 
  AIActionEvent, 
  ChatRequestEvent,
  PracticeArea 
} from './types';

interface ExplorerExampleProps {
  currentPracticeArea?: PracticeArea;
}

const ExplorerExample: React.FC<ExplorerExampleProps> = ({ 
  currentPracticeArea = 'legal' 
}) => {
  // Use the explorer state hook
  const explorerState = useExplorerState({
    initialPracticeArea: currentPracticeArea,
    onMatterSelect: (matter: AIMatter) => {
      console.log('Matter selected:', matter.name);
      // Here you would typically update your main application state
      // or navigate to the matter detail view
    },
    onDocumentSelect: (document: AIDocument, matterId: string) => {
      console.log('Document selected:', document.name, 'from matter:', matterId);
      // Here you would typically open the document in the main editor
    },
    onAIAction: (action: AIActionEvent) => {
      console.log('AI Action triggered:', action.action.label);
      // Here you would typically execute the AI action
      // This might involve calling your backend API or updating the chat
      handleAIAction(action);
    },
    onChatRequest: (request: ChatRequestEvent) => {
      console.log('Chat request:', request.request);
      // Here you would typically send the request to your chat component
      handleChatRequest(request);
    }
  });

  const handleAIAction = async (action: AIActionEvent) => {
    // Example of handling different AI actions
    switch (action.action.type) {
      case 'generate-document':
        console.log(`Generating document: ${action.action.label}`);
        // Call your document generation API
        break;
      case 'research':
        console.log(`Starting research: ${action.action.label}`);
        // Call your research API
        break;
      case 'compliance-check':
        console.log(`Running compliance check: ${action.action.label}`);
        // Call your compliance API
        break;
      case 'calculate-deadline':
        console.log(`Calculating deadline: ${action.action.label}`);
        // Call your deadline calculation API
        break;
      case 'create-deadline':
        console.log(`Creating deadline: ${action.action.label}`);
        // Call your deadline creation API
        break;
      default:
        console.log(`Unknown action type: ${action.action.type}`);
    }
  };

  const handleChatRequest = (request: ChatRequestEvent) => {
    // Example of handling chat requests
    console.log('Processing chat request:', {
      request: request.request,
      context: request.context
    });
    
    // Here you would typically:
    // 1. Send the request to your chat component
    // 2. Update the chat state
    // 3. Trigger AI processing
    
    // Example: Focus the chat input and pre-fill the request
    // chatRef.current?.sendMessage(request.request, request.context);
  };

  return (
    <div className="h-full w-80 border-r border-gray-200">
      <EnhancedExplorerPanel
        currentPracticeArea={currentPracticeArea}
        onMatterSelect={explorerState.selectMatter}
        onDocumentSelect={explorerState.selectDocument}
        onAIAction={explorerState.executeAIAction}
        onChatRequest={explorerState.sendChatRequest}
      />
      
      {/* Debug Info Panel (remove in production) */}
      {process.env.NODE_ENV === 'development' && (
        <div className="p-4 bg-gray-50 border-t text-xs">
          <h4 className="font-medium mb-2">Debug Info:</h4>
          <div className="space-y-1 text-gray-600">
            <div>Total Matters: {explorerState.totalMatters}</div>
            <div>Filtered: {explorerState.filteredMatters.length}</div>
            <div>AI Generated: {explorerState.aiGeneratedMatters}</div>
            <div>Upcoming Deadlines: {explorerState.upcomingDeadlines}</div>
            <div>Selected: {explorerState.selectedMatter?.name || 'None'}</div>
            <div>Loading: {explorerState.isLoading ? 'Yes' : 'No'}</div>
            {explorerState.error && (
              <div className="text-red-600">Error: {explorerState.error}</div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ExplorerExample;

// Example of how to integrate with your main application layout
export const ExplorerIntegrationExample: React.FC = () => {
  const [currentPracticeArea, setCurrentPracticeArea] = React.useState<PracticeArea>('legal');

  return (
    <div className="flex h-screen">
      {/* Explorer Panel */}
      <ExplorerExample currentPracticeArea={currentPracticeArea} />
      
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        {/* Practice Area Selector */}
        <div className="p-4 border-b border-gray-200">
          <select 
            value={currentPracticeArea}
            onChange={(e) => setCurrentPracticeArea(e.target.value as PracticeArea)}
            className="px-3 py-2 border border-gray-300 rounded-md"
          >
            <option value="legal">Legal</option>
            <option value="accounting">Accounting</option>
            <option value="tax">Tax</option>
            <option value="compliance">Compliance</option>
          </select>
        </div>
        
        {/* Main Editor Area */}
        <div className="flex-1 p-4">
          <div className="h-full bg-gray-50 rounded-lg flex items-center justify-center text-gray-500">
            Main Editor Area - Documents will open here
          </div>
        </div>
      </div>
      
      {/* Chat Panel */}
      <div className="w-80 border-l border-gray-200 bg-gray-50 flex items-center justify-center text-gray-500">
        Chat Panel - AI conversations happen here
      </div>
    </div>
  );
};