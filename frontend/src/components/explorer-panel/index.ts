// AI-Enhanced Explorer Panel - Main exports

export { default as EnhancedExplorerPanel } from './explorer-panel';
export { useExplorerState } from './use-explorer-state';
export { mockAIMatters, mockFilterOptions } from './mock-data';

// Export all types
export type {
  PracticeArea,
  MatterType,
  MatterStatus,
  MatterPriority,
  DocumentStatus,
  AIDeadline,
  AIAction,
  ChatContext,
  MatterProgress,
  AIFolder,
  AIDocument,
  MatterStructure,
  AIWorkflow,
  WorkflowStep,
  AITemplate,
  AIMatter,
  ExplorerFilter,
  ExplorerSearchResult,
  AIActionEvent,
  MatterSelectionEvent,
  DocumentSelectionEvent,
  ChatRequestEvent
} from './types';

export type {
  UseExplorerStateOptions,
  UseExplorerStateReturn
} from './use-explorer-state';