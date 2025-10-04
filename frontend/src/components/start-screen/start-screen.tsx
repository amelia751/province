"use client";

import React, { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';
import {
  Search,
  FolderOpen,
  Plus,
  Users,
  Briefcase,
  Calculator,
  FileText,
  Shield,
  ArrowRight,
  Grid3X3,
  List,
  ChevronRight
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

import { RecentProject, ProjectTemplate, PracticeArea } from './types';
import { mockRecentProjects, mockProjectTemplates } from './mock-data';

interface StartScreenProps {
  onProjectSelect: (project: RecentProject) => void;
  onNewProject: (template?: ProjectTemplate, prompt?: string) => void;
  onOpenProject: () => void;
}

// Practice area configuration - minimalistic black and white
const practiceAreaConfig = {
  legal: {
    icon: Briefcase,
    name: 'Legal'
  },
  accounting: {
    icon: Calculator,
    name: 'Accounting'
  },
  tax: {
    icon: FileText,
    name: 'Tax'
  },
  compliance: {
    icon: Shield,
    name: 'Compliance'
  }
};

// Recent Project Card Component - Minimalistic Design
const ProjectCard: React.FC<{
  project: RecentProject;
  onClick: () => void;
  viewMode: 'grid' | 'list';
}> = ({ project, onClick, viewMode }) => {
  const config = practiceAreaConfig[project.practiceArea];
  const PracticeIcon = config.icon;
  
  const formatLastOpened = (date: Date) => {
    const now = new Date();
    const diffInHours = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60));
    
    if (diffInHours < 1) return 'Just now';
    if (diffInHours < 24) return `${diffInHours}h ago`;
    if (diffInHours < 48) return 'Yesterday';
    return date.toLocaleDateString();
  };

  if (viewMode === 'list') {
    return (
      <Card className="cursor-pointer hover:bg-muted/50 transition-colors" onClick={onClick}>
        <CardContent className="flex items-center p-4">
          <div className="p-2 rounded-md bg-muted mr-3">
            <PracticeIcon className="h-4 w-4" />
          </div>
          
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2">
              <h3 className="font-medium truncate">{project.name}</h3>
            </div>
            <div className="flex items-center space-x-4 text-sm text-muted-foreground mt-1">
              <span>{project.client}</span>
              <span>•</span>
              <span>{formatLastOpened(project.lastOpened)}</span>
              {project.progress && (
                <>
                  <span>•</span>
                  <span>{project.progress.percentage}% complete</span>
                </>
              )}
            </div>
          </div>
          
          <ChevronRight className="h-4 w-4 text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="cursor-pointer hover:shadow-md transition-shadow group" onClick={onClick}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="p-2 rounded-md bg-muted">
            <PracticeIcon className="h-5 w-5" />
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="pt-0">
        <CardTitle className="text-base mb-2 line-clamp-2 group-hover:text-primary">
          {project.name}
        </CardTitle>
        
        <CardDescription className="mb-3 line-clamp-2">
          {project.description}
        </CardDescription>
        
        <div className="flex items-center justify-between text-xs text-muted-foreground mb-3">
          <span>{project.client}</span>
          <span>{formatLastOpened(project.lastOpened)}</span>
        </div>
        
        {project.progress && (
          <div className="mb-3">
            <div className="flex items-center justify-between text-xs mb-1">
              <span>Progress</span>
              <span>{project.progress.percentage}%</span>
            </div>
            <Progress value={project.progress.percentage} className="h-1.5" />
          </div>
        )}
        
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {project.teamMembers.length > 0 && (
              <div className="flex items-center text-xs text-muted-foreground">
                <Users className="h-3 w-3 mr-1" />
                <span>{project.teamMembers.length}</span>
              </div>
            )}
            <Badge variant="outline" className="text-xs">
              {config.name}
            </Badge>
          </div>
          <ArrowRight className="h-4 w-4 text-muted-foreground group-hover:text-primary group-hover:translate-x-1 transition-all" />
        </div>
      </CardContent>
    </Card>
  );
};

// Template Card Component - Minimalistic Design
const TemplateCard: React.FC<{
  template: ProjectTemplate;
  onClick: () => void;
}> = ({ template, onClick }) => {
  const config = practiceAreaConfig[template.practiceArea];
  
  return (
    <Card className="cursor-pointer hover:shadow-md transition-shadow group" onClick={onClick}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="text-2xl">{template.icon}</div>
          <Badge variant="outline" className="text-xs">
            {config.name}
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent className="pt-0">
        <CardTitle className="text-base mb-2 group-hover:text-primary">
          {template.name}
        </CardTitle>
        
        <CardDescription className="mb-3 line-clamp-2">
          {template.description}
        </CardDescription>
        
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>{template.estimatedTime}</span>
          <Badge variant="secondary" className="text-xs capitalize">
            {template.complexity}
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
};

// Main Start Screen Component
const StartScreen: React.FC<StartScreenProps> = ({
  onProjectSelect,
  onNewProject,
  onOpenProject
}) => {
  const [recentProjects] = useState<RecentProject[]>(mockRecentProjects);
  const [filteredProjects, setFilteredProjects] = useState<RecentProject[]>(mockRecentProjects);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPracticeArea, setSelectedPracticeArea] = useState<PracticeArea | 'all'>('all');
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [showTemplates, setShowTemplates] = useState(false);

  // Filter projects based on search and practice area
  useEffect(() => {
    let filtered = recentProjects;

    if (searchQuery) {
      filtered = filtered.filter(project =>
        project.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        project.client.toLowerCase().includes(searchQuery.toLowerCase()) ||
        project.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        project.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
      );
    }

    if (selectedPracticeArea !== 'all') {
      filtered = filtered.filter(project => project.practiceArea === selectedPracticeArea);
    }

    setFilteredProjects(filtered);
  }, [recentProjects, searchQuery, selectedPracticeArea]);

  const handleTemplateSelect = (template: ProjectTemplate) => {
    onNewProject(template);
  };

  const handleQuickStart = () => {
    onNewProject();
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Tabs value={showTemplates ? "templates" : "projects"} onValueChange={(value) => setShowTemplates(value === "templates")}>
                <TabsList>
                  <TabsTrigger value="projects">Recent Projects</TabsTrigger>
                  <TabsTrigger value="templates">Templates</TabsTrigger>
                </TabsList>
              </Tabs>
            </div>
            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-2">
                <Button
                  variant={viewMode === 'grid' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setViewMode('grid')}
                >
                  <Grid3X3 className="h-4 w-4" />
                </Button>
                <Button
                  variant={viewMode === 'list' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setViewMode('list')}
                >
                  <List className="h-4 w-4" />
                </Button>
              </div>
              <Button variant="outline" onClick={onOpenProject}>
                <FolderOpen className="h-4 w-4 mr-2" />
                Open Project
              </Button>
              <Button onClick={handleQuickStart}>
                <Plus className="h-4 w-4 mr-2" />
                New Project
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="w-full">
          {/* Main Content */}
          <div>
            <Tabs value={showTemplates ? "templates" : "projects"} onValueChange={(value) => setShowTemplates(value === "templates")} className="w-full">

              <TabsContent value="projects" className="space-y-6 mt-6">
                {/* Search and Filters */}
                <div className="flex items-center space-x-4">
                  <div className="flex-1 relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                    <Input
                      placeholder="Search projects, clients, or tags..."
                      className="pl-10"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                    />
                  </div>
                  <Select value={selectedPracticeArea} onValueChange={(value) => setSelectedPracticeArea(value as PracticeArea | 'all')}>
                    <SelectTrigger className="w-48">
                      <SelectValue placeholder="Practice Area" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Practice Areas</SelectItem>
                      <SelectItem value="legal">Legal</SelectItem>
                      <SelectItem value="accounting">Accounting</SelectItem>
                      <SelectItem value="tax">Tax</SelectItem>
                      <SelectItem value="compliance">Compliance</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* Projects Grid/List */}
                {filteredProjects.length === 0 ? (
                  <Card className="p-12 text-center">
                    <div className="mx-auto w-16 h-16 bg-muted rounded-full flex items-center justify-center mb-4">
                      <FolderOpen className="h-8 w-8 text-muted-foreground" />
                    </div>
                    <h3 className="text-lg font-medium mb-2">No projects found</h3>
                    <p className="text-muted-foreground mb-4">
                      {searchQuery || selectedPracticeArea !== 'all'
                        ? 'Try adjusting your search or filters'
                        : 'Get started by creating your first project'
                      }
                    </p>
                    <Button onClick={handleQuickStart}>
                      <Plus className="h-4 w-4 mr-2" />
                      Create Project
                    </Button>
                  </Card>
                ) : (
                  <div className={cn(
                    viewMode === 'grid'
                      ? 'grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4'
                      : 'space-y-2'
                  )}>
                    {filteredProjects.map((project) => (
                      <ProjectCard
                        key={project.id}
                        project={project}
                        onClick={() => onProjectSelect(project)}
                        viewMode={viewMode}
                      />
                    ))}
                  </div>
                )}
              </TabsContent>

              <TabsContent value="templates" className="space-y-6 mt-6">
                <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                  {mockProjectTemplates.map((template) => (
                    <TemplateCard
                      key={template.id}
                      template={template}
                      onClick={() => handleTemplateSelect(template)}
                    />
                  ))}
                </div>
              </TabsContent>
            </Tabs>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StartScreen;