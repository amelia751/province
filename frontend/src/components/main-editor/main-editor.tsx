"use client";

import React, { useState, useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import { PdfViewer } from "@/components/pdf-viewer";
import { TaxFormFiller } from '@/components/tax-form-filler';
import "@/components/pdf-viewer/pdf-viewer.css";
import {
  X,
  Circle,
  MoreHorizontal,
  Split,
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
  w2Data?: any;
  hasChanges?: boolean;
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

const MainEditor: React.FC<MainEditorProps> = ({ selectedDocument }) => {
  const [tabs, setTabs] = useState(mockTabs);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [autoScroll, setAutoScroll] = useState(true);
  const [selectedW2File, setSelectedW2File] = useState<string>('');
  const [ocrResult, setOcrResult] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState(false);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const logsContainerRef = useRef<HTMLDivElement>(null);

  // Available W2 files for testing
  const w2Files = [
    {
      name: 'W2_XL_input_clean_1000.pdf',
      url: 'https://province-documents-[REDACTED-ACCOUNT-ID]-us-east-1.s3.us-east-1.amazonaws.com/datasets/w2-forms/W2_Clean_DataSet_01_20Sep2019/W2_XL_input_clean_1000.pdf',
      type: 'pdf'
    },
    {
      name: 'W2_XL_input_clean_1000.jpg',
      url: 'https://province-documents-[REDACTED-ACCOUNT-ID]-us-east-1.s3.us-east-1.amazonaws.com/datasets/w2-forms/W2_Clean_DataSet_01_20Sep2019/W2_XL_input_clean_1000.jpg',
      type: 'image'
    }
  ];

  // Bedrock Data Automation W2 processing function
  const processWithBedrockDataAutomation = async (fileUrl: string, fileName: string) => {
    setIsProcessing(true);
    setOcrResult('Processing with AWS Bedrock Data Automation...');
    
    try {
      // Extract S3 key from the URL
      const s3Key = fileUrl.split('.amazonaws.com/')[1];
      
      // Call the backend ingest_w2 API
      const response = await fetch('/api/v1/tax/ingest-w2', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          s3_key: s3Key,
          taxpayer_name: 'Test User',
          tax_year: 2024
        })
      });
      
      if (!response.ok) {
        throw new Error(`API call failed: ${response.status} ${response.statusText}`);
      }
      
      const result = await response.json();
      
      if (result.success) {
        // Format the structured W2 data for display
        const formattedResult = formatW2Results(result, fileName);
        setOcrResult(formattedResult);
        
        // Create a new tab for tax form filling
        const newTab: EditorTab = {
          id: `tax-form-filler-${Date.now()}`,
          name: `Fill 1040 Form`,
          path: 'tax/form-filler',
          isDirty: false,
          type: 'tax-form-filler',
          url: undefined,
          w2Data: result, // Pass the W2 extraction result
          isActive: false,
          hasChanges: false
        };
        
        setTabs(prevTabs => [...prevTabs, newTab]);
        
        // Add success log
        addLog('success', 'system', `W2 processed successfully. Tax form filler ready.`, 
               `Extracted data from ${result.forms_count} W2 form(s). Total wages: $${result.total_wages.toLocaleString()}`);
      } else {
        setOcrResult(`❌ Processing failed: ${result.error}`);
        addLog('error', 'system', 'W2 processing failed', result.error);
      }
    } catch (error) {
      console.error('W2 processing error:', error);
      setOcrResult(`❌ Error processing file: ${error instanceof Error ? error.message : 'Unknown error'}`);
    } finally {
      setIsProcessing(false);
    }
  };

  // Format W2 results for display
  const formatW2Results = (result: {
    w2_extract: { forms: Array<{ employer: { name?: string; EIN?: string; address?: string }; employee: { name?: string; SSN?: string; address?: string }; boxes: Record<string, string> }> };
    validation_results: { is_valid: boolean; warnings: string[]; errors: string[] };
    processing_method: string;
    forms_count: number;
    total_wages: number;
    total_withholding: number;
  }, fileName: string) => {
    const w2Extract = result.w2_extract;
    const validation = result.validation_results;
    
    let output = `🎯 AWS Bedrock Data Automation Results for ${fileName}\n`;
    output += `📊 Processing Method: ${result.processing_method}\n`;
    output += `📋 Forms Processed: ${result.forms_count}\n`;
    output += `💰 Total Wages: $${result.total_wages.toLocaleString()}\n`;
    output += `💸 Total Withholding: $${result.total_withholding.toLocaleString()}\n\n`;
    
    // Display each W2 form
    w2Extract.forms.forEach((form, index: number) => {
      output += `📄 W-2 Form ${index + 1}:\n`;
      output += `${'='.repeat(50)}\n\n`;
      
      // Employer Information
      output += `🏢 EMPLOYER INFORMATION:\n`;
      output += `   Company: ${form.employer.name || 'Not found'}\n`;
      output += `   EIN: ${form.employer.EIN || 'Not found'}\n`;
      output += `   Address: ${form.employer.address || 'Not found'}\n\n`;
      
      // Employee Information
      output += `👤 EMPLOYEE INFORMATION:\n`;
      output += `   Name: ${form.employee.name || 'Not found'}\n`;
      output += `   SSN: ${form.employee.SSN || 'Not found'}\n`;
      output += `   Address: ${form.employee.address || 'Not found'}\n\n`;
      
      // W2 Boxes
      output += `📊 W-2 TAX BOXES:\n`;
      const boxes = form.boxes;
      
      if (boxes['1']) output += `   Box 1 - Wages, tips, other compensation: $${parseFloat(boxes['1']).toLocaleString()}\n`;
      if (boxes['2']) output += `   Box 2 - Federal income tax withheld: $${parseFloat(boxes['2']).toLocaleString()}\n`;
      if (boxes['3']) output += `   Box 3 - Social security wages: $${parseFloat(boxes['3']).toLocaleString()}\n`;
      if (boxes['4']) output += `   Box 4 - Social security tax withheld: $${parseFloat(boxes['4']).toLocaleString()}\n`;
      if (boxes['5']) output += `   Box 5 - Medicare wages and tips: $${parseFloat(boxes['5']).toLocaleString()}\n`;
      if (boxes['6']) output += `   Box 6 - Medicare tax withheld: $${parseFloat(boxes['6']).toLocaleString()}\n`;
      if (boxes['7']) output += `   Box 7 - Social security tips: $${parseFloat(boxes['7']).toLocaleString()}\n`;
      if (boxes['8']) output += `   Box 8 - Allocated tips: $${parseFloat(boxes['8']).toLocaleString()}\n`;
      if (boxes['10']) output += `   Box 10 - Dependent care benefits: $${parseFloat(boxes['10']).toLocaleString()}\n`;
      if (boxes['11']) output += `   Box 11 - Nonqualified plans: $${parseFloat(boxes['11']).toLocaleString()}\n`;
      if (boxes['12']) output += `   Box 12 - Codes: ${boxes['12']}\n`;
      if (boxes['13']) output += `   Box 13 - Checkboxes: ${boxes['13']}\n`;
      if (boxes['14']) output += `   Box 14 - Other: ${boxes['14']}\n`;
      if (boxes['15']) output += `   Box 15 - State: ${boxes['15']}\n`;
      if (boxes['16']) output += `   Box 16 - State wages: $${parseFloat(boxes['16']).toLocaleString()}\n`;
      if (boxes['17']) output += `   Box 17 - State income tax: $${parseFloat(boxes['17']).toLocaleString()}\n`;
      if (boxes['18']) output += `   Box 18 - Local wages: $${parseFloat(boxes['18']).toLocaleString()}\n`;
      if (boxes['19']) output += `   Box 19 - Local income tax: $${parseFloat(boxes['19']).toLocaleString()}\n`;
      if (boxes['20']) output += `   Box 20 - Locality name: ${boxes['20']}\n`;
      
      output += `\n`;
    });
    
    // Validation Results
    output += `✅ VALIDATION RESULTS:\n`;
    output += `   Status: ${validation.is_valid ? '✅ Valid' : '❌ Invalid'}\n`;
    if (validation.warnings.length > 0) {
      output += `   Warnings:\n`;
      validation.warnings.forEach((warning: string) => {
        output += `     ⚠️  ${warning}\n`;
      });
    }
    if (validation.errors.length > 0) {
      output += `   Errors:\n`;
      validation.errors.forEach((error: string) => {
        output += `     ❌ ${error}\n`;
      });
    }
    
    output += `\n📋 RAW JSON DATA:\n`;
    output += `${'='.repeat(50)}\n`;
    output += JSON.stringify(result, null, 2);
    
    return output;
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
        {/* Tab Bar */}
        <div className="flex items-center border-b border-gray-100 bg-gray-50 relative z-10">
          <div className="flex-1 min-w-0 overflow-x-auto overflow-y-hidden hover:scrollbar-thin scrollbar-none">
            <div className="inline-flex min-w-full">
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
          </div>

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
                    {(activeTab.type === 'w2-form' ||
                      activeTab.type === 'tax-return' ||
                      activeTab.type?.includes('pdf') ||
                      activeTab.name?.toLowerCase().endsWith('.pdf')) && activeTab.url ? (
                      // PDF Viewer with overlay support
                      <PdfViewer
                        url={activeTab.url}
                        className="w-full h-full"
                      />
                    ) : activeTab.type?.includes('image') && activeTab.url ? (
                      // Image viewer
                      <div className="flex items-center justify-center h-full p-4">
                        {/* eslint-disable-next-line @next/next/no-img-element */}
                        <img
                          src={activeTab.url}
                          alt={activeTab.name}
                          className="max-w-full max-h-full object-contain"
                        />
                      </div>
                    ) : activeTab.type === 'tax-form-filler' ? (
                      // Tax Form Filler
                      <div className="h-full overflow-auto">
                        <TaxFormFiller
                          w2Data={activeTab.w2Data}
                          onFormFilled={(result) => {
                            addLog('success', 'system', 'Tax form generated successfully', 
                                   `Form URL: ${result.filled_form_url}`);
                            
                            // Optionally create a new tab with the filled form
                            if (result.filled_form_url) {
                              const filledFormTab: EditorTab = {
                                id: `filled-1040-${Date.now()}`,
                                name: 'Filled 1040 Form',
                                path: 'tax/filled-1040',
                                isDirty: false,
                                type: 'pdf',
                                url: result.filled_form_url,
                                isActive: false,
                                hasChanges: false
                              };
                              setTabs(prevTabs => [...prevTabs, filledFormTab]);
                            }
                          }}
                        />
                      </div>
                    ) : activeTab.type === 'ingest-tool' && activeTab.id === 'ingest-w2' ? (
                      // Ingest W-2 Tool
                      <div className="h-full flex flex-col p-6">
                        <div className="mb-6">
                          <h2 className="text-xl font-semibold text-gray-800 mb-2">W-2 Bedrock Data Automation</h2>
                          <p className="text-gray-600">Select a W-2 file to process with AWS Bedrock Data Automation for superior accuracy</p>
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
                                processWithBedrockDataAutomation(selectedFile.url, selectedFile.name);
                              }
                            }}
                            disabled={!selectedW2File || isProcessing}
                            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
                          >
                            {isProcessing ? 'Processing...' : 'Process with Bedrock Data Automation'}
                          </button>
                        </div>

                        {/* Results */}
                        <div className="flex-1 min-h-0">
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            Bedrock Data Automation Results:
                          </label>
                          <textarea
                            value={ocrResult}
                            readOnly
                            className="w-full h-full p-3 border border-gray-300 rounded-md font-mono text-sm resize-none focus:outline-none"
                            placeholder="Structured W2 data will appear here..."
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
            ) : activeTab ? (
              <>
                <span>{activeTab.name}</span>
                {activeTab.type && (
                  <span className="text-gray-500">
                    {activeTab.type === 'w2-form' ? 'W-2 Form' :
                     activeTab.type === 'tax-return' ? 'Tax Return' :
                     activeTab.type === 'tax-form-filler' ? '1040 Form' :
                     activeTab.type === 'ingest-tool' ? 'Tax Tool' :
                     activeTab.type?.includes('pdf') ? 'PDF Document' :
                     activeTab.type?.includes('image') ? 'Image' :
                     activeTab.type}
                  </span>
                )}
                <span className="text-gray-500">Last edited: Just now</span>
              </>
            ) : null}
          </div>
          <div className="flex items-center space-x-2">
            {/* Empty right side - removed Run/Debug buttons */}
          </div>
        </div>
      </div>
    </div>
  );
};

export default MainEditor;
