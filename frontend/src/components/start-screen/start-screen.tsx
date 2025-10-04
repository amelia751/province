"use client";

import React, { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import {
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
  ChevronRight,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";

import { RecentProject, ProjectTemplate, PracticeArea } from "./types";
import { mockRecentProjects, mockProjectTemplates } from "./mock-data";

interface StartScreenProps {
  onProjectSelect: (project: RecentProject) => void;
  onNewProject: (template?: ProjectTemplate, prompt?: string) => void;
  onOpenProject: () => void;
}

// Practice area configuration
const practiceAreaConfig = {
  legal: {
    icon: Briefcase,
    name: "Legal",
  },
  accounting: {
    icon: Calculator,
    name: "Accounting",
  },
  tax: {
    icon: FileText,
    name: "Tax",
  },
  compliance: {
    icon: Shield,
    name: "Compliance",
  },
};

// ProjectCard
const ProjectCard: React.FC<{
  project: RecentProject;
  onClick: () => void;
  viewMode: "grid" | "list";
}> = ({ project, onClick, viewMode }) => {
  const config = practiceAreaConfig[project.practiceArea];

  const formatLastOpened = (date: Date) => {
    const now = new Date();
    const diffInHours = Math.floor(
      (now.getTime() - date.getTime()) / (1000 * 60 * 60)
    );

    if (diffInHours < 1) return "Just now";
    if (diffInHours < 24) return `${diffInHours}h ago`;
    if (diffInHours < 48) return "Yesterday";
    return date.toLocaleDateString();
  };

  if (viewMode === "list") {
    return (
      <Card
        className="cursor-pointer hover:bg-muted/50 transition-colors"
        onClick={onClick}
      >
        <CardContent className="flex items-center p-4">
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
    <Card
      className="cursor-pointer hover:shadow-md transition-shadow group"
      onClick={onClick}
    >
      <CardHeader className="pb-3">
        <CardTitle className="text-base line-clamp-2 group-hover:text-primary">
          {project.name}
        </CardTitle>
      </CardHeader>

      <CardContent className="pt-0">
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

// TemplateCard
const TemplateCard: React.FC<{
  template: ProjectTemplate;
  onClick: () => void;
}> = ({ template, onClick }) => {
  const config = practiceAreaConfig[template.practiceArea];

  return (
    <Card
      className="cursor-pointer hover:shadow-md transition-shadow group"
      onClick={onClick}
    >
      <CardHeader className="pb-3">
        <CardTitle className="text-base line-clamp-2 group-hover:text-primary">
          {template.name}
        </CardTitle>
      </CardHeader>

      <CardContent className="pt-0">
        <CardDescription className="mb-3 line-clamp-2">
          {template.description}
        </CardDescription>

        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">{template.estimatedTime}</span>
          <Badge variant="outline" className="text-xs">
            {config.name}
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
};

// Main StartScreen
const StartScreen: React.FC<StartScreenProps> = ({
  onProjectSelect,
  onNewProject,
  onOpenProject,
}) => {
  const [recentProjects] = useState<RecentProject[]>(mockRecentProjects);
  const [filteredProjects, setFilteredProjects] =
    useState<RecentProject[]>(mockRecentProjects);
  const [templates] = useState<ProjectTemplate[]>(mockProjectTemplates);
  const [filteredTemplates, setFilteredTemplates] =
    useState<ProjectTemplate[]>(mockProjectTemplates);
  const [searchQuery, setSearchQuery] = useState("");
  const [templateSearchQuery, setTemplateSearchQuery] = useState("");
  const [selectedPracticeArea, setSelectedPracticeArea] = useState<
    PracticeArea | "all"
  >("all");
  const [selectedTemplatePracticeArea, setSelectedTemplatePracticeArea] = useState<
    PracticeArea | "all"
  >("all");
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [activeTab, setActiveTab] = useState<"projects" | "templates">("projects");

  useEffect(() => {
    let filtered = recentProjects;

    if (searchQuery) {
      filtered = filtered.filter(
        (project) =>
          project.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
          project.client.toLowerCase().includes(searchQuery.toLowerCase()) ||
          project.description
            .toLowerCase()
            .includes(searchQuery.toLowerCase()) ||
          project.tags.some((tag) =>
            tag.toLowerCase().includes(searchQuery.toLowerCase())
          )
      );
    }

    if (selectedPracticeArea !== "all") {
      filtered = filtered.filter(
        (project) => project.practiceArea === selectedPracticeArea
      );
    }

    setFilteredProjects(filtered);
  }, [recentProjects, searchQuery, selectedPracticeArea]);

  useEffect(() => {
    let filtered = templates;

    if (templateSearchQuery) {
      filtered = filtered.filter(
        (template) =>
          template.name.toLowerCase().includes(templateSearchQuery.toLowerCase()) ||
          template.description.toLowerCase().includes(templateSearchQuery.toLowerCase())
      );
    }

    if (selectedTemplatePracticeArea !== "all") {
      filtered = filtered.filter(
        (template) => template.practiceArea === selectedTemplatePracticeArea
      );
    }

    setFilteredTemplates(filtered);
  }, [templates, templateSearchQuery, selectedTemplatePracticeArea]);

  const handleTemplateSelect = (template: ProjectTemplate) => {
    onNewProject(template);
  };

  const handleQuickStart = () => {
    onNewProject();
  };

  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto px-6">
        <Tabs value={activeTab} onValueChange={(value) => setActiveTab(value as "projects" | "templates")} className="w-full">
          {/* Header */}
          <div className="border-b">
            <div className="py-4">
              <div className="flex items-center justify-between">
                <TabsList className="bg-white rounded-lg gap-1 p-1">
                  <TabsTrigger
                    value="projects"
                    className={cn(
                      "text-base font-light rounded-md px-4 py-2 transition-all duration-200 ease-in-out",
                      activeTab === "projects"
                        ? "bg-black text-white shadow-md"
                        : "bg-white text-black hover:bg-gray-100 hover:shadow-sm hover:scale-[1.02]"
                    )}
                  >
                    Recent Projects
                  </TabsTrigger>
                  <TabsTrigger
                    value="templates"
                    className={cn(
                      "text-base font-light rounded-md px-4 py-2 transition-all duration-200 ease-in-out",
                      activeTab === "templates"
                        ? "bg-black text-white shadow-md"
                        : "bg-white text-black hover:bg-gray-100 hover:shadow-sm hover:scale-[1.02]"
                    )}
                  >
                    Templates
                  </TabsTrigger>
                </TabsList>
                <div className="flex items-center space-x-3">
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

          {/* Projects Tab */}
          <TabsContent value="projects" className="py-8">
            <div className="space-y-6">
              {/* Search + Filters */}
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-4 flex-1">
                  <div className="flex-1">
                    <Input
                      placeholder="Search projects, clients, or tags..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      />
                  </div>
                  <Select
                    value={selectedPracticeArea}
                    onValueChange={(value) =>
                      setSelectedPracticeArea(value as PracticeArea | "all")
                    }
                  >
                    <SelectTrigger className="w-48 mr-4">
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
                <div className="flex items-center space-x-2">
                  <Button
                    variant={viewMode === "grid" ? "default" : "ghost"}
                    size="sm"
                    onClick={() => setViewMode("grid")}
                  >
                    <Grid3X3 className="h-4 w-4" />
                  </Button>
                  <Button
                    variant={viewMode === "list" ? "default" : "ghost"}
                    size="sm"
                    onClick={() => setViewMode("list")}
                  >
                    <List className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              {/* Projects Grid/List - Scrollable */}
              {filteredProjects.length === 0 ? (
                <Card className="p-12 text-center">
                  <div className="mx-auto w-16 h-16 bg-muted rounded-full flex items-center justify-center mb-4">
                    <FolderOpen className="h-8 w-8 text-muted-foreground" />
                  </div>
                  <h3 className="text-lg font-medium mb-2">No projects found</h3>
                  <p className="text-muted-foreground mb-4">
                    {searchQuery || selectedPracticeArea !== "all"
                      ? "Try adjusting your search or filters"
                      : "Get started by creating your first project"}
                  </p>
                  <Button onClick={handleQuickStart}>
                    <Plus className="h-4 w-4 mr-2" />
                    Create Project
                  </Button>
                </Card>
              ) : (
                <ScrollArea className="h-[66vh] pr-4">
                  <div
                    className={cn(
                      viewMode === "grid"
                        ? "grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 pb-4"
                        : "space-y-2 pb-4"
                    )}
                  >
                    {filteredProjects.map((project) => (
                      <ProjectCard
                        key={project.id}
                        project={project}
                        onClick={() => onProjectSelect(project)}
                        viewMode={viewMode}
                      />
                    ))}
                  </div>
                </ScrollArea>
              )}
            </div>
          </TabsContent>

          {/* Templates Tab */}
          <TabsContent value="templates" className="py-8">
            <div className="space-y-6">
              {/* Search + Filters */}
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-4 flex-1">
                  <div className="flex-1">
                    <Input
                      placeholder="Search templates..."
                      value={templateSearchQuery}
                      onChange={(e) => setTemplateSearchQuery(e.target.value)}
                    />
                  </div>
                  <Select
                    value={selectedTemplatePracticeArea}
                    onValueChange={(value) =>
                      setSelectedTemplatePracticeArea(value as PracticeArea | "all")
                    }
                  >
                    <SelectTrigger className="w-48 mr-4">
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
              </div>

              {/* Templates Grid - Scrollable */}
              <ScrollArea className="h-[66vh] pr-4">
                <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4 pb-4">
                  {filteredTemplates.map((template) => (
                    <TemplateCard
                      key={template.id}
                      template={template}
                      onClick={() => handleTemplateSelect(template)}
                    />
                  ))}
                </div>
              </ScrollArea>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default StartScreen;
