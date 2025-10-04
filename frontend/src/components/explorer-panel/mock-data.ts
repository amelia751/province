// Mock data for AI-Enhanced Explorer Panel

import { AIMatter, AIFolder, AIDocument, AIDeadline, AIAction, MatterProgress, ChatContext, AIWorkflow, AITemplate } from './types';

// Mock chat contexts
const mockChatContexts: ChatContext[] = [
  {
    sessionId: 'session-1',
    lastInteraction: new Date('2024-01-15T10:30:00'),
    conversationSummary: 'Discussed case strategy and document requirements for personal injury claim',
    relatedDocuments: ['complaint-draft.docx', 'medical-records-request.pdf']
  },
  {
    sessionId: 'session-2', 
    lastInteraction: new Date('2024-01-14T14:20:00'),
    conversationSummary: 'Reviewed tax planning strategies for S-Corp international operations',
    relatedDocuments: ['form-1120s.pdf', 'foreign-tax-credit-calc.xlsx']
  }
];

// Mock deadlines
const mockDeadlines: AIDeadline[] = [
  {
    id: 'deadline-1',
    task: 'File Complaint',
    dueDate: new Date('2024-02-15T17:00:00'),
    priority: 'high',
    description: 'Statute of limitations expires',
    completed: false
  },
  {
    id: 'deadline-2',
    task: 'Serve Defendant',
    dueDate: new Date('2024-02-20T17:00:00'),
    priority: 'high',
    description: 'Must serve within 60 days of filing',
    completed: false
  },
  {
    id: 'deadline-3',
    task: 'File Form 1120S',
    dueDate: new Date('2024-03-15T23:59:59'),
    priority: 'high',
    description: 'S-Corp tax return due date',
    completed: false
  }
];

// Mock AI actions
const mockAIActions: AIAction[] = [
  {
    id: 'action-1',
    type: 'generate-document',
    label: 'Draft Complaint',
    description: 'Generate personal injury complaint based on case facts',
    practiceArea: 'legal',
    enabled: true
  },
  {
    id: 'action-2',
    type: 'research',
    label: 'Research Similar Cases',
    description: 'Find similar personal injury cases in California',
    practiceArea: 'legal',
    enabled: true
  },
  {
    id: 'action-3',
    type: 'calculate-deadline',
    label: 'Calculate Statute of Limitations',
    description: 'Determine filing deadline based on accident date',
    practiceArea: 'legal',
    enabled: true
  },
  {
    id: 'action-4',
    type: 'generate-document',
    label: 'Prepare Form 1120S',
    description: 'Generate S-Corp tax return with international schedules',
    practiceArea: 'tax',
    enabled: true
  },
  {
    id: 'action-5',
    type: 'compliance-check',
    label: 'International Compliance Review',
    description: 'Check foreign reporting requirements',
    practiceArea: 'tax',
    enabled: true
  }
];

// Mock folders for personal injury case
const personalInjuryFolders: AIFolder[] = [
  {
    id: 'folder-1',
    name: '01-Pleadings',
    purpose: 'Initial court filings and responses',
    requiredDocuments: ['Complaint', 'Answer', 'Cross-Complaint'],
    suggestedTemplates: ['CA Personal Injury Complaint Template'],
    children: [],
    expanded: true,
    aiGenerated: true,
    createdAt: new Date('2024-01-15T10:30:00')
  },
  {
    id: 'folder-2',
    name: '02-Discovery',
    purpose: 'Information gathering phase documents',
    requiredDocuments: ['Interrogatories', 'Document Requests', 'Depositions'],
    suggestedTemplates: ['Standard PI Discovery Set'],
    children: [],
    expanded: false,
    aiGenerated: true,
    createdAt: new Date('2024-01-15T10:30:00')
  },
  {
    id: 'folder-3',
    name: '03-Medical Records',
    purpose: 'Client medical documentation and bills',
    requiredDocuments: ['Hospital Records', 'Doctor Reports', 'Medical Bills'],
    suggestedTemplates: ['Medical Records Request Letter'],
    children: [],
    expanded: false,
    aiGenerated: true,
    createdAt: new Date('2024-01-15T10:30:00')
  },
  {
    id: 'folder-4',
    name: '04-Expert Witnesses',
    purpose: 'Expert testimony and professional reports',
    requiredDocuments: ['Expert Reports', 'CV', 'Fee Agreements'],
    suggestedTemplates: ['Expert Witness Retention Agreement'],
    children: [],
    expanded: false,
    aiGenerated: true,
    createdAt: new Date('2024-01-15T10:30:00')
  }
];

// Mock documents
const mockDocuments: AIDocument[] = [
  {
    id: 'doc-1',
    name: 'Complaint - Draft.docx',
    type: 'legal-complaint',
    path: '/matters/smith-v-abc/pleadings/complaint-draft.docx',
    status: 'draft',
    lastModified: new Date('2024-01-15T15:30:00'),
    aiGenerated: true,
    generationPrompt: 'Draft a personal injury complaint for car accident in California',
    collaborators: ['john.doe@firm.com'],
    size: 45000
  },
  {
    id: 'doc-2',
    name: 'Client Intake Form.pdf',
    type: 'legal-brief',
    path: '/matters/smith-v-abc/intake/client-intake.pdf',
    status: 'final',
    lastModified: new Date('2024-01-14T09:15:00'),
    aiGenerated: true,
    collaborators: ['jane.smith@firm.com'],
    size: 12000
  },
  {
    id: 'doc-3',
    name: 'Form 1120S - Draft.pdf',
    type: 'tax-return',
    path: '/matters/acme-corp-tax/returns/form-1120s-draft.pdf',
    status: 'review',
    lastModified: new Date('2024-01-16T11:45:00'),
    aiGenerated: true,
    generationPrompt: 'Prepare Form 1120S for S-Corp with international operations',
    collaborators: ['tax.preparer@firm.com'],
    size: 78000
  }
];

// Mock progress data
const mockProgress: MatterProgress[] = [
  {
    completedTasks: 3,
    totalTasks: 12,
    percentage: 25,
    nextMilestone: 'File Complaint',
    estimatedCompletion: new Date('2024-04-15T17:00:00')
  },
  {
    completedTasks: 8,
    totalTasks: 10,
    percentage: 80,
    nextMilestone: 'File Tax Return',
    estimatedCompletion: new Date('2024-03-10T17:00:00')
  }
];

// Mock AI Matters
export const mockAIMatters: AIMatter[] = [
  {
    id: 'matter-1',
    name: 'Smith v. ABC Insurance - Car Accident',
    type: 'personal-injury',
    practiceArea: 'legal',
    client: 'John Smith',
    description: 'Personal injury case arising from motor vehicle accident on Highway 101. Client sustained back injuries and seeks damages for medical expenses, lost wages, and pain and suffering.',
    status: 'active',
    priority: 'high',
    aiGenerated: true,
    generationPrompt: 'Build me a personal injury case for a car accident in California',
    structure: {
      folders: personalInjuryFolders,
      documents: [mockDocuments[0], mockDocuments[1]],
      workflows: [],
      templates: []
    },
    progress: mockProgress[0],
    deadlines: [mockDeadlines[0], mockDeadlines[1]],
    suggestedActions: [mockAIActions[0], mockAIActions[1], mockAIActions[2]],
    chatContext: mockChatContexts[0],
    createdAt: new Date('2024-01-15T10:30:00'),
    lastModified: new Date('2024-01-16T14:20:00'),
    assignedTo: ['john.doe@firm.com', 'jane.smith@firm.com'],
    jurisdiction: 'California',
    estimatedValue: 150000,
    tags: ['motor-vehicle', 'personal-injury', 'insurance-claim']
  },
  {
    id: 'matter-2',
    name: 'ACME Corp - S-Corp Tax Return 2023',
    type: 'tax-return',
    practiceArea: 'tax',
    client: 'ACME Corporation',
    description: 'Preparation of Form 1120S for S-Corporation with international subsidiaries. Includes foreign tax credit calculations and transfer pricing documentation.',
    status: 'active',
    priority: 'high',
    aiGenerated: true,
    generationPrompt: 'Help me prepare a corporate tax return for an S-Corp with international operations',
    structure: {
      folders: [
        {
          id: 'folder-tax-1',
          name: 'Tax Returns',
          purpose: 'Primary tax return forms and schedules',
          requiredDocuments: ['Form 1120S', 'Schedule K-1s'],
          suggestedTemplates: ['S-Corp Return Template'],
          children: [],
          expanded: true,
          aiGenerated: true,
          createdAt: new Date('2024-01-14T14:20:00')
        },
        {
          id: 'folder-tax-2',
          name: 'International Forms',
          purpose: 'Foreign entity reporting requirements',
          requiredDocuments: ['Form 8865', 'Form 5471'],
          suggestedTemplates: ['International Reporting Package'],
          children: [],
          expanded: false,
          aiGenerated: true,
          createdAt: new Date('2024-01-14T14:20:00')
        }
      ],
      documents: [mockDocuments[2]],
      workflows: [],
      templates: []
    },
    progress: mockProgress[1],
    deadlines: [mockDeadlines[2]],
    suggestedActions: [mockAIActions[3], mockAIActions[4]],
    chatContext: mockChatContexts[1],
    createdAt: new Date('2024-01-14T14:20:00'),
    lastModified: new Date('2024-01-16T16:30:00'),
    assignedTo: ['tax.preparer@firm.com'],
    jurisdiction: 'Federal',
    estimatedValue: 25000,
    tags: ['s-corp', 'international', 'tax-return', '2023']
  },
  {
    id: 'matter-3',
    name: 'TechStart Inc - SOX Compliance Assessment',
    type: 'compliance-assessment',
    practiceArea: 'compliance',
    client: 'TechStart Inc',
    description: 'Sarbanes-Oxley compliance assessment for newly public technology company. Includes internal controls evaluation and management certification preparation.',
    status: 'pending',
    priority: 'medium',
    aiGenerated: true,
    generationPrompt: 'Set up SOX compliance for a newly public company',
    structure: {
      folders: [
        {
          id: 'folder-comp-1',
          name: 'Controls Documentation',
          purpose: 'Internal control matrices and procedures',
          requiredDocuments: ['Control Matrix', 'Process Flows', 'Risk Assessment'],
          suggestedTemplates: ['SOX Controls Template'],
          children: [],
          expanded: false,
          aiGenerated: true,
          createdAt: new Date('2024-01-13T09:00:00')
        }
      ],
      documents: [],
      workflows: [],
      templates: []
    },
    progress: {
      completedTasks: 1,
      totalTasks: 15,
      percentage: 7,
      nextMilestone: 'Complete Risk Assessment',
      estimatedCompletion: new Date('2024-06-30T17:00:00')
    },
    deadlines: [
      {
        id: 'deadline-comp-1',
        task: 'Complete Management Assessment',
        dueDate: new Date('2024-03-31T17:00:00'),
        priority: 'medium',
        description: 'Management assessment of internal controls',
        completed: false
      }
    ],
    suggestedActions: [
      {
        id: 'action-comp-1',
        type: 'generate-document',
        label: 'Create Control Matrix',
        description: 'Generate internal controls documentation matrix',
        practiceArea: 'compliance',
        enabled: true
      }
    ],
    chatContext: {
      sessionId: 'session-3',
      lastInteraction: new Date('2024-01-13T09:00:00'),
      conversationSummary: 'Initial SOX compliance setup discussion',
      relatedDocuments: []
    },
    createdAt: new Date('2024-01-13T09:00:00'),
    lastModified: new Date('2024-01-13T09:00:00'),
    assignedTo: ['compliance.officer@firm.com'],
    jurisdiction: 'SEC',
    estimatedValue: 75000,
    tags: ['sox', 'compliance', 'public-company', 'internal-controls']
  }
];

// Mock filter options
export const mockFilterOptions = {
  practiceAreas: ['legal', 'accounting', 'tax', 'compliance'] as const,
  statuses: ['active', 'pending', 'completed', 'archived'] as const,
  priorities: ['high', 'medium', 'low'] as const,
  clients: ['John Smith', 'ACME Corporation', 'TechStart Inc'],
  assignees: ['john.doe@firm.com', 'jane.smith@firm.com', 'tax.preparer@firm.com', 'compliance.officer@firm.com']
};