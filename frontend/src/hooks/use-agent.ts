/**
 * React hook for managing AI agent interactions
 * Provides state management and methods for chat, sessions, and real-time updates
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { agentService, AgentSession, ChatRequest, ChatResponse } from '@/services/agent-service';
import { websocketService, MessageType, WebSocketMessage } from '@/services/websocket-service';

export interface ChatMessage {
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

export interface UseAgentOptions {
  agentName?: string;
  matterId?: string;
  autoConnect?: boolean;
  enableWebSocket?: boolean;
}

export interface UseAgentReturn {
  // State
  messages: ChatMessage[];
  currentSession: AgentSession | null;
  isProcessing: boolean;
  isConnected: boolean;
  selectedAgent: string;
  
  // Actions
  sendMessage: (message: string) => Promise<void>;
  setSelectedAgent: (agentName: string) => void;
  createSession: (agentName?: string, matterId?: string) => Promise<void>;
  closeSession: () => Promise<void>;
  clearMessages: () => void;
  
  // WebSocket actions
  joinDocument: (documentId: string, matterId: string) => void;
  leaveDocument: (documentId: string) => void;
  sendDocumentEdit: (documentId: string, edit: any) => void;
  
  // Utilities
  parseActionsFromResponse: (response: string) => ChatMessage['actions'];
}

export function useAgent(options: UseAgentOptions = {}): UseAgentReturn {
  const {
    agentName = 'legal_drafting',
    matterId,
    autoConnect = true,
    enableWebSocket = false,
  } = options;

  // State
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentSession, setCurrentSession] = useState<AgentSession | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [selectedAgent, setSelectedAgentState] = useState(agentName);
  
  // Refs
  const sessionRef = useRef<AgentSession | null>(null);
  const messagesRef = useRef<ChatMessage[]>([]);

  // Update refs when state changes
  useEffect(() => {
    sessionRef.current = currentSession;
  }, [currentSession]);

  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);

  // Initialize session when agent changes
  useEffect(() => {
    if (autoConnect) {
      createSession(selectedAgent, matterId);
    }
  }, [selectedAgent, matterId, autoConnect]);

  // Initialize WebSocket if enabled
  useEffect(() => {
    if (enableWebSocket) {
      initializeWebSocket();
    }

    return () => {
      if (enableWebSocket) {
        websocketService.disconnect();
      }
    };
  }, [enableWebSocket]);

  /**
   * Initialize WebSocket connection
   */
  const initializeWebSocket = useCallback(async () => {
    try {
      await websocketService.connect();
      setIsConnected(websocketService.isConnected());

      // Set up message handlers
      websocketService.onMessage(MessageType.DOCUMENT_EDIT, handleDocumentEdit);
      websocketService.onMessage(MessageType.USER_PRESENCE, handleUserPresence);
      websocketService.onMessage(MessageType.DOCUMENT_LOCK, handleDocumentLock);
      websocketService.onMessage(MessageType.ERROR, handleWebSocketError);
    } catch (error) {
      console.error('Failed to initialize WebSocket:', error);
      setIsConnected(false);
    }
  }, []);

  /**
   * Handle document edit from WebSocket
   */
  const handleDocumentEdit = useCallback((message: WebSocketMessage) => {
    console.log('Document edit received:', message.payload);
    // Handle real-time document edits
    // This would integrate with your document editor
  }, []);

  /**
   * Handle user presence updates
   */
  const handleUserPresence = useCallback((message: WebSocketMessage) => {
    console.log('User presence update:', message.payload);
    // Handle user presence indicators
  }, []);

  /**
   * Handle document lock/unlock
   */
  const handleDocumentLock = useCallback((message: WebSocketMessage) => {
    console.log('Document lock update:', message.payload);
    // Handle document locking UI
  }, []);

  /**
   * Handle WebSocket errors
   */
  const handleWebSocketError = useCallback((message: WebSocketMessage) => {
    console.error('WebSocket error:', message.payload.error);
  }, []);

  /**
   * Create a new agent session
   */
  const createSession = useCallback(async (agentName?: string, matterId?: string) => {
    try {
      const agent = agentName || selectedAgent;
      const session = await agentService.createSession(agent, matterId);
      setCurrentSession(session);
      
      // Add welcome message
      const welcomeMessage: ChatMessage = {
        id: `welcome_${Date.now()}`,
        type: 'assistant',
        content: `Hello! I'm your ${agent.replace('_', ' ')} assistant. How can I help you today?`,
        timestamp: new Date(),
        agent: agent,
        status: 'completed',
      };
      
      setMessages([welcomeMessage]);
    } catch (error) {
      console.error('Failed to create session:', error);
      
      const errorMessage: ChatMessage = {
        id: `error_${Date.now()}`,
        type: 'assistant',
        content: 'I apologize, but I encountered an error connecting to the AI service. The backend may not be running. Please start the backend server and try again.',
        timestamp: new Date(),
        status: 'error',
      };
      
      setMessages([errorMessage]);
    }
  }, [selectedAgent]);

  /**
   * Close current session
   */
  const closeSession = useCallback(async () => {
    if (currentSession) {
      await agentService.closeSession(currentSession.sessionId);
      setCurrentSession(null);
    }
  }, [currentSession]);

  /**
   * Send message to agent
   */
  const sendMessage = useCallback(async (messageContent: string) => {
    if (!messageContent.trim() || isProcessing || !currentSession) {
      return;
    }

    const userMessage: ChatMessage = {
      id: `user_${Date.now()}`,
      type: 'user',
      content: messageContent,
      timestamp: new Date(),
    };

    const processingMessage: ChatMessage = {
      id: `processing_${Date.now()}`,
      type: 'assistant',
      content: 'Processing your request...',
      timestamp: new Date(),
      agent: selectedAgent,
      status: 'processing',
    };

    setMessages(prev => [...prev, userMessage, processingMessage]);
    setIsProcessing(true);

    try {
      const request: ChatRequest = {
        message: messageContent,
        sessionId: currentSession.sessionId,
        agentName: selectedAgent,
        matterId: currentSession.matterId,
        enableTrace: false,
      };

      const response = await agentService.sendMessage(request);

      const assistantMessage: ChatMessage = {
        id: `assistant_${Date.now()}`,
        type: 'assistant',
        content: response.response,
        timestamp: new Date(),
        agent: selectedAgent,
        citations: response.citations,
        actions: parseActionsFromResponse(response.response),
        status: 'completed',
      };

      setMessages(prev => {
        const newMessages = [...prev];
        newMessages[newMessages.length - 1] = assistantMessage;
        return newMessages;
      });

      // Update session if changed
      if (response.sessionId !== currentSession.sessionId) {
        setCurrentSession(prev => prev ? { ...prev, sessionId: response.sessionId } : null);
      }
    } catch (error) {
      console.error('Error sending message:', error);

      const errorMessage: ChatMessage = {
        id: `error_${Date.now()}`,
        type: 'assistant',
        content: 'I apologize, but I encountered an error processing your request. Please ensure the backend server is running and try again.',
        timestamp: new Date(),
        agent: selectedAgent,
        status: 'error',
      };

      setMessages(prev => {
        const newMessages = [...prev];
        newMessages[newMessages.length - 1] = errorMessage;
        return newMessages;
      });
    } finally {
      setIsProcessing(false);
    }
  }, [currentSession, selectedAgent, isProcessing]);

  /**
   * Parse actions from agent response
   */
  const parseActionsFromResponse = useCallback((response: string): ChatMessage['actions'] => {
    const actions: ChatMessage['actions'] = [];

    // Parse response for action indicators
    if (response.includes('Matter Created:') || response.includes('**Matter Created:**')) {
      actions.push({
        type: 'create_matter',
        label: 'View Matter',
        data: { matterId: `matter_${Date.now()}`, name: 'New Matter' },
      });
    }

    if (response.includes('Document') && (response.includes('created') || response.includes('generated'))) {
      actions.push({
        type: 'create_document',
        label: 'Open Document',
        data: { documentId: `doc_${Date.now()}`, name: 'Generated Document' },
      });
    }

    if (response.includes('Deadline') && response.includes('Created')) {
      actions.push({
        type: 'create_deadline',
        label: 'View Deadlines',
        data: { matterId: `matter_${Date.now()}`, deadlines: 1 },
      });
    }

    return actions;
  }, []);

  /**
   * Set selected agent and create new session
   */
  const setSelectedAgent = useCallback((agentName: string) => {
    setSelectedAgentState(agentName);
  }, []);

  /**
   * Clear all messages
   */
  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  /**
   * Join document for real-time editing
   */
  const joinDocument = useCallback((documentId: string, matterId: string) => {
    if (enableWebSocket && websocketService.isConnected()) {
      websocketService.joinDocument(documentId, matterId);
    }
  }, [enableWebSocket]);

  /**
   * Leave document
   */
  const leaveDocument = useCallback((documentId: string) => {
    if (enableWebSocket && websocketService.isConnected()) {
      websocketService.leaveDocument(documentId);
    }
  }, [enableWebSocket]);

  /**
   * Send document edit
   */
  const sendDocumentEdit = useCallback((documentId: string, edit: any) => {
    if (enableWebSocket && websocketService.isConnected()) {
      websocketService.sendDocumentEdit(documentId, edit);
    }
  }, [enableWebSocket]);

  return {
    // State
    messages,
    currentSession,
    isProcessing,
    isConnected,
    selectedAgent,

    // Actions
    sendMessage,
    setSelectedAgent,
    createSession,
    closeSession,
    clearMessages,

    // WebSocket actions
    joinDocument,
    leaveDocument,
    sendDocumentEdit,

    // Utilities
    parseActionsFromResponse,
  };
}