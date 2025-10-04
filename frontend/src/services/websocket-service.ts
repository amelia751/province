/**
 * WebSocket Service for real-time collaboration
 * Handles document editing, user presence, and live updates
 */

export interface WebSocketMessage {
  type: string;
  payload: any;
  user_id?: string;
  timestamp?: string;
  message_id?: string;
}

export interface DocumentEdit {
  operation: 'insert' | 'delete' | 'replace';
  position: number;
  content: string;
  length?: number;
  user_id: string;
  timestamp: string;
}

export interface UserPresence {
  user_id: string;
  connection_id: string;
  document_id: string;
  cursor_position: number;
  selection_start: number;
  selection_end: number;
  last_seen: string;
  user_name: string;
  user_color: string;
}

export interface DocumentSession {
  document_id: string;
  matter_id: string;
  active_users: UserPresence[];
  document_version: string;
  last_sync: string;
  lock_holder?: string;
  lock_expires?: string;
}

export enum MessageType {
  CONNECT = 'connect',
  DISCONNECT = 'disconnect',
  JOIN_DOCUMENT = 'join_document',
  LEAVE_DOCUMENT = 'leave_document',
  DOCUMENT_EDIT = 'document_edit',
  CURSOR_POSITION = 'cursor_position',
  USER_PRESENCE = 'user_presence',
  DOCUMENT_LOCK = 'document_lock',
  DOCUMENT_UNLOCK = 'document_unlock',
  SYNC_REQUEST = 'sync_request',
  SYNC_RESPONSE = 'sync_response',
  ERROR = 'error',
}

type MessageHandler = (message: WebSocketMessage) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private url: string;
  private userId: string;
  private matterId?: string;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private messageHandlers: Map<string, MessageHandler[]> = new Map();
  private isConnecting = false;
  private currentDocumentId?: string;

  constructor() {
    this.url = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/api/v1/ws/connect';
    this.userId = this.generateUserId(); // In real app, get from auth
  }

  /**
   * Connect to WebSocket server
   */
  async connect(userId?: string, matterId?: string): Promise<boolean> {
    if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
      return true;
    }

    this.isConnecting = true;
    this.userId = userId || this.userId;
    this.matterId = matterId;

    try {
      const wsUrl = new URL(this.url);
      wsUrl.searchParams.set('user_id', this.userId);
      if (this.matterId) {
        wsUrl.searchParams.set('matter_id', this.matterId);
      }

      this.ws = new WebSocket(wsUrl.toString());

      return new Promise((resolve, reject) => {
        if (!this.ws) {
          reject(new Error('Failed to create WebSocket'));
          return;
        }

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          resolve(true);
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WebSocketMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        this.ws.onclose = (event) => {
          console.log('WebSocket disconnected:', event.code, event.reason);
          this.isConnecting = false;
          this.ws = null;
          
          // Attempt to reconnect if not a clean close
          if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
            setTimeout(() => {
              this.reconnectAttempts++;
              this.connect(this.userId, this.matterId);
            }, this.reconnectDelay * Math.pow(2, this.reconnectAttempts));
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          this.isConnecting = false;
          reject(error);
        };

        // Timeout after 10 seconds
        setTimeout(() => {
          if (this.isConnecting) {
            this.isConnecting = false;
            reject(new Error('WebSocket connection timeout'));
          }
        }, 10000);
      });
    } catch (error) {
      this.isConnecting = false;
      console.error('Error connecting to WebSocket:', error);
      throw error;
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
  }

  /**
   * Send message to server
   */
  private sendMessage(message: WebSocketMessage): boolean {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('WebSocket not connected, cannot send message');
      return false;
    }

    try {
      this.ws.send(JSON.stringify(message));
      return true;
    } catch (error) {
      console.error('Error sending WebSocket message:', error);
      return false;
    }
  }

  /**
   * Join a document editing session
   */
  joinDocument(documentId: string, matterId: string): boolean {
    this.currentDocumentId = documentId;
    
    return this.sendMessage({
      type: MessageType.JOIN_DOCUMENT,
      payload: {
        document_id: documentId,
        matter_id: matterId,
      },
    });
  }

  /**
   * Leave a document editing session
   */
  leaveDocument(documentId: string): boolean {
    if (this.currentDocumentId === documentId) {
      this.currentDocumentId = undefined;
    }
    
    return this.sendMessage({
      type: MessageType.LEAVE_DOCUMENT,
      payload: {
        document_id: documentId,
      },
    });
  }

  /**
   * Send document edit
   */
  sendDocumentEdit(documentId: string, edit: Omit<DocumentEdit, 'user_id' | 'timestamp'>): boolean {
    return this.sendMessage({
      type: MessageType.DOCUMENT_EDIT,
      payload: {
        document_id: documentId,
        operation: edit.operation,
        position: edit.position,
        content: edit.content,
        length: edit.length || 0,
      },
    });
  }

  /**
   * Send cursor position update
   */
  sendCursorPosition(documentId: string, position: number, selectionStart?: number, selectionEnd?: number): boolean {
    return this.sendMessage({
      type: MessageType.CURSOR_POSITION,
      payload: {
        document_id: documentId,
        position,
        selection_start: selectionStart || position,
        selection_end: selectionEnd || position,
      },
    });
  }

  /**
   * Lock document for exclusive editing
   */
  lockDocument(documentId: string, lockDuration: number = 300): boolean {
    return this.sendMessage({
      type: MessageType.DOCUMENT_LOCK,
      payload: {
        document_id: documentId,
        lock_duration: lockDuration,
      },
    });
  }

  /**
   * Unlock document
   */
  unlockDocument(documentId: string): boolean {
    return this.sendMessage({
      type: MessageType.DOCUMENT_UNLOCK,
      payload: {
        document_id: documentId,
      },
    });
  }

  /**
   * Request document synchronization
   */
  requestSync(documentId: string): boolean {
    return this.sendMessage({
      type: MessageType.SYNC_REQUEST,
      payload: {
        document_id: documentId,
      },
    });
  }

  /**
   * Add message handler
   */
  onMessage(messageType: string, handler: MessageHandler): void {
    if (!this.messageHandlers.has(messageType)) {
      this.messageHandlers.set(messageType, []);
    }
    this.messageHandlers.get(messageType)!.push(handler);
  }

  /**
   * Remove message handler
   */
  offMessage(messageType: string, handler: MessageHandler): void {
    const handlers = this.messageHandlers.get(messageType);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  /**
   * Handle incoming message
   */
  private handleMessage(message: WebSocketMessage): void {
    const handlers = this.messageHandlers.get(message.type);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(message);
        } catch (error) {
          console.error('Error in message handler:', error);
        }
      });
    }

    // Handle system messages
    switch (message.type) {
      case MessageType.CONNECT:
        console.log('Connected to WebSocket server:', message.payload);
        break;
      case MessageType.ERROR:
        console.error('WebSocket error:', message.payload.error);
        break;
    }
  }

  /**
   * Get connection status
   */
  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  /**
   * Get current document ID
   */
  getCurrentDocumentId(): string | undefined {
    return this.currentDocumentId;
  }

  /**
   * Generate user ID (in real app, get from auth)
   */
  private generateUserId(): string {
    return `user_${Math.random().toString(36).substr(2, 9)}`;
  }
}

// Export singleton instance
export const websocketService = new WebSocketService();