"use client";

import { useRouter } from 'next/navigation';
import StartScreen from '@/components/start-screen/start-screen';
import { RecentProject, ProjectTemplate } from '@/components/start-screen/types';

export default function StartScreenClient() {
  const router = useRouter();

  const handleProjectSelect = (project: RecentProject) => {
    // Navigate to the project page
    router.push(`/app/project/${project.id}`);
  };

  const handleNewProject = (template?: ProjectTemplate, prompt?: string) => {
    // Create a new project ID
    const newProjectId = `project-${Date.now()}`;
    
    // TODO: Here you would typically:
    // 1. Call an API to create the project in the database
    // 2. Store the template and prompt if provided
    // 3. Then navigate to the new project
    
    console.log('Creating new project:', { template, prompt });
    
    // Navigate to the new project page
    router.push(`/app/project/${newProjectId}`);
  };

  const handleOpenProject = () => {
    // Here you would typically open a file dialog
    console.log('Opening project from computer...');
    // For demo purposes, we'll just log this
    alert('File dialog would open here to select a project folder');
  };

  return (
    <StartScreen
      onProjectSelect={handleProjectSelect}
      onNewProject={handleNewProject}
      onOpenProject={handleOpenProject}
    />
  );
}

