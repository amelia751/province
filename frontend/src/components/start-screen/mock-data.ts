// Mock data for Start Screen

import { RecentProject, ProjectTemplate } from './types';

export const mockRecentProjects: RecentProject[] = [
  {
    id: 'project-1',
    name: 'Smith v. ABC Insurance - Car Accident',
    practiceArea: 'legal',
    client: 'John Smith',
    lastOpened: new Date('2024-01-16T14:30:00'),
    path: '/projects/smith-v-abc-insurance',
    description: 'Personal injury case arising from motor vehicle accident on Highway 101',
    status: 'active',
    aiGenerated: true,
    progress: {
      completed: 8,
      total: 15,
      percentage: 53
    },
    tags: ['personal-injury', 'motor-vehicle', 'california'],
    teamMembers: ['john.doe@firm.com', 'jane.smith@firm.com']
  },
  {
    id: 'project-2',
    name: 'ACME Corp - S-Corp Tax Return 2023',
    practiceArea: 'tax',
    client: 'ACME Corporation',
    lastOpened: new Date('2024-01-15T16:45:00'),
    path: '/projects/acme-corp-tax-2023',
    description: 'Annual S-Corporation tax return with international operations',
    status: 'active',
    aiGenerated: true,
    progress: {
      completed: 12,
      total: 18,
      percentage: 67
    },
    tags: ['s-corp', 'international', 'tax-return'],
    teamMembers: ['tax.preparer@firm.com']
  },
  {
    id: 'project-3',
    name: 'TechStart Inc - SOX Compliance Assessment',
    practiceArea: 'compliance',
    client: 'TechStart Inc',
    lastOpened: new Date('2024-01-14T11:20:00'),
    path: '/projects/techstart-sox-compliance',
    description: 'Sarbanes-Oxley compliance assessment for newly public company',
    status: 'active',
    aiGenerated: true,
    progress: {
      completed: 3,
      total: 20,
      percentage: 15
    },
    tags: ['sox', 'compliance', 'public-company'],
    teamMembers: ['compliance.officer@firm.com', 'audit.manager@firm.com']
  },
  {
    id: 'project-4',
    name: 'Global Manufacturing - Financial Audit 2023',
    practiceArea: 'accounting',
    client: 'Global Manufacturing Ltd',
    lastOpened: new Date('2024-01-13T09:15:00'),
    path: '/projects/global-manufacturing-audit',
    description: 'Annual financial statement audit for manufacturing company',
    status: 'completed',
    aiGenerated: false,
    progress: {
      completed: 25,
      total: 25,
      percentage: 100
    },
    tags: ['audit', 'manufacturing', 'financial-statements'],
    teamMembers: ['audit.partner@firm.com', 'senior.auditor@firm.com']
  },
  {
    id: 'project-5',
    name: 'Johnson Estate Planning',
    practiceArea: 'legal',
    client: 'Robert Johnson',
    lastOpened: new Date('2024-01-12T15:30:00'),
    path: '/projects/johnson-estate-planning',
    description: 'Comprehensive estate planning including trusts and tax optimization',
    status: 'active',
    aiGenerated: true,
    progress: {
      completed: 6,
      total: 12,
      percentage: 50
    },
    tags: ['estate-planning', 'trusts', 'tax-optimization'],
    teamMembers: ['estate.attorney@firm.com']
  },
  {
    id: 'project-6',
    name: 'RetailCorp - GDPR Compliance Review',
    practiceArea: 'compliance',
    client: 'RetailCorp International',
    lastOpened: new Date('2024-01-11T13:45:00'),
    path: '/projects/retailcorp-gdpr-review',
    description: 'GDPR compliance review for international retail operations',
    status: 'active',
    aiGenerated: true,
    progress: {
      completed: 9,
      total: 16,
      percentage: 56
    },
    tags: ['gdpr', 'privacy', 'international', 'retail'],
    teamMembers: ['privacy.counsel@firm.com', 'compliance.analyst@firm.com']
  }
];

export const mockProjectTemplates: ProjectTemplate[] = [
  {
    id: 'template-1',
    name: 'Personal Injury Case',
    description: 'Complete personal injury case structure with pleadings, discovery, and settlement documents',
    practiceArea: 'legal',
    icon: '⚖️',
    estimatedTime: '2-6 months',
    complexity: 'moderate',
    aiPrompt: 'Build me a personal injury case for [accident type] in [jurisdiction]'
  },
  {
    id: 'template-2',
    name: 'Corporate Tax Return',
    description: 'Corporate tax return preparation with all necessary forms and schedules',
    practiceArea: 'tax',
    icon: '📊',
    estimatedTime: '2-4 weeks',
    complexity: 'complex',
    aiPrompt: 'Prepare a corporate tax return for [entity type] with [special circumstances]'
  },
  {
    id: 'template-3',
    name: 'Financial Statement Audit',
    description: 'Complete audit engagement from planning to reporting',
    practiceArea: 'accounting',
    icon: '🔍',
    estimatedTime: '6-12 weeks',
    complexity: 'complex',
    aiPrompt: 'Set up a financial statement audit for [company type] with [revenue size]'
  },
  {
    id: 'template-4',
    name: 'Compliance Assessment',
    description: 'Regulatory compliance assessment and remediation plan',
    practiceArea: 'compliance',
    icon: '🛡️',
    estimatedTime: '4-8 weeks',
    complexity: 'moderate',
    aiPrompt: 'Create a compliance assessment for [regulation] in [industry]'
  },
  {
    id: 'template-5',
    name: 'Contract Review & Negotiation',
    description: 'Contract analysis, redlining, and negotiation support',
    practiceArea: 'legal',
    icon: '📄',
    estimatedTime: '1-3 weeks',
    complexity: 'simple',
    aiPrompt: 'Help me review and negotiate a [contract type] for [client type]'
  },
  {
    id: 'template-6',
    name: 'Individual Tax Return',
    description: 'Individual tax return with standard and complex situations',
    practiceArea: 'tax',
    icon: '👤',
    estimatedTime: '1-2 weeks',
    complexity: 'simple',
    aiPrompt: 'Prepare an individual tax return for [taxpayer situation]'
  }
];