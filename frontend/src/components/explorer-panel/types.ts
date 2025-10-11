// AI-Enhanced Explorer Panel Types for Province Cursor

export type PracticeArea = 'legal' | 'accounting' | 'tax' | 'compliance';

export type MatterType = 
  | 'personal-injury' 
  | 'corporate-law' 
  | 'contract-dispute'
  | 'financial-audit'
  | 'tax-return'
  | 'compliance-assessment'
  | 'regulatory-filing';

export type MatterStatus = 'active' | 'pending' | 'completed' | 'archived';
export type MatterPriority = 'high' | 'medium' | 'low';
export type DocumentStatus = 'draft' | 'review' | 'final' | 'archived';

export interface AIDeadline {
  id: string;
  task: string;
  dueDate: Date;
  priority: MatterPriority;
  description?: string;
  completed: boolean;
}

export interface AIAction {
  id: string;
  type: 'generate-document' | 'create-deadline' | 'research' | 'compliance-check' | 'calculate-deadline';
  label: string;
  description: string;
  practiceArea: PracticeArea;
  enabled: boolean;
}

export interface ChatContext {
  sessionId: string;
  lastInteraction: Date;
  conversationSummary: string;
  relatedDocuments: string[];
}

export interface MatterProgress {
  completedTasks: number;
  totalTasks: number;
  percentage: number;
  nextMilestone?: string;
  estimatedCompletion?: Date;
}

export interface AIFolder {
  id: string;
  name: string;
  purpose: string; // AI explanation of folder purpose
  requiredDocuments: string[];
  suggestedTemplates: string[];
  children: AIFolder[];
  expanded?: boolean;
  aiGenerated: boolean;
  needsDocumentIngest?: boolean; // Flag for folders that accept document uploads
  createdAt: Date;
}

export interface AIDocument {
  id: string;
  name: string;
  type: 'legal-complaint' | 'legal-motion' | 'legal-contract' | 'legal-brief'
       | 'tax-return' | 'tax-memo' | 'tax-planning' | 'tax-organizer' | 'tax-workpaper' | 'w2-form' | 'calendar'
       | 'financial-statement' | 'audit-report' | 'management-letter'
       | 'compliance-report' | 'policy-document' | 'audit-checklist';
  path: string;
  status: DocumentStatus;
  lastModified: Date;
  aiGenerated: boolean;
  generationPrompt?: string;
  collaborators: string[];
  size?: number;
  url?: string; // Optional URL for external documents (e.g., S3 links)
}

export interface MatterStructure {
  folders: AIFolder[];
  documents: AIDocument[];
  workflows: AIWorkflow[];
  templates: AITemplate[];
}

export interface AIWorkflow {
  id: string;
  name: string;
  description: string;
  steps: WorkflowStep[];
  currentStep: number;
  practiceArea: PracticeArea;
  estimatedDuration: string;
}

export interface WorkflowStep {
  id: string;
  name: string;
  description: string;
  completed: boolean;
  requiredDocuments: string[];
  estimatedTime: string;
}

export interface AITemplate {
  id: string;
  name: string;
  description: string;
  practiceArea: PracticeArea;
  matterType: MatterType;
  jurisdiction?: string;
  lastUsed?: Date;
}

export interface AIMatter {
  id: string;
  name: string;
  type: MatterType;
  practiceArea: PracticeArea;
  client: string;
  description: string;
  status: MatterStatus;
  priority: MatterPriority;
  aiGenerated: boolean;
  generationPrompt?: string;
  structure: MatterStructure;
  progress: MatterProgress;
  deadlines: AIDeadline[];
  suggestedActions: AIAction[];
  chatContext: ChatContext;
  createdAt: Date;
  lastModified: Date;
  assignedTo: string[];
  jurisdiction?: string;
  estimatedValue?: number;
  tags: string[];
}

export interface ExplorerFilter {
  practiceArea?: PracticeArea;
  status?: MatterStatus;
  priority?: MatterPriority;
  client?: string;
  assignedTo?: string;
  dateRange?: {
    start: Date;
    end: Date;
  };
  aiGenerated?: boolean;
  hasUpcomingDeadlines?: boolean;
}

export interface ExplorerSearchResult {
  matters: AIMatter[];
  documents: AIDocument[];
  totalResults: number;
  searchTime: number;
}

// Event types for AI actions
export interface AIActionEvent {
  type: 'ai-action-triggered';
  action: AIAction;
  matterId: string;
  context: any;
}

export interface MatterSelectionEvent {
  type: 'matter-selected';
  matter: AIMatter;
}

export interface DocumentSelectionEvent {
  type: 'document-selected';
  document: AIDocument;
  matterId: string;
}

export interface ChatRequestEvent {
  type: 'chat-request';
  request: string;
  context: {
    matterId?: string;
    practiceArea: PracticeArea;
    selectedItems?: string[];
  };
}