"use client";

import { useState, useCallback, useEffect } from 'react';
import { cn } from '@/lib/utils';
import Sidebar from '@/components/ui/sidebar';
import Header from '@/components/interface/header';
import ExplorerPanel from '@/components/explorer-panel/explorer-panel';
import MainEditor from '@/components/main-editor/main-editor';
import Chat from '@/components/chat/chat';
import { mockAIMatters } from '@/components/explorer-panel/mock-data';

interface InterfaceLayoutProps {
  organizationName?: string | null;
  projectId?: string;
  debugInfo?: any;
}

// Explorer Resize Handle Component
interface ExplorerResizeHandleProps {
  onResize: (width: number) => void;
}

function ExplorerResizeHandle({ onResize }: ExplorerResizeHandleProps) {
  const [isResizing, setIsResizing] = useState(false);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;

      const sidebarWidth = 64; // Fixed sidebar width
      const newWidth = e.clientX - sidebarWidth;
      onResize(newWidth);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };

    if (isResizing) {
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing, onResize]);

  const handleResizeStart = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  };

  return (
    <div
      className="absolute top-0 right-0 w-3 h-full cursor-col-resize group z-50 flex items-center justify-center hover:bg-gray-100/50"
      onMouseDown={handleResizeStart}
    />
  );
}

// Main Editor Left Resize Handle Component (for expanding into explorer)
interface MainEditorLeftResizeHandleProps {
  onResize: (explorerWidth: number) => void;
}

function MainEditorLeftResizeHandle({ onResize }: MainEditorLeftResizeHandleProps) {
  const [isResizing, setIsResizing] = useState(false);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;

      const sidebarWidth = 64; // Fixed sidebar width
      const newExplorerWidth = e.clientX - sidebarWidth;
      onResize(newExplorerWidth);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };

    if (isResizing) {
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing, onResize]);

  const handleResizeStart = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  };

  return (
    <div
      className="absolute top-0 left-0 w-3 h-full cursor-col-resize group z-50 flex items-center justify-center hover:bg-gray-100/50"
      onMouseDown={handleResizeStart}
    />
  );
}

// Main Editor Right Resize Handle Component (for expanding into chat)
interface MainEditorRightResizeHandleProps {
  onResize: (chatWidth: number) => void;
}

function MainEditorRightResizeHandle({ onResize }: MainEditorRightResizeHandleProps) {
  const [isResizing, setIsResizing] = useState(false);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;

      const newChatWidth = window.innerWidth - e.clientX;
      onResize(newChatWidth);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };

    if (isResizing) {
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing, onResize]);

  const handleResizeStart = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  };

  return (
    <div
      className="absolute top-0 right-0 w-3 h-full cursor-col-resize group z-50 flex items-center justify-center hover:bg-gray-100/50"
      onMouseDown={handleResizeStart}
    />
  );
}

// Chat Resize Handle Component
interface ChatResizeHandleProps {
  onResize: (width: number) => void;
}

function ChatResizeHandle({ onResize }: ChatResizeHandleProps) {
  const [isResizing, setIsResizing] = useState(false);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;

      const newWidth = window.innerWidth - e.clientX;
      onResize(newWidth);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };

    if (isResizing) {
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing, onResize]);

  const handleResizeStart = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  };

  return (
    <div
      className="absolute top-0 left-0 w-3 h-full cursor-col-resize group z-50 flex items-center justify-center hover:bg-gray-100/50"
      onMouseDown={handleResizeStart}
    />
  );
}

export default function InterfaceLayout({ organizationName, projectId, debugInfo }: InterfaceLayoutProps) {
  const [sidebarWidth, setSidebarWidth] = useState(64);
  const [explorerWidth, setExplorerWidth] = useState(280);
  const [chatWidth, setChatWidth] = useState(400);
  // Use first mock matter as selected project, but override the ID with the real project ID
  const [selectedProject] = useState(() => {
    const mockProject = mockAIMatters[0];
    return projectId ? { ...mockProject, id: projectId } : mockProject;
  });
  // Selected document state
  const [selectedDocument, setSelectedDocument] = useState<{
    id: string;
    name: string;
    type: string;
    url?: string;
    path: string;
  } | null>(null);

  // Handle document selection
  const handleDocumentSelect = useCallback((document: any, matterId: string) => {
    setSelectedDocument({
      id: document.id,
      name: document.name,
      type: document.type,
      url: document.url,
      path: document.path
    });
  }, []);

  // Calculate available space for panels
  const getAvailableWidth = () => {
    return window.innerWidth - sidebarWidth;
  };

  // Handle explorer panel resizing
  const handleExplorerWidthChange = useCallback((newExplorerWidth: number) => {
    const availableWidth = getAvailableWidth();
    const maxAllowed = Math.floor(availableWidth * (2 / 3));
    const minWidth = 200;
    const minMainEditor = 400;
    const minChatWidth = 300;
    const defaultChatWidth = 400;

    // If dragging to very small width (< minWidth), hide explorer completely
    if (newExplorerWidth < minWidth) {
      setExplorerWidth(0);
      // If chat is hidden, restore it to default width
      if (chatWidth === 0) {
        const spaceForChat = availableWidth - minMainEditor;
        if (spaceForChat >= minChatWidth) {
          setChatWidth(Math.min(defaultChatWidth, spaceForChat));
        }
      }
      return;
    }

    // Constrain explorer width
    let constrainedWidth = Math.max(minWidth, Math.min(newExplorerWidth, maxAllowed));

    // If explorer would take 2/3 or more, hide chat completely
    if (constrainedWidth >= maxAllowed) {
      setExplorerWidth(maxAllowed);
      setChatWidth(0);
      return;
    }

    // Calculate space left for main editor + chat
    const remainingSpace = availableWidth - constrainedWidth;
    const spaceForChat = remainingSpace - minMainEditor;

    // Always try to show chat if there's enough space
    if (spaceForChat >= minChatWidth) {
      setExplorerWidth(constrainedWidth);
      // If chat is currently hidden, restore it to default width or available space
      if (chatWidth === 0) {
        setChatWidth(Math.min(defaultChatWidth, spaceForChat));
      } else {
        // Chat is visible, maintain its current width if possible
        setChatWidth(Math.min(chatWidth, spaceForChat));
      }
    } else {
      // Not enough space for chat, hide it
      setExplorerWidth(constrainedWidth);
      setChatWidth(0);
    }
  }, [sidebarWidth, chatWidth]);

  // Handle chat panel resizing
  const handleChatWidthChange = useCallback((newChatWidth: number) => {
    const availableWidth = getAvailableWidth();
    const maxAllowed = Math.floor(availableWidth * (2 / 3));
    const minWidth = 300;
    const minMainEditor = 400;
    const minExplorerWidth = 200;
    const defaultExplorerWidth = 280;

    // If dragging to very small width (< minWidth), hide chat completely
    if (newChatWidth < minWidth) {
      setChatWidth(0);
      // If explorer is hidden, restore it to default width
      if (explorerWidth === 0) {
        const spaceForExplorer = availableWidth - minMainEditor;
        if (spaceForExplorer >= minExplorerWidth) {
          setExplorerWidth(Math.min(defaultExplorerWidth, spaceForExplorer));
        }
      }
      return;
    }

    // Constrain chat width
    let constrainedWidth = Math.max(minWidth, Math.min(newChatWidth, maxAllowed));

    // If chat would take 2/3 or more, hide explorer completely
    if (constrainedWidth >= maxAllowed) {
      setChatWidth(maxAllowed);
      setExplorerWidth(0);
      return;
    }

    // Calculate space left for main editor + explorer
    const remainingSpace = availableWidth - constrainedWidth;
    const spaceForExplorer = remainingSpace - minMainEditor;

    // Always try to show explorer if there's enough space
    if (spaceForExplorer >= minExplorerWidth) {
      setChatWidth(constrainedWidth);
      // If explorer is currently hidden, restore it to default width or available space
      if (explorerWidth === 0) {
        setExplorerWidth(Math.min(defaultExplorerWidth, spaceForExplorer));
      } else {
        // Explorer is visible, maintain its current width if possible
        setExplorerWidth(Math.min(explorerWidth, spaceForExplorer));
      }
    } else {
      // Not enough space for explorer, hide it
      setChatWidth(constrainedWidth);
      setExplorerWidth(0);
    }
  }, [sidebarWidth, explorerWidth]);

  // Handle sidebar width change
  const handleSidebarWidthChange = useCallback((width: number) => {
    setSidebarWidth(width);
  }, []);

  // Toggle explorer panel
  const handleToggleExplorer = useCallback(() => {
    if (explorerWidth === 0) {
      // Show explorer with default width
      setExplorerWidth(280);
      // If there's not enough space, hide chat
      const availableWidth = getAvailableWidth();
      if (280 + 400 + 400 > availableWidth) {
        setChatWidth(0);
      }
    } else {
      // Hide explorer
      setExplorerWidth(0);
    }
  }, [explorerWidth, chatWidth]);

  // Toggle chat panel
  const handleToggleChat = useCallback(() => {
    if (chatWidth === 0) {
      // Show chat with default width
      setChatWidth(400);
      // If there's not enough space, hide explorer
      const availableWidth = getAvailableWidth();
      if (280 + 400 + 400 > availableWidth) {
        setExplorerWidth(0);
      }
    } else {
      // Hide chat
      setChatWidth(0);
    }
  }, [explorerWidth, chatWidth]);

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <Header
        onToggleExplorer={handleToggleExplorer}
        onToggleChat={handleToggleChat}
      />

      {/* Main Content Area - Flex container for the three panels */}
      <div className="flex flex-1 h-full relative min-h-0 overflow-hidden">
        {/* Explorer Panel - only render if width > 0 */}
        {explorerWidth > 0 && (
          <div
            className="flex-shrink-0 relative h-full border-r border-gray-200"
            style={{ width: `${explorerWidth}px` }}
          >
            <ExplorerPanel
              selectedProject={selectedProject}
              onDocumentSelect={handleDocumentSelect}
            />
            {/* Explorer Resize Handle */}
            <ExplorerResizeHandle onResize={handleExplorerWidthChange} />
          </div>
        )}

        {/* Main Editor Area - Takes remaining space */}
        <div className={cn(
          "flex-1 min-w-0 relative h-full",
          chatWidth === 0 && "border-r-0"
        )}>
          <MainEditor selectedDocument={selectedDocument} debugInfo={debugInfo} />
          {/* Main Editor Left Resize Handle - only show if explorer is visible */}
          {explorerWidth > 0 && (
            <MainEditorLeftResizeHandle onResize={handleExplorerWidthChange} />
          )}
          {/* Main Editor Right Resize Handle - only show if chat is visible */}
          {chatWidth > 0 && (
            <MainEditorRightResizeHandle onResize={handleChatWidthChange} />
          )}
        </div>

        {/* Chat Panel - only render if width > 0 */}
        {chatWidth > 0 && (
          <div
            className="flex-shrink-0 relative h-full"
            style={{ width: `${chatWidth}px` }}
          >
            {/* Chat Resize Handle */}
            <ChatResizeHandle onResize={handleChatWidthChange} />
            <Chat engagementId={projectId} />
          </div>
        )}
      </div>
    </div>
  );
}