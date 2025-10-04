"use client";

import React, { useState, useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import { useAgent } from "@/hooks/use-agent";
import AgentActions from "./agent-actions";
import {
  Send,
  Paperclip,
  Mic,
  User,
  Bot,
  Copy,
  ThumbsUp,
  ThumbsDown,
  RotateCcw,
  FileText,
  Calendar,
  Search,
  Loader2,
  CheckCircle,
  AlertCircle,
  Settings
} from "lucide-react";

interface ChatProps {
  onWidthChange?: (width: number) => void;
  onDocumentCreate?: (document: any) => void;
  onMatterCreate?: (matter: any) => void;
  onDeadlineCreate?: (deadline: any) => void;
}

interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  agent?: string;
  citations?: Array<{
    title: string;
    url: string;
    snippet: string;
  }>;
  actions?: Array<{
    type: 'create_document' | 'create_matter' | 'create_deadline' | 'search';
    label: string;
    data: any;
  }>;
  status?: 'sending' | 'processing' | 'completed' | 'error';
}

const mockMessages: ChatMessage[] = [
  {
    id: "1",
    type: "user",
    content: "I need to draft a contract for a new client acquisition. Can you help me set up the matter and create the initial documents?",
    timestamp: new Date(Date.now() - 300000)
  },
  {
    id: "2",
    type: "assistant",
    content: "I'll help you set up a new client acquisition matter and draft the contract. Let me create the matter structure and generate the initial contract template.\n\n**Matter Created:** Client Acquisition - [Client Name]\n**Practice Area:** Corporate Law\n**Documents Generated:**\n- Service Agreement Template\n- Engagement Letter\n- Conflict Check Form\n\nI've created a comprehensive folder structure with all necessary documents. The service agreement includes standard terms for professional services, liability limitations, and payment terms. Would you like me to customize any specific clauses?",
    timestamp: new Date(Date.now() - 240000),
    agent: "legal_drafting",
    actions: [
      {
        type: 'create_matter',
        label: 'View Matter',
        data: { matterId: 'matter_123', name: 'Client Acquisition - [Client Name]' }
      },
      {
        type: 'create_document',
        label: 'Open Service Agreement',
        data: { documentId: 'doc_456', name: 'Service Agreement Template' }
      }
    ],
    status: 'completed'
  },
  {
    id: "3",
    type: "user",
    content: "Perfect! Can you also set up deadlines for the key milestones?",
    timestamp: new Date(Date.now() - 120000)
  },
  {
    id: "4",
    type: "assistant",
    content: "I've set up the key deadlines for your client acquisition matter:\n\n**Deadlines Created:**\n- Initial client meeting: 3 days from now\n- Contract review and revisions: 1 week from now\n- Final contract execution: 2 weeks from now\n- Engagement letter signed: 2 weeks from now\n\nAll deadlines include automatic reminders and are integrated with your calendar. The system will notify you 24 hours before each deadline.",
    timestamp: new Date(Date.now() - 60000),
    agent: "case_management",
    actions: [
      {
        type: 'create_deadline',
        label: 'View Deadlines',
        data: { matterId: 'matter_123', deadlines: 4 }
      }
    ],
    status: 'completed'
  },
  ...Array.from({ length: 10 }, (_, i) => ({
    id: `demo_${i + 5}`,
    type: (i % 2 === 0 ? 'user' : 'assistant') as 'user' | 'assistant',
    content: i % 2 === 0
      ? `This is user message ${i + 1} to demonstrate scrolling in the chat interface.`
      : `This is assistant response ${i + 1}. I can help you with various legal tasks including document drafting, research, and case management. The chat interface supports scrolling when there are many messages.`,
    timestamp: new Date(Date.now() - (60000 * (10 - i))),
    agent: i % 3 === 0 ? 'legal_drafting' : i % 3 === 1 ? 'legal_research' : 'case_management',
    status: 'completed' as const
  }))
];

const Chat: React.FC<ChatProps> = ({
  onDocumentCreate,
  onMatterCreate,
  onDeadlineCreate
}) => {
  const [inputValue, setInputValue] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const {
    messages,
    currentSession,
    isProcessing,
    selectedAgent,
    sendMessage: sendAgentMessage,
    setSelectedAgent,
    createSession,
  } = useAgent({
    agentName: 'legal_drafting',
    autoConnect: false,
    enableWebSocket: false,
  });

  const displayMessages = messages.length > 0 ? messages : mockMessages;

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [displayMessages]);

  const sendMessage = async () => {
    if (!inputValue.trim() || isProcessing) return;
    const messageContent = inputValue;
    setInputValue("");
    if (!currentSession) {
      await createSession(selectedAgent);
    }
    await sendAgentMessage(messageContent);
  };

  const handleActionClick = (action: NonNullable<ChatMessage['actions']>[0]) => {
    switch (action.type) {
      case 'create_document':
        onDocumentCreate?.(action.data);
        break;
      case 'create_matter':
        onMatterCreate?.(action.data);
        break;
      case 'create_deadline':
        onDeadlineCreate?.(action.data);
        break;
      case 'search':
        break;
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const getAgentIcon = (agent?: string) => {
    switch (agent) {
      case 'legal_drafting':
        return <FileText className="h-4 w-4 text-white" />;
      case 'legal_research':
        return <Search className="h-4 w-4 text-white" />;
      case 'case_management':
        return <Calendar className="h-4 w-4 text-white" />;
      default:
        return <Bot className="h-4 w-4 text-white" />;
    }
  };

  const getStatusIcon = (status?: string) => {
    switch (status) {
      case 'processing':
        return <Loader2 className="h-3 w-3 text-blue-500 animate-spin" />;
      case 'completed':
        return <CheckCircle className="h-3 w-3 text-green-500" />;
      case 'error':
        return <AlertCircle className="h-3 w-3 text-red-500" />;
      default:
        return null;
    }
  };

  return (
    <div className="chat-container flex bg-white h-full w-full">
      <div className="flex flex-col h-full flex-1 min-h-0">
        {/* Header */}
        <div className="flex items-center justify-between p-3 border-b border-gray-100">
          <div className="flex items-center space-x-2">
            <h3 className="text-sm font-medium text-gray-900">Legal AI Assistant</h3>
            {currentSession && (
              <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                {selectedAgent.replace('_', ' ')}
              </span>
            )}
          </div>
          <div className="flex items-center space-x-1">
            <select
              value={selectedAgent}
              onChange={(e) => setSelectedAgent(e.target.value)}
              className="text-xs border border-gray-200 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-black"
            >
              <option value="legal_drafting">Legal Drafting</option>
              <option value="legal_research">Legal Research</option>
              <option value="case_management">Case Management</option>
            </select>
            <button
              onClick={() => createSession(selectedAgent)}
              className="p-1 hover:bg-gray-100 rounded"
              title="Reset session"
            >
              <RotateCcw className="h-4 w-4 text-gray-500" />
            </button>
            <button className="p-1 hover:bg-gray-100 rounded">
              <Settings className="h-4 w-4 text-gray-500" />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 relative min-h-0">
          {/* Actual scroll container */}
          <div className="absolute inset-0 overflow-y-auto">
            <div className="p-4 space-y-4">
              {displayMessages.length === 0 ? (
                <div
                  className="flex items-center justify-center text-gray-500"
                  style={{ minHeight: 'calc(100vh - 200px)' }}
                >
                  <div className="text-center">
                    <Bot className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                    <div className="text-lg mb-2">Welcome to Legal AI Assistant</div>
                    <div className="text-sm">Start a conversation to get help with legal tasks</div>
                  </div>
                </div>
              ) : (
                displayMessages.map((message) => (
                  <div
                    key={message.id}
                    className={cn(
                      "flex space-x-3",
                      message.type === 'user' ? "justify-end" : "justify-start"
                    )}
                  >
                    {message.type === 'assistant' && (
                      <div className="w-8 h-8 bg-black rounded-full flex items-center justify-center flex-shrink-0">
                        {getAgentIcon(message.agent)}
                      </div>
                    )}

                    <div
                      className={cn(
                        "max-w-[80%] rounded-lg px-3 py-2",
                        message.type === 'user'
                          ? "bg-black text-white"
                          : "bg-gray-100 text-gray-900"
                      )}
                    >
                      <div className="text-sm whitespace-pre-wrap">{message.content}</div>

                      {message.citations && message.citations.length > 0 && (
                        <div className="mt-2 space-y-1">
                          <div className="text-xs font-medium text-gray-600">Sources:</div>
                          {message.citations.map((citation, idx) => (
                            <div key={idx} className="text-xs bg-white p-2 rounded border">
                              <div className="font-medium">{citation.title}</div>
                              <div className="text-gray-600 mt-1">{citation.snippet}</div>
                            </div>
                          ))}
                        </div>
                      )}

                      {message.actions && message.actions.length > 0 && (
                        <AgentActions
                          actions={message.actions}
                          onActionExecute={handleActionClick}
                        />
                      )}

                      <div
                        className={cn(
                          "flex items-center justify-between mt-1",
                          message.type === 'user' ? "text-gray-300" : "text-gray-500"
                        )}
                      >
                        <div className="text-xs">
                          {message.timestamp.toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit'
                          })}
                          {message.agent && (
                            <span className="ml-2 capitalize">
                              • {message.agent.replace('_', ' ')}
                            </span>
                          )}
                        </div>
                        {message.status && (
                          <div className="flex items-center">
                            {getStatusIcon(message.status)}
                          </div>
                        )}
                      </div>
                    </div>

                    {message.type === 'user' && (
                      <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center flex-shrink-0">
                        <User className="h-4 w-4 text-gray-600" />
                      </div>
                    )}

                    {message.type === 'assistant' && (
                      <div className="flex flex-col space-y-1 mt-1">
                        <button className="p-1 hover:bg-gray-100 rounded">
                          <Copy className="h-3 w-3 text-gray-400" />
                        </button>
                        <button className="p-1 hover:bg-gray-100 rounded">
                          <ThumbsUp className="h-3 w-3 text-gray-400" />
                        </button>
                        <button className="p-1 hover:bg-gray-100 rounded">
                          <ThumbsDown className="h-3 w-3 text-gray-400" />
                        </button>
                      </div>
                    )}
                  </div>
                ))
              )}

              {/* Scroll anchor */}
              <div ref={messagesEndRef} />
            </div>
          </div>
        </div>

        {/* Input */}
        <div className="p-4 border-t border-gray-100">
          <div className="flex items-end space-x-2">
            <div className="flex-1 relative">
              <textarea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyPress}
                placeholder="Ask me anything..."
                className="w-full resize-none border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
                rows={1}
                style={{ minHeight: '36px', maxHeight: '120px' }}
              />
            </div>
            <div className="flex space-x-1">
              <button className="p-2 hover:bg-gray-100 rounded">
                <Paperclip className="h-4 w-4 text-gray-500" />
              </button>
              <button className="p-2 hover:bg-gray-100 rounded">
                <Mic className="h-4 w-4 text-gray-500" />
              </button>
              <button
                onClick={sendMessage}
                disabled={!inputValue.trim() || isProcessing}
                className={cn(
                  "p-2 rounded transition-colors",
                  inputValue.trim() && !isProcessing
                    ? "bg-black text-white hover:bg-gray-800"
                    : "bg-gray-100 text-gray-400 cursor-not-allowed"
                )}
              >
                {isProcessing ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Chat;
