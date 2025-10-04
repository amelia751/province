/**
 * Agent Demo Component
 * Demonstrates the AI agent capabilities with example interactions
 */

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  FileText, 
  Search, 
  Calendar, 
  Bot, 
  Zap, 
  CheckCircle,
  ArrowRight,
  MessageSquare
} from 'lucide-react';

interface DemoScenario {
  id: string;
  title: string;
  description: string;
  agent: 'legal_drafting' | 'legal_research' | 'case_management';
  prompt: string;
  expectedActions: string[];
  icon: React.ReactNode;
}

const demoScenarios: DemoScenario[] = [
  {
    id: 'contract_drafting',
    title: 'Contract Drafting',
    description: 'Generate a comprehensive service agreement with all necessary clauses',
    agent: 'legal_drafting',
    prompt: 'I need to draft a service agreement for a new client. The client is a tech startup that needs ongoing legal consultation. Please create the contract and set up the matter.',
    expectedActions: ['Create Matter', 'Generate Contract', 'Set Deadlines'],
    icon: <FileText className="h-5 w-5" />
  },
  {
    id: 'legal_research',
    title: 'Legal Research',
    description: 'Research case law and precedents for a specific legal issue',
    agent: 'legal_research',
    prompt: 'I need to research recent cases related to data privacy violations in California. Please find relevant precedents and analyze the current legal landscape.',
    expectedActions: ['Search Cases', 'Generate Research Report', 'Cite Sources'],
    icon: <Search className="h-5 w-5" />
  },
  {
    id: 'case_management',
    title: 'Case Management',
    description: 'Set up a new matter with deadlines and task management',
    agent: 'case_management',
    prompt: 'I have a new corporate merger case. Please set up the matter structure, create the necessary folders, and establish key deadlines for due diligence.',
    expectedActions: ['Create Matter Structure', 'Set Deadlines', 'Create Tasks'],
    icon: <Calendar className="h-5 w-5" />
  }
];

interface AgentDemoProps {
  onRunDemo?: (scenario: DemoScenario) => void;
}

const AgentDemo: React.FC<AgentDemoProps> = ({ onRunDemo }) => {
  const [runningDemo, setRunningDemo] = useState<string | null>(null);

  const handleRunDemo = async (scenario: DemoScenario) => {
    setRunningDemo(scenario.id);
    
    // Simulate demo execution
    setTimeout(() => {
      setRunningDemo(null);
      onRunDemo?.(scenario);
    }, 2000);
  };

  const getAgentBadgeColor = (agent: DemoScenario['agent']) => {
    switch (agent) {
      case 'legal_drafting':
        return 'bg-blue-100 text-blue-800';
      case 'legal_research':
        return 'bg-purple-100 text-purple-800';
      case 'case_management':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center space-y-2">
        <h2 className="text-2xl font-bold text-gray-900">AI Agent Capabilities</h2>
        <p className="text-gray-600">
          Experience how our AI agents can perform real functions to help with legal work
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-1 lg:grid-cols-3">
        {demoScenarios.map((scenario) => (
          <Card key={scenario.id} className="relative overflow-hidden">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  {scenario.icon}
                  <CardTitle className="text-lg">{scenario.title}</CardTitle>
                </div>
                <Badge className={getAgentBadgeColor(scenario.agent)}>
                  {scenario.agent.replace('_', ' ')}
                </Badge>
              </div>
              <CardDescription className="text-sm">
                {scenario.description}
              </CardDescription>
            </CardHeader>

            <CardContent className="space-y-4">
              <div className="bg-gray-50 p-3 rounded-lg">
                <div className="flex items-start space-x-2">
                  <MessageSquare className="h-4 w-4 text-gray-500 mt-0.5 flex-shrink-0" />
                  <p className="text-sm text-gray-700 italic">
                    "{scenario.prompt}"
                  </p>
                </div>
              </div>

              <div className="space-y-2">
                <h4 className="text-sm font-medium text-gray-900">Expected Actions:</h4>
                <div className="space-y-1">
                  {scenario.expectedActions.map((action, index) => (
                    <div key={index} className="flex items-center space-x-2 text-sm">
                      <CheckCircle className="h-3 w-3 text-green-500" />
                      <span className="text-gray-600">{action}</span>
                    </div>
                  ))}
                </div>
              </div>

              <Button
                onClick={() => handleRunDemo(scenario)}
                disabled={runningDemo !== null}
                className="w-full"
                variant={runningDemo === scenario.id ? "secondary" : "default"}
              >
                {runningDemo === scenario.id ? (
                  <>
                    <Bot className="h-4 w-4 mr-2 animate-pulse" />
                    Running Demo...
                  </>
                ) : (
                  <>
                    <Zap className="h-4 w-4 mr-2" />
                    Try This Demo
                    <ArrowRight className="h-4 w-4 ml-2" />
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start space-x-3">
          <Bot className="h-5 w-5 text-blue-600 mt-0.5" />
          <div>
            <h3 className="text-sm font-medium text-blue-900">How It Works</h3>
            <p className="text-sm text-blue-700 mt-1">
              Each agent is powered by AWS Bedrock and can perform real functions like creating documents, 
              setting up matters, managing deadlines, and conducting research. The agents understand natural 
              language and can execute complex workflows based on your requests.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgentDemo;