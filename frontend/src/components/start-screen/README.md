# Province Cursor Start Screen

The Start Screen component provides a Cursor IDE-style project selection interface for Province Cursor. It follows the familiar pattern of showing recent projects first, then transitioning to the project explorer when a project is selected.

## Features

### 🎯 **Cursor-Style Workflow**
- **Start Screen**: Shows recent projects and templates (like Cursor's project list)
- **Project Selection**: Click a project to enter the three-panel IDE view
- **Quick Actions**: New project, open project, browse templates

### 📁 **Recent Projects**
- **Smart Display**: Shows recent projects with practice area icons
- **Progress Tracking**: Visual progress bars and completion percentages
- **Search & Filter**: Find projects by name, client, or practice area
- **Multiple Views**: Grid and list view modes

### 🚀 **Project Creation**
- **AI Templates**: Pre-built templates for common workflows
- **Quick Start**: Create new projects with AI assistance
- **File System**: Open existing projects from computer

### 💼 **Practice Area Support**
- **Legal**: Briefcase icon, blue theme
- **Accounting**: Calculator icon, green theme  
- **Tax**: FileText icon, purple theme
- **Compliance**: Shield icon, red theme

## Usage

### Basic Implementation

```tsx
import { StartScreen } from '@/components/start-screen';

function App() {
  const handleProjectSelect = (project) => {
    // Navigate to project explorer
    setCurrentView('project');
    setSelectedProject(project);
  };

  const handleNewProject = (template, prompt) => {
    // Create new project with AI
    createProject(template, prompt);
  };

  const handleOpenProject = () => {
    // Open file dialog
    openFileDialog();
  };

  return (
    <StartScreen
      onProjectSelect={handleProjectSelect}
      onNewProject={handleNewProject}
      onOpenProject={handleOpenProject}
    />
  );
}
```

### Full App Integration

```tsx
import { ProvinceCursorApp } from '@/components/ui/province-cursor-app';

function MyApp() {
  return (
    <ProvinceCursorApp organizationName="My Law Firm" />
  );
}
```

## Components

### StartScreen
Main component that renders the project selection interface.

**Props:**
- `onProjectSelect`: Called when user selects a project
- `onNewProject`: Called when user creates a new project
- `onOpenProject`: Called when user wants to open from file system

### ProjectCard
Displays individual project information in grid or list format.

### TemplateCard
Shows available project templates for quick creation.

## Mock Data

The component includes comprehensive mock data:

- **6 Sample Projects**: Across all practice areas with realistic data
- **6 Project Templates**: Common workflows for each practice area
- **Progress Tracking**: Completion percentages and task counts
- **Team Members**: Assigned users and collaborators

## Integration with Explorer Panel

The start screen seamlessly integrates with the enhanced explorer panel:

1. **Project Selection**: Converts `RecentProject` to `AIMatter` format
2. **State Management**: Manages transition between start and project views
3. **Context Preservation**: Maintains project context across components

## Styling

Uses Tailwind CSS with:
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Practice Area Colors**: Consistent color coding across components
- **Hover Effects**: Smooth transitions and interactive feedback
- **Grid/List Views**: Flexible display options

## Future Enhancements

- **Real-time Updates**: Live project status updates
- **Collaboration**: Show active team members
- **Recent Activity**: Timeline of recent changes
- **Favorites**: Pin frequently used projects
- **Advanced Search**: Full-text search across project content

The Start Screen provides the familiar Cursor IDE experience while adding professional services intelligence and AI-powered project creation capabilities.