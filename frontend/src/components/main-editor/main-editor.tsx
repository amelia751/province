"use client";

import React, { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import {
  X,
  Circle,
  MoreHorizontal,
  Split,
  Settings,
  Search,
  Play,
  Bug
} from "lucide-react";

interface MainEditorProps {
  onWidthChange?: (width: number) => void;
}

interface EditorTab {
  id: string;
  name: string;
  path: string;
  isDirty: boolean;
  isActive: boolean;
}

const mockTabs: EditorTab[] = [
  {
    id: "1",
    name: "sidebar.tsx",
    path: "src/components/ui/sidebar.tsx",
    isDirty: true,
    isActive: true
  },
  {
    id: "2",
    name: "page.tsx",
    path: "src/app/page.tsx",
    isDirty: false,
    isActive: false
  },
  {
    id: "3",
    name: "layout.tsx",
    path: "src/app/layout.tsx",
    isDirty: false,
    isActive: false
  }
];

const MainEditor: React.FC<MainEditorProps> = ({ onWidthChange }) => {
  const [tabs, setTabs] = useState(mockTabs);



  const closeTab = (tabId: string) => {
    setTabs(tabs.filter(tab => tab.id !== tabId));
  };

  const setActiveTab = (tabId: string) => {
    setTabs(tabs.map(tab => ({
      ...tab,
      isActive: tab.id === tabId
    })));
  };



  return (
    <div
      className="main-editor-container flex bg-white h-full w-full"
    >
      <div className="flex flex-col h-full flex-1">
        {/* Tab Bar */}
        <div className="flex items-center border-b border-gray-100 bg-gray-50">
          <div className="flex flex-1 overflow-x-auto">
            {tabs.map((tab) => (
              <div
                key={tab.id}
                className={cn(
                  "flex items-center px-3 py-2 border-r border-gray-200 cursor-pointer group min-w-0",
                  tab.isActive 
                    ? "bg-white text-black" 
                    : "bg-gray-50 text-gray-600 hover:bg-gray-100"
                )}
                onClick={() => setActiveTab(tab.id)}
              >
                <div className="flex items-center min-w-0 flex-1">
                  <span className="text-sm truncate">{tab.name}</span>
                  {tab.isDirty && (
                    <Circle className="h-2 w-2 ml-2 fill-current text-orange-500" />
                  )}
                </div>
                <button
                  className="ml-2 p-0.5 hover:bg-gray-200 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                  onClick={(e) => {
                    e.stopPropagation();
                    closeTab(tab.id);
                  }}
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            ))}
          </div>
          <div className="flex items-center px-2 space-x-1">
            <button className="p-1 hover:bg-gray-200 rounded">
              <Split className="h-4 w-4 text-gray-500" />
            </button>
            <button className="p-1 hover:bg-gray-200 rounded">
              <MoreHorizontal className="h-4 w-4 text-gray-500" />
            </button>
          </div>
        </div>

        {/* Editor Content */}
        <div className="flex-1 relative">
          {tabs.find(tab => tab.isActive) ? (
            <div className="h-full p-4">
              <div className="h-full bg-gray-50 rounded border border-gray-200 p-4">
                <div className="text-sm text-gray-500 mb-2">
                  {tabs.find(tab => tab.isActive)?.path}
                </div>
                <div className="font-mono text-sm text-gray-800">
                  <div className="text-blue-600">{"// Editor content would go here"}</div>
                  <div className="text-green-600">{"import React from 'react';"}</div>
                  <div className="text-purple-600">{"export default function Component() {"}</div>
                  <div className="ml-4 text-gray-800">{"return <div>Hello World</div>;"}</div>
                  <div className="text-purple-600">{"}"}</div>
                </div>
              </div>
            </div>
          ) : (
            <div className="h-full flex items-center justify-center text-gray-500">
              <div className="text-center">
                <div className="text-lg mb-2">No file open</div>
                <div className="text-sm">Select a file from the explorer to start editing</div>
              </div>
            </div>
          )}
        </div>

        {/* Status Bar */}
        <div className="flex items-center justify-between px-4 py-1 bg-gray-50 border-t border-gray-100 text-xs text-gray-600">
          <div className="flex items-center space-x-4">
            <span>Ln 1, Col 1</span>
            <span>UTF-8</span>
            <span>TypeScript React</span>
          </div>
          <div className="flex items-center space-x-2">
            <button className="flex items-center space-x-1 hover:text-black">
              <Play className="h-3 w-3" />
              <span>Run</span>
            </button>
            <button className="flex items-center space-x-1 hover:text-black">
              <Bug className="h-3 w-3" />
              <span>Debug</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MainEditor;