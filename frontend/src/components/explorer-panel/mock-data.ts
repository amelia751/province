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

// Mock folders for tax return (1040)
const taxReturnFolders: AIFolder[] = [
  {
    id: 'folder-intake',
    name: 'Intake',
    purpose: 'Client intake and organizer documents',
    requiredDocuments: ['Organizer'],
    suggestedTemplates: [],
    children: [],
    expanded: true,
    aiGenerated: false,
    createdAt: new Date('2025-01-10T09:00:00')
  },
  {
    id: 'folder-documents',
    name: 'Documents',
    purpose: 'Source documents and prior year returns',
    requiredDocuments: ['W-2', 'Prior Year Returns'],
    suggestedTemplates: [],
    children: [
      {
        id: 'folder-w2',
        name: 'W2',
        purpose: 'W-2 forms from employers',
        requiredDocuments: [],
        suggestedTemplates: [],
        children: [],
        expanded: false,
        aiGenerated: false,
        needsDocumentIngest: true,
        createdAt: new Date('2025-01-10T09:00:00')
      },
      {
        id: 'folder-prior-year',
        name: 'Prior_Year',
        purpose: 'Prior year tax returns',
        requiredDocuments: [],
        suggestedTemplates: [],
        children: [],
        expanded: false,
        aiGenerated: false,
        createdAt: new Date('2025-01-10T09:00:00')
      },
      {
        id: 'folder-1099-forms',
        name: '1099_Forms',
        purpose: '1099 information returns from financial institutions',
        requiredDocuments: [],
        suggestedTemplates: [],
        children: [],
        expanded: false,
        aiGenerated: false,
        createdAt: new Date('2025-10-11T17:49:00')
      }
    ],
    expanded: true,
    aiGenerated: false,
    createdAt: new Date('2025-01-10T09:00:00')
  },
  {
    id: 'folder-workpapers',
    name: 'Workpapers',
    purpose: 'Calculation worksheets and extracts',
    requiredDocuments: ['W2 Extracts', '1040 Calculations'],
    suggestedTemplates: [],
    children: [],
    expanded: true,
    aiGenerated: true,
    createdAt: new Date('2025-01-10T09:00:00')
  },
  {
    id: 'folder-returns',
    name: 'Returns',
    purpose: 'Draft and final tax returns',
    requiredDocuments: ['1040 Draft', '1040 Final'],
    suggestedTemplates: [],
    children: [
      {
        id: 'folder-forms-to-fill',
        name: 'Forms_To_Fill',
        purpose: 'Blank tax forms and schedules to complete',
        requiredDocuments: [],
        suggestedTemplates: [],
        children: [],
        expanded: true,
        aiGenerated: false,
        createdAt: new Date('2025-10-11T17:48:00')
      }
    ],
    expanded: true,
    aiGenerated: false,
    createdAt: new Date('2025-01-10T09:00:00')
  },
  {
    id: 'folder-deadlines',
    name: 'Deadlines',
    purpose: 'Important tax deadline reminders',
    requiredDocuments: ['Federal Deadlines'],
    suggestedTemplates: [],
    children: [],
    expanded: true,
    aiGenerated: false,
    createdAt: new Date('2025-01-10T09:00:00')
  },
  {
    id: 'folder-correspondence',
    name: 'Correspondence',
    purpose: 'Client and IRS correspondence',
    requiredDocuments: [],
    suggestedTemplates: [],
    children: [],
    expanded: true,
    aiGenerated: false,
    createdAt: new Date('2025-01-10T09:00:00')
  }
];

// Mock documents for tax return
const taxReturnDocuments: AIDocument[] = [
  {
    id: 'doc-tax-1',
    name: 'Organizer.md',
    type: 'tax-organizer',
    path: '/Doe_John_1040_2025/Intake/Organizer.md',
    status: 'final',
    lastModified: new Date('2025-01-10T10:00:00'),
    aiGenerated: false,
    collaborators: ['tax.preparer@firm.com'],
    size: 8500
  },
  {
    id: 'doc-w2-1',
    name: 'W2_XL_input_clean_1000.pdf',
    type: 'w2-form',
    path: '/Doe_John_1040_2025/Documents/W2/W2_XL_input_clean_1000.pdf',
    status: 'final',
    lastModified: new Date('2025-01-10T09:30:00'),
    aiGenerated: false,
    collaborators: ['tax.preparer@firm.com'],
    size: 143030,
    url: 'https://province-documents-[REDACTED-ACCOUNT-ID]-us-east-1.s3.us-east-1.amazonaws.com/datasets/w2-forms/W2_Clean_DataSet_01_20Sep2019/W2_XL_input_clean_1000.pdf'
  },
  {
    id: 'doc-w2-2',
    name: 'W2_XL_input_clean_1000.jpg',
    type: 'w2-form',
    path: '/Doe_John_1040_2025/Documents/W2/W2_XL_input_clean_1000.jpg',
    status: 'final',
    lastModified: new Date('2025-01-10T09:35:00'),
    aiGenerated: false,
    collaborators: ['tax.preparer@firm.com'],
    size: 350672,
    url: 'https://province-documents-[REDACTED-ACCOUNT-ID]-us-east-1.s3.us-east-1.amazonaws.com/datasets/w2-forms/W2_Clean_DataSet_01_20Sep2019/W2_XL_input_clean_1000.jpg'
  },
  {
    id: 'doc-tax-2',
    name: 'W2_Extracts.json',
    type: 'tax-workpaper',
    path: '/Doe_John_1040_2025/Workpapers/W2_Extracts.json',
    status: 'final',
    lastModified: new Date('2025-01-10T11:30:00'),
    aiGenerated: true,
    generationPrompt: 'Extract W-2 data from uploaded documents',
    collaborators: ['tax.preparer@firm.com'],
    size: 3200
  },
  {
    id: 'doc-tax-3',
    name: 'Calc_1040_Simple.json',
    type: 'tax-workpaper',
    path: '/Doe_John_1040_2025/Workpapers/Calc_1040_Simple.json',
    status: 'final',
    lastModified: new Date('2025-01-10T12:45:00'),
    aiGenerated: true,
    generationPrompt: 'Calculate Form 1040 from W-2 data',
    collaborators: ['tax.preparer@firm.com'],
    size: 15600
  },
  {
    id: 'doc-tax-4',
    name: '1040_Draft.pdf',
    type: 'tax-return',
    path: '/Doe_John_1040_2025/Returns/1040_Draft.pdf',
    status: 'review',
    lastModified: new Date('2025-01-10T14:00:00'),
    aiGenerated: true,
    generationPrompt: 'Generate Form 1040 PDF from calculations',
    collaborators: ['tax.preparer@firm.com'],
    size: 45000
  },
  {
    id: 'doc-tax-5',
    name: 'Federal.ics',
    type: 'calendar',
    path: '/Doe_John_1040_2025/Deadlines/Federal.ics',
    status: 'final',
    lastModified: new Date('2025-01-10T09:30:00'),
    aiGenerated: true,
    collaborators: ['tax.preparer@firm.com'],
    size: 1200
  },
  
  // IRS Tax Forms and Templates (from S3 templates bucket)
  // Core Forms
  {
    id: 'form-1040',
    name: 'Form 1040 - U.S. Individual Income Tax Return',
    type: 'tax-return',
    path: '/Doe_John_1040_2025/Returns/Forms_To_Fill/f1040.pdf',
    status: 'final',
    lastModified: new Date('2025-10-11T17:48:40'),
    aiGenerated: false,
    collaborators: ['tax.preparer@firm.com'],
    size: 163287,
    url: 'https://province-templates-[REDACTED-ACCOUNT-ID]-us-east-1.s3.us-east-1.amazonaws.com/tax_forms/2024/f1040.pdf'
  },
  {
    id: 'form-1040s1',
    name: 'Schedule 1 - Additional Income and Adjustments',
    type: 'tax-return',
    path: '/Doe_John_1040_2025/Returns/Forms_To_Fill/f1040s1.pdf',
    status: 'final',
    lastModified: new Date('2025-10-11T17:48:40'),
    aiGenerated: false,
    collaborators: ['tax.preparer@firm.com'],
    size: 90905,
    url: 'https://province-templates-[REDACTED-ACCOUNT-ID]-us-east-1.s3.us-east-1.amazonaws.com/tax_forms/2024/f1040s1.pdf'
  },
  {
    id: 'form-1040s2',
    name: 'Schedule 2 - Additional Taxes',
    type: 'tax-return',
    path: '/Doe_John_1040_2025/Returns/Forms_To_Fill/f1040s2.pdf',
    status: 'final',
    lastModified: new Date('2025-10-11T17:48:40'),
    aiGenerated: false,
    collaborators: ['tax.preparer@firm.com'],
    size: 234638,
    url: 'https://province-templates-[REDACTED-ACCOUNT-ID]-us-east-1.s3.us-east-1.amazonaws.com/tax_forms/2024/f1040s2.pdf'
  },
  {
    id: 'form-1040s3',
    name: 'Schedule 3 - Additional Credits and Payments',
    type: 'tax-return',
    path: '/Doe_John_1040_2025/Returns/Forms_To_Fill/f1040s3.pdf',
    status: 'final',
    lastModified: new Date('2025-10-11T17:48:41'),
    aiGenerated: false,
    collaborators: ['tax.preparer@firm.com'],
    size: 69979,
    url: 'https://province-templates-[REDACTED-ACCOUNT-ID]-us-east-1.s3.us-east-1.amazonaws.com/tax_forms/2024/f1040s3.pdf'
  },
  
  // Itemized Deductions and Income Schedules
  {
    id: 'form-1040sa',
    name: 'Schedule A - Itemized Deductions',
    type: 'tax-return',
    path: '/Doe_John_1040_2025/Returns/Forms_To_Fill/f1040sa.pdf',
    status: 'final',
    lastModified: new Date('2025-10-11T17:48:41'),
    aiGenerated: false,
    collaborators: ['tax.preparer@firm.com'],
    size: 78925,
    url: 'https://province-templates-[REDACTED-ACCOUNT-ID]-us-east-1.s3.us-east-1.amazonaws.com/tax_forms/2024/f1040sa.pdf'
  },
  {
    id: 'form-1040sb',
    name: 'Schedule B - Interest and Ordinary Dividends',
    type: 'tax-return',
    path: '/Doe_John_1040_2025/Returns/Forms_To_Fill/f1040sb.pdf',
    status: 'final',
    lastModified: new Date('2025-10-11T17:48:41'),
    aiGenerated: false,
    collaborators: ['tax.preparer@firm.com'],
    size: 76237,
    url: 'https://province-templates-[REDACTED-ACCOUNT-ID]-us-east-1.s3.us-east-1.amazonaws.com/tax_forms/2024/f1040sb.pdf'
  },
  {
    id: 'form-1040sc',
    name: 'Schedule C - Profit or Loss From Business',
    type: 'tax-return',
    path: '/Doe_John_1040_2025/Returns/Forms_To_Fill/f1040sc.pdf',
    status: 'final',
    lastModified: new Date('2025-10-11T17:48:41'),
    aiGenerated: false,
    collaborators: ['tax.preparer@firm.com'],
    size: 122304,
    url: 'https://province-templates-[REDACTED-ACCOUNT-ID]-us-east-1.s3.us-east-1.amazonaws.com/tax_forms/2024/f1040sc.pdf'
  },
  {
    id: 'form-1040sd',
    name: 'Schedule D - Capital Gains and Losses',
    type: 'tax-return',
    path: '/Doe_John_1040_2025/Returns/Forms_To_Fill/f1040sd.pdf',
    status: 'final',
    lastModified: new Date('2025-10-11T17:48:42'),
    aiGenerated: false,
    collaborators: ['tax.preparer@firm.com'],
    size: 97168,
    url: 'https://province-templates-[REDACTED-ACCOUNT-ID]-us-east-1.s3.us-east-1.amazonaws.com/tax_forms/2024/f1040sd.pdf'
  },
  {
    id: 'form-1040se',
    name: 'Schedule E - Supplemental Income and Loss',
    type: 'tax-return',
    path: '/Doe_John_1040_2025/Returns/Forms_To_Fill/f1040se.pdf',
    status: 'final',
    lastModified: new Date('2025-10-11T17:48:43'),
    aiGenerated: false,
    collaborators: ['tax.preparer@firm.com'],
    size: 148158,
    url: 'https://province-templates-[REDACTED-ACCOUNT-ID]-us-east-1.s3.us-east-1.amazonaws.com/tax_forms/2024/f1040se.pdf'
  },
  
  // Tax Credits and Special Forms
  {
    id: 'form-8812',
    name: 'Form 8812 - Credits for Qualifying Children and Other Dependents',
    type: 'tax-return',
    path: '/Doe_John_1040_2025/Returns/Forms_To_Fill/f8812.pdf',
    status: 'final',
    lastModified: new Date('2025-10-11T17:49:22'),
    aiGenerated: false,
    collaborators: ['tax.preparer@firm.com'],
    size: 115238,
    url: 'https://province-templates-[REDACTED-ACCOUNT-ID]-us-east-1.s3.us-east-1.amazonaws.com/tax_forms/2024/f8812.pdf'
  },
  {
    id: 'form-2441',
    name: 'Form 2441 - Child and Dependent Care Expenses',
    type: 'tax-return',
    path: '/Doe_John_1040_2025/Returns/Forms_To_Fill/f2441.pdf',
    status: 'final',
    lastModified: new Date('2025-10-11T17:49:23'),
    aiGenerated: false,
    collaborators: ['tax.preparer@firm.com'],
    size: 121249,
    url: 'https://province-templates-[REDACTED-ACCOUNT-ID]-us-east-1.s3.us-east-1.amazonaws.com/tax_forms/2024/f2441.pdf'
  },
  {
    id: 'form-8863',
    name: 'Form 8863 - Education Credits',
    type: 'tax-return',
    path: '/Doe_John_1040_2025/Returns/Forms_To_Fill/f8863.pdf',
    status: 'final',
    lastModified: new Date('2025-10-11T17:49:23'),
    aiGenerated: false,
    collaborators: ['tax.preparer@firm.com'],
    size: 118839,
    url: 'https://province-templates-[REDACTED-ACCOUNT-ID]-us-east-1.s3.us-east-1.amazonaws.com/tax_forms/2024/f8863.pdf'
  },
  {
    id: 'form-8880',
    name: 'Form 8880 - Credit for Qualified Retirement Savings Contributions',
    type: 'tax-return',
    path: '/Doe_John_1040_2025/Returns/Forms_To_Fill/f8880.pdf',
    status: 'final',
    lastModified: new Date('2025-10-11T17:49:23'),
    aiGenerated: false,
    collaborators: ['tax.preparer@firm.com'],
    size: 95617,
    url: 'https://province-templates-[REDACTED-ACCOUNT-ID]-us-east-1.s3.us-east-1.amazonaws.com/tax_forms/2024/f8880.pdf'
  },
  {
    id: 'form-8962',
    name: 'Form 8962 - Premium Tax Credit',
    type: 'tax-return',
    path: '/Doe_John_1040_2025/Returns/Forms_To_Fill/f8962.pdf',
    status: 'final',
    lastModified: new Date('2025-10-11T17:49:23'),
    aiGenerated: false,
    collaborators: ['tax.preparer@firm.com'],
    size: 117814,
    url: 'https://province-templates-[REDACTED-ACCOUNT-ID]-us-east-1.s3.us-east-1.amazonaws.com/tax_forms/2024/f8962.pdf'
  },
  {
    id: 'form-8867',
    name: 'Form 8867 - Paid Preparers Due Diligence Checklist',
    type: 'tax-return',
    path: '/Doe_John_1040_2025/Returns/Forms_To_Fill/f8867.pdf',
    status: 'final',
    lastModified: new Date('2025-10-11T17:49:23'),
    aiGenerated: false,
    collaborators: ['tax.preparer@firm.com'],
    size: 134641,
    url: 'https://province-templates-[REDACTED-ACCOUNT-ID]-us-east-1.s3.us-east-1.amazonaws.com/tax_forms/2024/f8867.pdf'
  },
  
  // Information Returns (1099 Forms) - moved to Documents folder since these are received documents
  {
    id: 'form-1099int',
    name: 'Form 1099-INT - Interest Income (Template)',
    type: 'tax-organizer',
    path: '/Doe_John_1040_2025/Documents/1099_Forms/f1099int.pdf',
    status: 'final',
    lastModified: new Date('2025-10-11T17:49:24'),
    aiGenerated: false,
    collaborators: ['tax.preparer@firm.com'],
    size: 538774,
    url: 'https://province-templates-[REDACTED-ACCOUNT-ID]-us-east-1.s3.us-east-1.amazonaws.com/tax_forms/2024/f1099int.pdf'
  },
  {
    id: 'form-1099div',
    name: 'Form 1099-DIV - Dividends and Distributions (Template)',
    type: 'tax-organizer',
    path: '/Doe_John_1040_2025/Documents/1099_Forms/f1099div.pdf',
    status: 'final',
    lastModified: new Date('2025-10-11T17:49:24'),
    aiGenerated: false,
    collaborators: ['tax.preparer@firm.com'],
    size: 539778,
    url: 'https://province-templates-[REDACTED-ACCOUNT-ID]-us-east-1.s3.us-east-1.amazonaws.com/tax_forms/2024/f1099div.pdf'
  },
  {
    id: 'form-1099r',
    name: 'Form 1099-R - Retirement Distributions (Template)',
    type: 'tax-organizer',
    path: '/Doe_John_1040_2025/Documents/1099_Forms/f1099r.pdf',
    status: 'final',
    lastModified: new Date('2025-10-11T17:49:24'),
    aiGenerated: false,
    collaborators: ['tax.preparer@firm.com'],
    size: 601017,
    url: 'https://province-templates-[REDACTED-ACCOUNT-ID]-us-east-1.s3.us-east-1.amazonaws.com/tax_forms/2024/f1099r.pdf'
  },
  {
    id: 'form-1099g',
    name: 'Form 1099-G - Government Payments (Template)',
    type: 'tax-organizer',
    path: '/Doe_John_1040_2025/Documents/1099_Forms/f1099g.pdf',
    status: 'final',
    lastModified: new Date('2025-10-11T17:49:25'),
    aiGenerated: false,
    collaborators: ['tax.preparer@firm.com'],
    size: 523268,
    url: 'https://province-templates-[REDACTED-ACCOUNT-ID]-us-east-1.s3.us-east-1.amazonaws.com/tax_forms/2024/f1099g.pdf'
  },
  
  // W-2 Template (moved to Documents/W2 folder where it belongs)
  {
    id: 'form-w2-template',
    name: 'Form W-2 - Wage and Tax Statement (Template)',
    type: 'w2-form',
    path: '/Doe_John_1040_2025/Documents/W2/fw2.pdf',
    status: 'final',
    lastModified: new Date('2025-10-11T17:48:44'),
    aiGenerated: false,
    collaborators: ['tax.preparer@firm.com'],
    size: 1343180,
    url: 'https://province-templates-[REDACTED-ACCOUNT-ID]-us-east-1.s3.us-east-1.amazonaws.com/tax_forms/2024/fw2.pdf'
  },
  
  // Instructions and Reference Materials
  {
    id: 'form-1040-instructions',
    name: 'Form 1040 Instructions - General Instructions',
    type: 'tax-return',
    path: '/Doe_John_1040_2025/Returns/Forms_To_Fill/i1040gi.pdf',
    status: 'final',
    lastModified: new Date('2025-10-11T17:48:44'),
    aiGenerated: false,
    collaborators: ['tax.preparer@firm.com'],
    size: 4375877,
    url: 'https://province-templates-[REDACTED-ACCOUNT-ID]-us-east-1.s3.us-east-1.amazonaws.com/tax_forms/2024/i1040gi.pdf'
  },
  {
    id: 'form-tax-tables',
    name: 'Tax Tables for 2024',
    type: 'tax-return',
    path: '/Doe_John_1040_2025/Returns/Forms_To_Fill/i1040tt.pdf',
    status: 'final',
    lastModified: new Date('2025-10-11T17:49:25'),
    aiGenerated: false,
    collaborators: ['tax.preparer@firm.com'],
    size: 2967636,
    url: 'https://province-templates-[REDACTED-ACCOUNT-ID]-us-east-1.s3.us-east-1.amazonaws.com/tax_forms/2024/i1040tt.pdf'
  }
];

// Mock AI Matters
export const mockAIMatters: AIMatter[] = [
  {
    id: 'matter-1',
    name: 'Doe_John_1040_2025',
    type: 'tax-return',
    practiceArea: 'tax',
    client: 'John Doe',
    description: 'Individual Form 1040 tax return for 2025 tax year. Simple W-2 employee return with standard deduction.',
    status: 'active',
    priority: 'high',
    aiGenerated: true,
    generationPrompt: 'Prepare individual 1040 tax return for W-2 employee',
    structure: {
      folders: taxReturnFolders,
      documents: taxReturnDocuments,
      workflows: [],
      templates: []
    },
    progress: {
      completedTasks: 4,
      totalTasks: 6,
      percentage: 67,
      nextMilestone: 'Client Review',
      estimatedCompletion: new Date('2025-04-10T17:00:00')
    },
    deadlines: [
      {
        id: 'deadline-tax-1',
        task: 'File Form 1040',
        dueDate: new Date('2025-04-15T23:59:59'),
        priority: 'high',
        description: 'Federal income tax return filing deadline',
        completed: false
      }
    ],
    suggestedActions: [mockAIActions[3], mockAIActions[4]],
    chatContext: {
      sessionId: 'session-tax-1',
      lastInteraction: new Date('2025-01-10T14:30:00'),
      conversationSummary: 'Discussed W-2 income and standard deduction',
      relatedDocuments: ['Organizer.md', 'W2_Extracts.json']
    },
    createdAt: new Date('2025-01-10T09:00:00'),
    lastModified: new Date('2025-01-10T14:30:00'),
    assignedTo: ['tax.preparer@firm.com'],
    jurisdiction: 'Federal',
    estimatedValue: 500,
    tags: ['1040', 'individual', 'w2-employee', '2025']
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