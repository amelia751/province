// Start Screen Types for Province Cursor

export type PracticeArea = 'legal' | 'accounting' | 'tax' | 'compliance';

export interface RecentProject {
  id: string;
  name: string;
  practiceArea: PracticeArea;
  client: string;
  lastOpened: Date;
  path: string;
  description: string;
  status: 'active' | 'completed' | 'archived';
  aiGenerated: boolean;
  progress?: {
    completed: number;
    total: number;
    percentage: number;
  };
  tags: string[];
  teamMembers: string[];
}

export interface ProjectTemplate {
  id: string;
  name: string;
  description: string;
  practiceArea: PracticeArea;
  icon: string;
  estimatedTime: string;
  complexity: 'simple' | 'moderate' | 'complex';
  aiPrompt: string;
}

export interface StartScreenState {
  view: 'start' | 'project-explorer';
  selectedProject: RecentProject | null;
  recentProjects: RecentProject[];
  searchQuery: string;
  filteredProjects: RecentProject[];
}

export interface ProjectSelectionEvent {
  type: 'project-selected';
  project: RecentProject;
}

export interface NewProjectEvent {
  type: 'new-project-requested';
  template?: ProjectTemplate;
  prompt?: string;
}

export interface OpenProjectEvent {
  type: 'open-project-requested';
  path?: string;
}