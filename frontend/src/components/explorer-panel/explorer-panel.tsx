"use client";

import React, { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import {
  Folder,
  File,
  ChevronRight,
  ChevronDown,
  Search,
  MoreHorizontal,
  Plus,
  FolderPlus,
  FilePlus
} from "lucide-react";

interface ExplorerPanelProps {
  onWidthChange?: (width: number) => void;
}

interface FileTreeItem {
  name: string;
  type: 'file' | 'folder';
  children?: FileTreeItem[];
  expanded?: boolean;
}

const mockFileTree: FileTreeItem[] = [
  {
    name: "src",
    type: "folder",
    expanded: true,
    children: [
      {
        name: "components",
        type: "folder",
        expanded: true,
        children: [
          { name: "ui", type: "folder", children: [
            { name: "sidebar.tsx", type: "file" },
            { name: "button.tsx", type: "file" }
          ]},
          { name: "dashboard", type: "folder", children: [
            { name: "dashboard-layout.tsx", type: "file" }
          ]}
        ]
      },
      {
        name: "app",
        type: "folder",
        children: [
          { name: "page.tsx", type: "file" },
          { name: "layout.tsx", type: "file" }
        ]
      }
    ]
  },
  { name: "package.json", type: "file" },
  { name: "README.md", type: "file" }
];

const FileTreeNode: React.FC<{ item: FileTreeItem; depth: number }> = ({ item, depth }) => {
  const [isExpanded, setIsExpanded] = useState(item.expanded || false);

  const handleToggle = () => {
    if (item.type === 'folder') {
      setIsExpanded(!isExpanded);
    }
  };

  return (
    <div>
      <div
        className={cn(
          "flex items-center py-1 px-2 hover:bg-gray-50 cursor-pointer text-sm",
          "text-gray-700 hover:text-black"
        )}
        style={{ paddingLeft: `${depth * 12 + 8}px` }}
        onClick={handleToggle}
      >
        {item.type === 'folder' && (
          <div className="w-4 h-4 flex items-center justify-center mr-1">
            {isExpanded ? (
              <ChevronDown className="h-3 w-3" />
            ) : (
              <ChevronRight className="h-3 w-3" />
            )}
          </div>
        )}
        {item.type === 'folder' ? (
          <Folder className="h-4 w-4 mr-2 text-blue-500" />
        ) : (
          <File className="h-4 w-4 mr-2 text-gray-500" />
        )}
        <span className="truncate">{item.name}</span>
      </div>
      {item.type === 'folder' && isExpanded && item.children && (
        <div>
          {item.children.map((child, index) => (
            <FileTreeNode key={index} item={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  );
};

const ExplorerPanel: React.FC<ExplorerPanelProps> = ({ onWidthChange }) => {



  return (
    <div className="explorer-panel-container flex bg-white h-full w-full"
    >
      <div className="flex flex-col h-full flex-1">
        {/* Header */}
        <div className="flex items-center justify-between p-3 border-b border-gray-100">
          <h3 className="text-sm font-medium text-gray-900">Explorer</h3>
          <div className="flex items-center space-x-1">
            <button className="p-1 hover:bg-gray-100 rounded">
              <Plus className="h-4 w-4 text-gray-500" />
            </button>
            <button className="p-1 hover:bg-gray-100 rounded">
              <FolderPlus className="h-4 w-4 text-gray-500" />
            </button>
            <button className="p-1 hover:bg-gray-100 rounded">
              <Search className="h-4 w-4 text-gray-500" />
            </button>
            <button className="p-1 hover:bg-gray-100 rounded">
              <MoreHorizontal className="h-4 w-4 text-gray-500" />
            </button>
          </div>
        </div>

        {/* File Tree */}
        <div className="flex-1 overflow-y-auto">
          <div className="py-2">
            {mockFileTree.map((item, index) => (
              <FileTreeNode key={index} item={item} depth={0} />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExplorerPanel;