"use client";

import React, { useState, useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
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
  Server,
  File
} from "lucide-react";

interface MainEditorProps {
  onWidthChange?: (width: number) => void;
  selectedDocument?: {
    id: string;
    name: string;
    type: string;
    url?: string;
    path: string;
  } | null;
}

interface EditorTab {
  id: string;
  name: string;
  path: string;
  isDirty: boolean;
  isActive: boolean;
  type?: string;
  url?: string;
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
    id: "ingest-w2",
    name: "Ingest W-2",
    path: "tools/ingest-w2",
    isDirty: false,
    isActive: false,
    type: "ingest-tool"
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

const MainEditor: React.FC<MainEditorProps> = ({ onWidthChange, selectedDocument }) => {
  const [tabs, setTabs] = useState(mockTabs);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [autoScroll, setAutoScroll] = useState(true);
  const [isHoveringTabArea, setIsHoveringTabArea] = useState(false);
  const [selectedW2File, setSelectedW2File] = useState<string>('');
  const [ocrResult, setOcrResult] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState(false);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const logsContainerRef = useRef<HTMLDivElement>(null);

  // Available W2 files for testing
  const w2Files = [
    {
      name: 'W2_XL_input_clean_1000.pdf',
      url: 'https://province-documents-[REDACTED-ACCOUNT-ID]-us-east-2.s3.us-east-2.amazonaws.com/datasets/w2-forms/W2_Clean_DataSet_01_20Sep2019/W2_XL_input_clean_1000.pdf',
      type: 'pdf'
    },
    {
      name: 'W2_XL_input_clean_1000.jpg',
      url: 'https://province-documents-[REDACTED-ACCOUNT-ID]-us-east-2.s3.us-east-2.amazonaws.com/datasets/w2-forms/W2_Clean_DataSet_01_20Sep2019/W2_XL_input_clean_1000.jpg',
      type: 'image'
    }
  ];

  // Mock Tesseract processing function
  const processWithTesseract = async (fileUrl: string, fileName: string) => {
    setIsProcessing(true);
    setOcrResult('Processing...');
    
    try {
      // Simulate API call to backend Tesseract service
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Mock OCR result based on our terminal testing
      const mockResult = `=== Tesseract OCR Results for ${fileName} ===

REISSUED Employee's social security number
STATEMENT 077-49-4905 OMB No. 1645-0008

b Employer identification number
37-2766773

c Employer's name, address, and ZIP code
Richardson-Brown PLC
2936 Howard Radial
West Raymond NV 44735-6958

d Control number
4741345

e Employee's first name and initial Last name
April Hensley

f Employee's address and ZIP code
31403 David Circles Suite 863
West Erinfort WY 45881-3334

1 Wages, tips, other compensation: 55151.93
2 Federal income tax withheld: 16606.17
3 Social security wages: 67588.01
4 Social security tax withheld: 5170.48
5 Medicare wages and tips: 50518.06
6 Medicare tax withheld: 1465.02
7 Social security tips: 67588.01
8 Allocated tips: 50518.06
9 Advance EIC payment: 238
10 Dependent care benefits: 
11 Nonqualified plans: 210
12a See instructions for box 12: G 8500
13 Statutory employee: 
14 Other: D 999, G 381
15 State: DC
16 State wages, tips, etc: 28287.19
17 State income tax: 1608.75
18 Local wages, tips, etc: 44590.58
19 Local income tax: 6842.08
20 Locality name: Rocha Wells

=== Processing Complete ===`;
      
      setOcrResult(mockResult);
    } catch (error) {
      setOcrResult(`Error processing file: ${error}`);
    } finally {
      setIsProcessing(false);
    }
  };

  // Handle document selection
  useEffect(() => {
    if (selectedDocument) {
      setTabs(prevTabs => {
        // Check if document tab already exists
        const existingTab = prevTabs.find(tab => tab.id === selectedDocument.id);
        
        if (!existingTab) {
          // Create new tab for the document
          const newTab: EditorTab = {
            id: selectedDocument.id,
            name: selectedDocument.name,
            path: selectedDocument.path,
            isDirty: false,
            isActive: true,
            type: selectedDocument.type,
            url: selectedDocument.url
          };
          
          // Add new tab and make it active
          return [
            ...prevTabs.map(tab => ({ ...tab, isActive: false })),
            newTab
          ];
        } else {
          // Make existing tab active only if it's not already active
          if (!existingTab.isActive) {
            return prevTabs.map(tab => ({
              ...tab,
              isActive: tab.id === selectedDocument.id
            }));
          }
          // Return unchanged if already active
          return prevTabs;
        }
      });
    }
  }, [selectedDocument]);

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
        {/* Invisible hover area above tabs */}
        <div 
          className="absolute top-0 left-0 right-0 h-2 z-20"
          onMouseEnter={() => setIsHoveringTabArea(true)}
          onMouseLeave={() => setIsHoveringTabArea(false)}
        />
        {/* Tab Bar */}
        <div 
          className="flex items-center border-b border-gray-100 bg-gray-50 relative z-10"
          onMouseEnter={() => setIsHoveringTabArea(true)}
          onMouseLeave={() => setIsHoveringTabArea(false)}
        >
          <ScrollArea className="flex-1 min-w-0">
            <div className="flex w-max whitespace-nowrap">
              {tabs.map((tab) => (
                <div
                  key={tab.id}
                  className={cn(
                    "flex items-center px-3 py-2 border-r border-gray-200 cursor-pointer group flex-shrink-0 min-w-[120px] max-w-[200px]",
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
            <ScrollBar orientation="horizontal" />
          </ScrollArea>
          
          <div className="flex items-center px-2 space-x-1 border-l border-gray-200 flex-shrink-0">
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
                // Document viewer
                <div className="h-full flex flex-col">
                  {/* Document Header */}
                  <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gray-50">
                    <div className="flex items-center space-x-2">
                      <File className="h-5 w-5 text-gray-600" />
                      <h3 className="font-medium text-gray-800">{activeTab.name}</h3>
                      <span className="text-sm text-gray-500">({activeTab.type})</span>
                    </div>
                    <div className="flex items-center space-x-2">
                      {activeTab.url && (
                        <a
                          href={activeTab.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
                        >
                          Open in New Tab
                        </a>
                      )}
                    </div>
                  </div>

                  {/* Document Content */}
                  <div className="flex-1 relative">
                    {activeTab.type === 'w2-form' && activeTab.url ? (
                      // PDF Viewer for W2 forms
                      <div className="relative w-full h-full">
                        <iframe
                          src={activeTab.url}
                          className={cn(
                            "w-full h-full border-0 transition-all duration-200",
                            isHoveringTabArea ? "pointer-events-none" : "pointer-events-auto"
                          )}
                          title={`PDF Viewer - ${activeTab.name}`}
                        />
                      </div>
                    ) : activeTab.type?.includes('pdf') && activeTab.url ? (
                      // Generic PDF viewer
                      <div className="relative w-full h-full">
                        <iframe
                          src={activeTab.url}
                          className={cn(
                            "w-full h-full border-0 transition-all duration-200",
                            isHoveringTabArea ? "pointer-events-none" : "pointer-events-auto"
                          )}
                          title={`PDF Viewer - ${activeTab.name}`}
                        />
                      </div>
                    ) : activeTab.type?.includes('image') && activeTab.url ? (
                      // Image viewer
                      <div className="flex items-center justify-center h-full p-4">
                        <img
                          src={activeTab.url}
                          alt={activeTab.name}
                          className="max-w-full max-h-full object-contain"
                        />
                      </div>
                    ) : activeTab.type === 'ingest-tool' && activeTab.id === 'ingest-w2' ? (
                      // Ingest W-2 Tool
                      <div className="h-full flex flex-col p-6">
                        <div className="mb-6">
                          <h2 className="text-xl font-semibold text-gray-800 mb-2">W-2 Tesseract OCR Testing</h2>
                          <p className="text-gray-600">Select a W-2 file to test Tesseract OCR processing</p>
                        </div>

                        {/* File Selection */}
                        <div className="mb-6">
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Select W-2 File:
                          </label>
                          <select
                            value={selectedW2File}
                            onChange={(e) => setSelectedW2File(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                          >
                            <option value="">Choose a file...</option>
                            {w2Files.map((file, index) => (
                              <option key={index} value={file.url}>
                                {file.name} ({file.type.toUpperCase()})
                              </option>
                            ))}
                          </select>
                        </div>

                        {/* Process Button */}
                        <div className="mb-6">
                          <button
                            onClick={() => {
                              const selectedFile = w2Files.find(f => f.url === selectedW2File);
                              if (selectedFile) {
                                processWithTesseract(selectedFile.url, selectedFile.name);
                              }
                            }}
                            disabled={!selectedW2File || isProcessing}
                            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                          >
                            {isProcessing ? 'Processing...' : 'Process with Tesseract'}
                          </button>
                        </div>

                        {/* Results */}
                        <div className="flex-1 min-h-0">
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            OCR Results:
                          </label>
                          <textarea
                            value={ocrResult}
                            readOnly
                            className="w-full h-full p-3 border border-gray-300 rounded-md font-mono text-sm resize-none focus:outline-none"
                            placeholder="OCR results will appear here..."
                          />
                        </div>
                      </div>
                    ) : (
                      // Default text/code editor
                      <div className="p-4">
                        <div className="bg-gray-50 rounded border border-gray-200 p-4">
                          <div className="text-sm text-gray-500 mb-2">
                            {activeTab.path}
                          </div>
                          <div className="font-mono text-sm text-gray-800 space-y-1">
                            <div className="text-blue-600">{"// Document content would be loaded here"}</div>
                            <div className="text-gray-600">{"// Type: " + activeTab.type}</div>
                            {activeTab.url && (
                              <div className="text-gray-600">{"// URL: " + activeTab.url}</div>
                            )}
                          </div>
                        </div>
                      </div>
                    )}
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
