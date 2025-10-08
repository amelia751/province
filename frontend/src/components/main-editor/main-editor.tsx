"use client";

import React, { useState, useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import {
  X,
  Circle,
  MoreHorizontal,
  Split,
  Play,
  Bug,
  Terminal,
  Copy,
  Trash2,
  AlertCircle,
  CheckCircle,
  Clock,
  Server
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

interface LogEntry {
  id: string;
  timestamp: Date;
  level: 'info' | 'error' | 'warning' | 'success';
  source: 'frontend' | 'backend' | 'system';
  message: string;
  details?: string;
}

const mockTabs: EditorTab[] = [
  {
    id: "logs",
    name: "Backend Logs",
    path: "system/logs",
    isDirty: false,
    isActive: true
  },
  {
    id: "1",
    name: "sidebar.tsx",
    path: "src/components/ui/sidebar.tsx",
    isDirty: true,
    isActive: false
  },
  {
    id: "2",
    name: "page.tsx",
    path: "src/app/page.tsx",
    isDirty: false,
    isActive: false
  }
];

const MainEditor: React.FC<MainEditorProps> = () => {
  const [tabs, setTabs] = useState(mockTabs);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [autoScroll, setAutoScroll] = useState(true);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const logsContainerRef = useRef<HTMLDivElement>(null);

  // Add initial system logs
  useEffect(() => {
    const initialLogs: LogEntry[] = [
      {
        id: '1',
        timestamp: new Date(),
        level: 'info',
        source: 'system',
        message: 'Frontend started on port 3000',
        details: 'Next.js development server running'
      },
      {
        id: '2',
        timestamp: new Date(Date.now() + 1000),
        level: 'info',
        source: 'system',
        message: 'Starting backend server...',
        details: 'FastAPI server initializing on port 8000'
      }
    ];
    setLogs(initialLogs);
  }, []);

  // Check backend connection status
  useEffect(() => {
    const checkBackend = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/v1/health/', { 
          method: 'GET',
          cache: 'no-cache'
        });
        
        if (response.ok) {
          const data = await response.json();
          addLog('success', 'backend', 'Backend connection established', 
            `Health check passed - Status: ${data.status}, Environment: ${data.environment}`);
        } else {
          throw new Error(`Backend returned ${response.status}`);
        }
      } catch (error) {
        addLog('error', 'backend', 'Backend connection failed', 
          error instanceof Error ? error.message : 'Unknown error');
        
        // Try again in 5 seconds
        setTimeout(checkBackend, 5000);
      }
    };

    // Initial check after a short delay
    const timer = setTimeout(checkBackend, 2000);
    return () => clearTimeout(timer);
  }, []);

  // Listen for fetch errors (like the one you showed)
  useEffect(() => {
    const originalFetch = window.fetch;
    window.fetch = async (...args) => {
      try {
        const response = await originalFetch(...args);
        if (!response.ok) {
          addLog('warning', 'frontend', `HTTP ${response.status}`, 
            `${args[0]} - ${response.statusText}`);
        }
        return response;
      } catch (error) {
        addLog('error', 'frontend', 'Network request failed', 
          `${args[0]} - ${error instanceof Error ? error.message : 'Unknown error'}`);
        throw error;
      }
    };

    return () => {
      window.fetch = originalFetch;
    };
  }, []);

  const addLog = (level: LogEntry['level'], source: LogEntry['source'], message: string, details?: string) => {
    const newLog: LogEntry = {
      id: Date.now().toString(),
      timestamp: new Date(),
      level,
      source,
      message,
      details
    };
    
    setLogs(prevLogs => [...prevLogs, newLog]);
  };

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll]);

  const closeTab = (tabId: string) => {
    if (tabId === 'logs') return; // Don't allow closing logs tab
    setTabs(tabs.filter(tab => tab.id !== tabId));
  };

  const setActiveTab = (tabId: string) => {
    setTabs(tabs.map(tab => ({
      ...tab,
      isActive: tab.id === tabId
    })));
  };

  const clearLogs = () => {
    setLogs([]);
    addLog('info', 'system', 'Logs cleared', 'Log history has been cleared');
  };

  const copyLogs = () => {
    const logText = logs.map(log => 
      `[${log.timestamp.toISOString()}] ${log.level.toUpperCase()} (${log.source}): ${log.message}${log.details ? ` - ${log.details}` : ''}`
    ).join('\n');
    
    navigator.clipboard.writeText(logText).then(() => {
      addLog('success', 'system', 'Logs copied to clipboard', `${logs.length} log entries copied`);
    });
  };

  const getLogIcon = (level: LogEntry['level']) => {
    switch (level) {
      case 'error': return <AlertCircle className="h-4 w-4 text-red-500" />;
      case 'warning': return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      case 'success': return <CheckCircle className="h-4 w-4 text-green-500" />;
      default: return <Clock className="h-4 w-4 text-blue-500" />;
    }
  };

  const getLogColor = (level: LogEntry['level']) => {
    switch (level) {
      case 'error': return 'text-red-700 bg-red-50 border-red-200';
      case 'warning': return 'text-yellow-700 bg-yellow-50 border-yellow-200';
      case 'success': return 'text-green-700 bg-green-50 border-green-200';
      default: return 'text-blue-700 bg-blue-50 border-blue-200';
    }
  };

  const activeTab = tabs.find(tab => tab.isActive);

  return (
    <div className="main-editor-container flex bg-white h-full w-full">
      <div className="flex flex-col h-full flex-1 min-h-0">
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
                  {tab.id === 'logs' && <Terminal className="h-3 w-3 mr-1" />}
                  <span className="text-sm truncate">{tab.name}</span>
                  {tab.isDirty && (
                    <Circle className="h-2 w-2 ml-2 fill-current text-orange-500" />
                  )}
                </div>
                {tab.id !== 'logs' && (
                  <button
                    className="ml-2 p-0.5 hover:bg-gray-200 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                    onClick={(e) => {
                      e.stopPropagation();
                      closeTab(tab.id);
                    }}
                  >
                    <X className="h-3 w-3" />
                  </button>
                )}
              </div>
            ))}
          </div>
          <div className="flex items-center px-2 space-x-1">
            {activeTab?.id === 'logs' && (
              <>
                <button 
                  className="p-1 hover:bg-gray-200 rounded"
                  onClick={copyLogs}
                  title="Copy logs to clipboard"
                >
                  <Copy className="h-4 w-4 text-gray-500" />
                </button>
                <button 
                  className="p-1 hover:bg-gray-200 rounded"
                  onClick={clearLogs}
                  title="Clear logs"
                >
                  <Trash2 className="h-4 w-4 text-gray-500" />
                </button>
              </>
            )}
            <button className="p-1 hover:bg-gray-200 rounded">
              <Split className="h-4 w-4 text-gray-500" />
            </button>
            <button className="p-1 hover:bg-gray-200 rounded">
              <MoreHorizontal className="h-4 w-4 text-gray-500" />
            </button>
          </div>
        </div>

        {/* Editor Content */}
        <div className="flex-1 relative min-h-0">
          {activeTab ? (
            <div className="absolute inset-0 overflow-y-auto">
              {activeTab.id === 'logs' ? (
                // Logs Viewer
                <div className="h-full flex flex-col">
                  {/* Logs Header */}
                  <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gray-50">
                    <div className="flex items-center space-x-2">
                      <Server className="h-5 w-5 text-gray-600" />
                      <h3 className="font-medium text-gray-800">System Logs</h3>
                      <span className="text-sm text-gray-500">({logs.length} entries)</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <label className="flex items-center space-x-2 text-sm text-gray-600">
                        <input
                          type="checkbox"
                          checked={autoScroll}
                          onChange={(e) => setAutoScroll(e.target.checked)}
                          className="rounded"
                        />
                        <span>Auto-scroll</span>
                      </label>
                    </div>
                  </div>

                  {/* Logs Content */}
                  <div 
                    ref={logsContainerRef}
                    className="flex-1 p-4 space-y-2 overflow-y-auto font-mono text-sm"
                  >
                    {logs.length === 0 ? (
                      <div className="text-center text-gray-500 py-8">
                        <Terminal className="h-12 w-12 mx-auto mb-2 text-gray-300" />
                        <p>No logs yet...</p>
                      </div>
                    ) : (
                      logs.map((log) => (
                        <div
                          key={log.id}
                          className={cn(
                            "p-3 rounded-lg border",
                            getLogColor(log.level)
                          )}
                        >
                          <div className="flex items-start space-x-2">
                            {getLogIcon(log.level)}
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center space-x-2 mb-1">
                                <span className="text-xs font-medium uppercase tracking-wider">
                                  {log.source}
                                </span>
                                <span className="text-xs text-gray-500">
                                  {log.timestamp.toLocaleTimeString()}
                                </span>
                              </div>
                              <div className="font-medium mb-1">{log.message}</div>
                              {log.details && (
                                <div className="text-sm opacity-75 break-all">
                                  {log.details}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                    <div ref={logsEndRef} />
                  </div>
                </div>
              ) : (
                // Regular file editor
                <div className="p-4">
                  <div className="bg-gray-50 rounded border border-gray-200 p-4">
                    <div className="text-sm text-gray-500 mb-2">
                      {activeTab.path}
                    </div>
                    <div className="font-mono text-sm text-gray-800 space-y-1">
                      <div className="text-blue-600">{"// Editor content would go here"}</div>
                      <div className="text-green-600">{"import React from 'react';"}</div>
                      <div className="text-purple-600">{"export default function Component() {"}</div>
                      <div className="ml-4 text-gray-800">{"return <div>Hello World</div>;"}</div>
                      <div className="text-purple-600">{"}"}</div>
                    </div>
                  </div>
                </div>
              )}
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
            {activeTab?.id === 'logs' ? (
              <>
                <span>Logs: {logs.length} entries</span>
                <span>Last: {logs[logs.length - 1]?.timestamp.toLocaleTimeString() || 'None'}</span>
              </>
            ) : (
              <>
                <span>Ln 1, Col 1</span>
                <span>UTF-8</span>
                <span>TypeScript React</span>
              </>
            )}
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
