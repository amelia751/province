// Hook for managing AI-Enhanced Explorer Panel state

import { useState, useEffect, useCallback } from 'react';
import { 
  AIMatter, 
  AIDocument, 
  ExplorerFilter, 
  ExplorerSearchResult,
  PracticeArea,
  AIActionEvent,
  MatterSelectionEvent,
  DocumentSelectionEvent,
  ChatRequestEvent
} from './types';
import { mockAIMatters } from './mock-data';

export interface UseExplorerStateOptions {
  initialPracticeArea?: PracticeArea;
  onMatterSelect?: (matter: AIMatter) => void;
  onDocumentSelect?: (document: AIDocument, matterId: string) => void;
  onAIAction?: (action: AIActionEvent) => void;
  onChatRequest?: (request: ChatRequestEvent) => void;
}

export interface UseExplorerStateReturn {
  // Data
  matters: AIMatter[];
  filteredMatters: AIMatter[];
  selectedMatter: AIMatter | null;
  selectedDocument: AIDocument | null;
  
  // Search & Filter
  searchQuery: string;
  filter: ExplorerFilter;
  searchResults: ExplorerSearchResult | null;
  
  // UI State
  isLoading: boolean;
  error: string | null;
  showFilter: boolean;
  
  // Actions
  setSearchQuery: (query: string) => void;
  setFilter: (filter: ExplorerFilter) => void;
  setShowFilter: (show: boolean) => void;
  selectMatter: (matter: AIMatter) => void;
  selectDocument: (document: AIDocument, matterId: string) => void;
  executeAIAction: (action: AIActionEvent) => void;
  sendChatRequest: (request: ChatRequestEvent) => void;
  refreshMatters: () => Promise<void>;
  createNewMatter: (prompt: string, practiceArea: PracticeArea) => Promise<AIMatter>;
  
  // Computed values
  hasActiveFilters: boolean;
  totalMatters: number;
  aiGeneratedMatters: number;
  upcomingDeadlines: number;
}

export const useExplorerState = (options: UseExplorerStateOptions = {}): UseExplorerStateReturn => {
  const {
    initialPracticeArea,
    onMatterSelect,
    onDocumentSelect,
    onAIAction,
    onChatRequest
  } = options;

  // Core state
  const [matters, setMatters] = useState<AIMatter[]>(mockAIMatters);
  const [filteredMatters, setFilteredMatters] = useState<AIMatter[]>(mockAIMatters);
  const [selectedMatter, setSelectedMatter] = useState<AIMatter | null>(null);
  const [selectedDocument, setSelectedDocument] = useState<AIDocument | null>(null);
  
  // Search & Filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [filter, setFilter] = useState<ExplorerFilter>({
    practiceArea: initialPracticeArea
  });
  const [searchResults, setSearchResults] = useState<ExplorerSearchResult | null>(null);
  
  // UI state
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showFilter, setShowFilter] = useState(false);

  // Filter and search logic
  useEffect(() => {
    const startTime = Date.now();
    let filtered = matters;

    // Apply search
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(matter => 
        matter.name.toLowerCase().includes(query) ||
        matter.client.toLowerCase().includes(query) ||
        matter.description.toLowerCase().includes(query) ||
        matter.tags.some(tag => tag.toLowerCase().includes(query)) ||
        matter.structure.documents.some(doc => 
          doc.name.toLowerCase().includes(query)
        )
      );
    }

    // Apply filters
    if (filter.practiceArea) {
      filtered = filtered.filter(matter => matter.practiceArea === filter.practiceArea);
    }
    if (filter.status) {
      filtered = filtered.filter(matter => matter.status === filter.status);
    }
    if (filter.priority) {
      filtered = filtered.filter(matter => matter.priority === filter.priority);
    }
    if (filter.client) {
      filtered = filtered.filter(matter => 
        matter.client.toLowerCase().includes(filter.client!.toLowerCase())
      );
    }
    if (filter.assignedTo) {
      filtered = filtered.filter(matter => 
        matter.assignedTo.includes(filter.assignedTo!)
      );
    }
    if (filter.aiGenerated !== undefined) {
      filtered = filtered.filter(matter => matter.aiGenerated === filter.aiGenerated);
    }
    if (filter.hasUpcomingDeadlines) {
      const weekFromNow = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000);
      filtered = filtered.filter(matter => 
        matter.deadlines.some(deadline => 
          !deadline.completed && new Date(deadline.dueDate) <= weekFromNow
        )
      );
    }
    if (filter.dateRange) {
      filtered = filtered.filter(matter => {
        const matterDate = new Date(matter.createdAt);
        return matterDate >= filter.dateRange!.start && matterDate <= filter.dateRange!.end;
      });
    }

    setFilteredMatters(filtered);

    // Update search results if there's a query
    if (searchQuery.trim()) {
      const documents = filtered.flatMap(matter => 
        matter.structure.documents.map(doc => ({ ...doc, matterId: matter.id }))
      );
      
      setSearchResults({
        matters: filtered,
        documents: documents as AIDocument[],
        totalResults: filtered.length + documents.length,
        searchTime: Date.now() - startTime
      });
    } else {
      setSearchResults(null);
    }
  }, [matters, searchQuery, filter]);

  // Actions
  const selectMatter = useCallback((matter: AIMatter) => {
    setSelectedMatter(matter);
    setSelectedDocument(null);
    onMatterSelect?.(matter);
  }, [onMatterSelect]);

  const selectDocument = useCallback((document: AIDocument, matterId: string) => {
    setSelectedDocument(document);
    onDocumentSelect?.(document, matterId);
  }, [onDocumentSelect]);

  const executeAIAction = useCallback((action: AIActionEvent) => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Here you would typically make an API call to execute the AI action
      console.log('Executing AI action:', action);
      onAIAction?.(action);
      
      // Simulate API delay
      setTimeout(() => {
        setIsLoading(false);
      }, 1000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to execute AI action');
      setIsLoading(false);
    }
  }, [onAIAction]);

  const sendChatRequest = useCallback((request: ChatRequestEvent) => {
    console.log('Sending chat request:', request);
    onChatRequest?.(request);
  }, [onChatRequest]);

  const refreshMatters = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Here you would typically fetch fresh data from the API
      // For now, we'll just simulate a refresh
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // In a real app, you'd do:
      // const freshMatters = await api.getMatters();
      // setMatters(freshMatters);
      
      setIsLoading(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to refresh matters');
      setIsLoading(false);
    }
  }, []);

  const createNewMatter = useCallback(async (prompt: string, practiceArea: PracticeArea): Promise<AIMatter> => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Here you would typically call the AI service to create a new matter
      // For now, we'll create a mock matter
      const newMatter: AIMatter = {
        id: `matter-${Date.now()}`,
        name: `New ${practiceArea} Matter`,
        type: practiceArea === 'legal' ? 'contract-dispute' : 'tax-return',
        practiceArea,
        client: 'New Client',
        description: `Matter created from prompt: ${prompt}`,
        status: 'active',
        priority: 'medium',
        aiGenerated: true,
        generationPrompt: prompt,
        structure: {
          folders: [],
          documents: [],
          workflows: [],
          templates: []
        },
        progress: {
          completedTasks: 0,
          totalTasks: 1,
          percentage: 0
        },
        deadlines: [],
        suggestedActions: [],
        chatContext: {
          sessionId: `session-${Date.now()}`,
          lastInteraction: new Date(),
          conversationSummary: `Created new matter: ${prompt}`,
          relatedDocuments: []
        },
        createdAt: new Date(),
        lastModified: new Date(),
        assignedTo: ['current.user@firm.com'],
        tags: ['ai-generated', 'new']
      };

      // Add to matters list
      setMatters(prev => [newMatter, ...prev]);
      setSelectedMatter(newMatter);
      
      setIsLoading(false);
      return newMatter;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create new matter');
      setIsLoading(false);
      throw err;
    }
  }, []);

  // Computed values
  const hasActiveFilters = Object.keys(filter).length > 0 && 
    Object.values(filter).some(value => value !== undefined && value !== '');
  
  const totalMatters = matters.length;
  const aiGeneratedMatters = matters.filter(m => m.aiGenerated).length;
  const upcomingDeadlines = matters.reduce((count, matter) => {
    const weekFromNow = new Date(Date.now() + 7 * 24 * 60 * 60 * 1000);
    return count + matter.deadlines.filter(deadline => 
      !deadline.completed && new Date(deadline.dueDate) <= weekFromNow
    ).length;
  }, 0);

  return {
    // Data
    matters,
    filteredMatters,
    selectedMatter,
    selectedDocument,
    
    // Search & Filter
    searchQuery,
    filter,
    searchResults,
    
    // UI State
    isLoading,
    error,
    showFilter,
    
    // Actions
    setSearchQuery,
    setFilter,
    setShowFilter,
    selectMatter,
    selectDocument,
    executeAIAction,
    sendChatRequest,
    refreshMatters,
    createNewMatter,
    
    // Computed values
    hasActiveFilters,
    totalMatters,
    aiGeneratedMatters,
    upcomingDeadlines
  };
};