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
    },
    {
        id: 'project-7',
        name: 'Martinez Real Estate Transaction',
        practiceArea: 'legal',
        client: 'Maria Martinez',
        lastOpened: new Date('2024-01-10T10:00:00'),
        path: '/projects/martinez-real-estate',
        description: 'Commercial property purchase and title review in downtown district',
        status: 'active',
        aiGenerated: true,
        progress: {
            completed: 4,
            total: 10,
            percentage: 40
        },
        tags: ['real-estate', 'commercial', 'title-review'],
        teamMembers: ['real.estate@firm.com']
    },
    {
        id: 'project-8',
        name: 'SoftwareInc - Payroll Tax Audit',
        practiceArea: 'tax',
        client: 'SoftwareInc',
        lastOpened: new Date('2024-01-09T14:20:00'),
        path: '/projects/softwareinc-payroll-audit',
        description: 'IRS payroll tax audit response and documentation preparation',
        status: 'active',
        aiGenerated: true,
        progress: {
            completed: 7,
            total: 14,
            percentage: 50
        },
        tags: ['payroll', 'irs', 'audit-response'],
        teamMembers: ['tax.partner@firm.com', 'tax.analyst@firm.com']
    },
    {
        id: 'project-9',
        name: 'HealthCare Partners - HIPAA Compliance',
        practiceArea: 'compliance',
        client: 'HealthCare Partners LLC',
        lastOpened: new Date('2024-01-08T09:30:00'),
        path: '/projects/healthcare-hipaa',
        description: 'HIPAA compliance audit and policy implementation for medical practice',
        status: 'active',
        aiGenerated: true,
        progress: {
            completed: 11,
            total: 20,
            percentage: 55
        },
        tags: ['hipaa', 'healthcare', 'privacy'],
        teamMembers: ['compliance.lead@firm.com', 'healthcare.specialist@firm.com']
    },
    {
        id: 'project-10',
        name: 'Thompson & Associates - Partnership Dissolution',
        practiceArea: 'accounting',
        client: 'Thompson & Associates',
        lastOpened: new Date('2024-01-07T16:15:00'),
        path: '/projects/thompson-dissolution',
        description: 'Partnership dissolution and asset distribution accounting',
        status: 'active',
        aiGenerated: false,
        progress: {
            completed: 5,
            total: 12,
            percentage: 42
        },
        tags: ['partnership', 'dissolution', 'asset-distribution'],
        teamMembers: ['cpa.lead@firm.com']
    },
    {
        id: 'project-11',
        name: 'Chen Immigration Petition',
        practiceArea: 'legal',
        client: 'Wei Chen',
        lastOpened: new Date('2024-01-06T11:45:00'),
        path: '/projects/chen-immigration',
        description: 'H-1B visa petition and employment verification documentation',
        status: 'active',
        aiGenerated: true,
        progress: {
            completed: 8,
            total: 10,
            percentage: 80
        },
        tags: ['immigration', 'visa', 'h1b'],
        teamMembers: ['immigration.attorney@firm.com']
    },
    {
        id: 'project-12',
        name: 'RetailMax - Sales Tax Review',
        practiceArea: 'tax',
        client: 'RetailMax Corporation',
        lastOpened: new Date('2024-01-05T13:00:00'),
        path: '/projects/retailmax-sales-tax',
        description: 'Multi-state sales tax nexus review and compliance planning',
        status: 'active',
        aiGenerated: true,
        progress: {
            completed: 15,
            total: 22,
            percentage: 68
        },
        tags: ['sales-tax', 'multi-state', 'nexus'],
        teamMembers: ['state.tax@firm.com', 'tax.analyst@firm.com']
    },
    {
        id: 'project-13',
        name: 'BioTech Labs - ISO Certification',
        practiceArea: 'compliance',
        client: 'BioTech Labs Inc',
        lastOpened: new Date('2024-01-04T08:30:00'),
        path: '/projects/biotech-iso',
        description: 'ISO 9001:2015 certification preparation and quality management system',
        status: 'active',
        aiGenerated: true,
        progress: {
            completed: 6,
            total: 18,
            percentage: 33
        },
        tags: ['iso', 'certification', 'quality-management'],
        teamMembers: ['compliance.director@firm.com']
    },
    {
        id: 'project-14',
        name: 'Williams Trademark Application',
        practiceArea: 'legal',
        client: 'Sarah Williams',
        lastOpened: new Date('2024-01-03T15:20:00'),
        path: '/projects/williams-trademark',
        description: 'Federal trademark application and comprehensive search',
        status: 'completed',
        aiGenerated: false,
        progress: {
            completed: 6,
            total: 6,
            percentage: 100
        },
        tags: ['trademark', 'intellectual-property', 'uspto'],
        teamMembers: ['ip.attorney@firm.com']
    },
    {
        id: 'project-15',
        name: 'GreenEnergy - R&D Tax Credits',
        practiceArea: 'tax',
        client: 'GreenEnergy Solutions',
        lastOpened: new Date('2024-01-02T10:45:00'),
        path: '/projects/greenenergy-rd-credits',
        description: 'Research and development tax credit calculation and documentation',
        status: 'active',
        aiGenerated: true,
        progress: {
            completed: 10,
            total: 16,
            percentage: 63
        },
        tags: ['r&d-credits', 'tax-incentives', 'clean-energy'],
        teamMembers: ['tax.credit.specialist@firm.com']
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
    },
    {
        id: 'template-7',
        name: 'Business Formation',
        description: 'LLC or Corporation formation with articles, operating agreement, and bylaws',
        practiceArea: 'legal',
        icon: '🏢',
        estimatedTime: '1-2 weeks',
        complexity: 'simple',
        aiPrompt: 'Set up a [entity type] in [state] with [ownership structure]'
    },
    {
        id: 'template-8',
        name: 'Employment Agreement',
        description: 'Executive employment agreement with non-compete and IP assignment',
        practiceArea: 'legal',
        icon: '📝',
        estimatedTime: '1 week',
        complexity: 'simple',
        aiPrompt: 'Draft employment agreement for [position] with [terms]'
    },
    {
        id: 'template-9',
        name: 'Partnership Tax Return',
        description: 'Form 1065 partnership return with K-1 schedules',
        practiceArea: 'tax',
        icon: '🤝',
        estimatedTime: '3-4 weeks',
        complexity: 'moderate',
        aiPrompt: 'Prepare partnership return for [business type] with [partners]'
    },
    {
        id: 'template-10',
        name: 'Internal Audit Program',
        description: 'Comprehensive internal audit framework and procedures',
        practiceArea: 'accounting',
        icon: '📋',
        estimatedTime: '4-6 weeks',
        complexity: 'complex',
        aiPrompt: 'Create internal audit program for [company type] focusing on [risk areas]'
    },
    {
        id: 'template-11',
        name: 'Privacy Policy & Terms',
        description: 'GDPR and CCPA compliant privacy policy and terms of service',
        practiceArea: 'compliance',
        icon: '🔒',
        estimatedTime: '1-2 weeks',
        complexity: 'moderate',
        aiPrompt: 'Draft privacy policy for [business type] complying with [regulations]'
    },
    {
        id: 'template-12',
        name: 'M&A Due Diligence',
        description: 'Merger and acquisition due diligence checklist and process',
        practiceArea: 'legal',
        icon: '🔄',
        estimatedTime: '8-12 weeks',
        complexity: 'complex',
        aiPrompt: 'Set up due diligence for [acquisition type] targeting [industry]'
    },
    {
        id: 'template-13',
        name: 'Estate Administration',
        description: 'Probate and estate administration with asset inventory',
        practiceArea: 'legal',
        icon: '⚱️',
        estimatedTime: '6-12 months',
        complexity: 'complex',
        aiPrompt: 'Manage estate administration for [estate size] in [jurisdiction]'
    },
    {
        id: 'template-14',
        name: 'Transfer Pricing Study',
        description: 'International transfer pricing documentation and analysis',
        practiceArea: 'tax',
        icon: '🌍',
        estimatedTime: '6-8 weeks',
        complexity: 'complex',
        aiPrompt: 'Prepare transfer pricing study for [transaction type] between [countries]'
    },
    {
        id: 'template-15',
        name: 'SEC Filing Review',
        description: '10-K and 10-Q filing review and compliance check',
        practiceArea: 'compliance',
        icon: '📑',
        estimatedTime: '3-4 weeks',
        complexity: 'complex',
        aiPrompt: 'Review SEC filing for [company] ensuring [requirements]'
    },
    {
        id: 'template-16',
        name: 'Cost Segregation Study',
        description: 'Depreciation analysis and cost segregation for real property',
        practiceArea: 'tax',
        icon: '🏗️',
        estimatedTime: '4-6 weeks',
        complexity: 'moderate',
        aiPrompt: 'Perform cost segregation for [property type] valued at [amount]'
    },
    {
        id: 'template-17',
        name: 'Quality Control Review',
        description: 'Peer review and quality control for accounting engagements',
        practiceArea: 'accounting',
        icon: '✅',
        estimatedTime: '2-3 weeks',
        complexity: 'moderate',
        aiPrompt: 'Conduct QC review for [engagement type] with [scope]'
    }
];