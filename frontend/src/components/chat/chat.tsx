"use client";

import React, { useState, useEffect, useRef } from "react";
import { cn } from "@/lib/utils";
import { useAgent } from "@/hooks/use-agent";
import AgentActions from "./agent-actions";
import VoiceChat from "./voice-chat";
import ChatInputArea from "./chat-input-area";
import EmptyChatState from "./empty-chat";
import { DocumentProcessingNotifications } from "./document-processing-notifications";
import {
  Send,
  User,
  Bot,
  RotateCcw,
  FileText,
  Calendar,
  Search,
  Loader2,
  MessageSquare,
  Mic2,
  ChevronDown,
  Settings,
  RefreshCw,
  AlertCircle,
  Calculator
} from "lucide-react";
import { Button } from "@/components/ui/button";

interface ChatProps {
  onWidthChange?: (width: number) => void;
  onDocumentCreate?: (document: any) => void;
  onMatterCreate?: (matter: any) => void;
  onDeadlineCreate?: (deadline: any) => void;
  engagementId?: string;
  userId?: string;  // Clerk user ID for PII-safe storage
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
  isStreaming?: boolean;
}


type ChatMode = 'text' | 'voice';

const TaxChatInterface: React.FC<ChatProps> = ({
  onDocumentCreate,
  onMatterCreate,
  onDeadlineCreate,
  engagementId,
  userId
}) => {
  const [inputValue, setInputValue] = useState("");
  // TODO: Re-enable voice mode later - temporarily defaulting to text
  const [chatMode, setChatMode] = useState<ChatMode>('text'); // Temporarily using text mode (was 'voice')
  const [showScrollToBottom, setShowScrollToBottom] = useState(false);
  const [isUserScrolling, setIsUserScrolling] = useState(false);
  const [hasReceivedFirstResponse, setHasReceivedFirstResponse] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectionError, setConnectionError] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const scrollTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const {
    messages,
    currentSession,
    isProcessing,
    selectedAgent,
    sendMessage: sendAgentMessage,
    setSelectedAgent,
    createSession,
  } = useAgent({
    agentName: 'TaxPlannerAgent', // Now using the correct tax agent
    autoConnect: true,
    enableWebSocket: false,
    userId: userId,  // Pass Clerk user ID for PII-safe storage
  });

  // Expose debug info to global window for debugging
  useEffect(() => {
    if (typeof window !== 'undefined') {
      (window as any).chatDebugInfo = {
        messages: messages.length,
        currentSession: currentSession ? {
          sessionId: currentSession.sessionId,
          agentName: currentSession.agentName,
          agentId: currentSession.agentId,
          status: currentSession.status
        } : null,
        isProcessing,
        selectedAgent,
        isConnected,
        isConnecting,
        connectionError,
        lastUpdate: new Date().toISOString()
      };
    }
  }, [messages, currentSession, isProcessing, selectedAgent, isConnected, isConnecting, connectionError]);

  const displayMessages = messages;

  // Simulate connection process for tax agent
  useEffect(() => {
    if (currentSession && !isConnected) {
      setIsConnecting(true);
      const timer = setTimeout(() => {
        setIsConnected(true);
        setIsConnecting(false);
        setHasReceivedFirstResponse(true);
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [currentSession, isConnected]);

  // Auto scroll to bottom when new messages arrive
  useEffect(() => {
    if (!isUserScrolling && messagesContainerRef.current) {
      const container = messagesContainerRef.current;
      const shouldAutoScroll = container.scrollHeight - container.scrollTop - container.clientHeight < 100;

      if (shouldAutoScroll) {
        container.scrollTo({
          top: container.scrollHeight,
          behavior: 'smooth'
        });
      }
    }
  }, [displayMessages, isUserScrolling]);

  // Handle scroll events
  const handleScroll = () => {
    if (!messagesContainerRef.current) return;

    const container = messagesContainerRef.current;
    const { scrollTop, scrollHeight, clientHeight } = container;
    const atBottom = scrollHeight - scrollTop - clientHeight < 50;

    setShowScrollToBottom(!atBottom);

    if (!atBottom) {
      setIsUserScrolling(true);
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
      scrollTimeoutRef.current = setTimeout(() => {
        const newScrollPos = container.scrollHeight - container.scrollTop - container.clientHeight;
        if (newScrollPos < 50) {
          setIsUserScrolling(false);
        }
      }, 150);
    } else {
      setIsUserScrolling(false);
    }
  };

  // Scroll to bottom
  const scrollToBottom = () => {
    if (messagesContainerRef.current) {
      messagesContainerRef.current.scrollTo({
        top: messagesContainerRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
    setShowScrollToBottom(false);
  };

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

  const handleRetryConnection = async () => {
    setConnectionError(false);
    setIsConnecting(true);
    try {
      await createSession('TaxPlannerAgent');
      setIsConnected(true);
    } catch (error) {
      setConnectionError(true);
    } finally {
      setIsConnecting(false);
    }
  };

  const getAgentIcon = (agent?: string) => {
    // Tax-focused icons
    switch (agent) {
      case 'TaxPlannerAgent':
        return <FileText className="h-4 w-4 text-white" />;
      case 'TaxIntakeAgent':
        return <MessageSquare className="h-4 w-4 text-white" />;
      case 'W2IngestAgent':
        return <FileText className="h-4 w-4 text-white" />;
      case 'Calc1040Agent':
        return <Calculator className="h-4 w-4 text-white" />;
      case 'ReviewAgent':
        return <Search className="h-4 w-4 text-white" />;
      case 'ReturnRenderAgent':
        return <FileText className="h-4 w-4 text-white" />;
      case 'DeadlinesAgent':
        return <Calendar className="h-4 w-4 text-white" />;
      case 'ComplianceAgent':
        return <Settings className="h-4 w-4 text-white" />;
      default:
        return <Bot className="h-4 w-4 text-white" />;
    }
  };

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (scrollTimeoutRef.current) {
        clearTimeout(scrollTimeoutRef.current);
      }
    };
  }, []);

  return (
    <div className="flex flex-col h-full bg-white relative">
      {/* Connection Loading Overlay */}
      {!hasReceivedFirstResponse && !connectionError && (
        <div className="absolute inset-0 bg-white/95 backdrop-blur-sm flex items-center justify-center z-50 rounded-3xl">
          <div className="flex flex-col items-center space-y-3">
            <Loader2 className="h-8 w-8 text-black animate-spin" />
            <p className="text-sm text-gray-600">Initializing session...</p>
          </div>
        </div>
      )}

      {/* Connection Failed Overlay */}
      {connectionError && (
        <div className="absolute inset-0 bg-white/95 backdrop-blur-sm flex items-center justify-center z-50 rounded-3xl">
          <div className="text-center p-6 sm:p-8 max-w-md mx-4">
            <div className="relative mb-8">
              <div className="relative w-20 h-20 sm:w-24 sm:h-24 mx-auto">
                <div className="absolute inset-0 bg-gray-100 rounded-full animate-pulse"></div>
                <div className="absolute inset-0 bg-black rounded-full flex items-center justify-center">
                  <AlertCircle className="h-10 w-10 sm:h-12 sm:w-12 text-white" />
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <h3 className="text-xl sm:text-2xl font-bold text-black tracking-tight">
                Connection Failed
              </h3>
              <p className="text-sm sm:text-base text-gray-600 leading-relaxed px-2">
                We couldn't connect to your tax assistant. This might be due to network issues or high server load.
              </p>
              <Button
                onClick={handleRetryConnection}
                className="w-full sm:w-auto px-8 py-3 bg-black hover:bg-gray-800 text-white font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-200"
              >
                <RefreshCw className="h-5 w-5 mr-2" />
                Retry Connection
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Messages Container */}
      <div className="flex-1 relative overflow-hidden">
        <div
          ref={messagesContainerRef}
          className="h-full overflow-y-auto p-4 scroll-smooth"
          onScroll={handleScroll}
          style={{ scrollBehavior: 'smooth' }}
        >
          {displayMessages.length === 0 ? (
            <EmptyChatState />
          ) : (
            <div className="space-y-4 max-w-4xl mx-auto px-4">
              {displayMessages.map((message, idx) => (
                <div key={message.id} className="w-full" style={{ userSelect: 'text' }}>
                  <div className={cn("flex", message.type === 'user' ? "justify-end" : "justify-start")} style={{ userSelect: 'text' }}>
                    <div
                      className={cn(
                        "max-w-[80%] rounded-lg px-3 py-2",
                        message.type === 'user'
                          ? "bg-black text-white"
                          : "bg-gray-100 text-black"
                      )}
                      style={{ userSelect: 'text' }}
                    >
                      <div
                        className="text-sm whitespace-pre-wrap cursor-text"
                        style={{
                          userSelect: 'text',
                          WebkitUserSelect: 'text',
                          MozUserSelect: 'text',
                          msUserSelect: 'text',
                          WebkitTouchCallout: 'default'
                        }}
                      >
                        {message.content}
                      </div>

                      {message.citations && message.citations.length > 0 && (
                        <div className="mt-2 space-y-1">
                          <div className="text-xs font-medium text-gray-600">Sources:</div>
                          {message.citations.map((citation, idx) => (
                            <div key={idx} className="text-xs bg-white p-2 rounded border border-gray-200">
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

                      <div className="flex items-center justify-between mt-1">
                        <div className={cn("text-[10px]", message.type === 'user' ? "text-gray-300" : "text-gray-500")}>
                          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </div>
                        {message.status === 'processing' && (
                          <Loader2 className="h-3 w-3 text-gray-400 animate-spin" />
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Scroll to Bottom Button */}
        {showScrollToBottom && (
          <div className="absolute bottom-4 right-4 z-10">
            <Button
              onClick={scrollToBottom}
              size="sm"
              className="rounded-full w-10 h-10 p-0 shadow-lg bg-black hover:bg-gray-800 text-white"
              aria-label="Scroll to bottom"
            >
              <ChevronDown className="h-4 w-4" />
            </Button>
          </div>
        )}
      </div>

      {/* Chat Input Area */}
      <ChatInputArea
        hasReceivedFirstResponse={hasReceivedFirstResponse}
        isConnected={isConnected}
        isContextSwitching={isConnecting}
        isTextSending={isProcessing}
        inputValue={inputValue}
        setInputValue={setInputValue}
        handleSendMessage={sendMessage}
        handleKeyPress={handleKeyPress}
        engagementId={engagementId}
      />
    </div>
  );
};

export default TaxChatInterface;
