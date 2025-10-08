"use client";

import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import { Room, RemoteTrack, RemoteTrackPublication, RemoteParticipant, ConnectionState, Track } from 'livekit-client';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'ai' | 'system';
  timestamp: Date;
  type?: 'text' | 'transcription' | 'system';
  isStreaming?: boolean;
}

interface LiveKitContextType {
  // Room state
  room: Room | null;
  isConnected: boolean;
  isConnecting: boolean;
  connectionState: ConnectionState;
  
  // Audio state
  isMuted: boolean;
  isListening: boolean;
  
  // Chat state
  chatMessages: Message[];
  isTextSending: boolean;
  isAgentTyping: boolean;
  
  // Actions
  connectToRoom: (agentName?: string) => Promise<void>;
  disconnectFromRoom: () => void;
  sendTextMessage: (message: string) => Promise<void>;
  toggleMute: () => Promise<void>;
  
  // Error state
  error: string | null;
}

const LiveKitContext = createContext<LiveKitContextType | undefined>(undefined);

interface LiveKitProviderProps {
  children: React.ReactNode;
}

export function LiveKitProvider({ children }: LiveKitProviderProps) {
  // Room state
  const [room, setRoom] = useState<Room | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectionState, setConnectionState] = useState<ConnectionState>(ConnectionState.Disconnected);
  
  // Audio state
  const [isMuted, setIsMuted] = useState(false);
  const [isListening, setIsListening] = useState(false);
  
  // Chat state
  const [chatMessages, setChatMessages] = useState<Message[]>([]);
  const [isTextSending, setIsTextSending] = useState(false);
  const [isAgentTyping, setIsAgentTyping] = useState(false);
  
  // Error state
  const [error, setError] = useState<string | null>(null);
  
  // Refs
  const roomRef = useRef<Room | null>(null);

  // Add log helper
  const addLog = useCallback((level: 'info' | 'error' | 'warning' | 'success', message: string, details?: string) => {
    const globalAddLog = (window as any).addMainEditorLog;
    if (globalAddLog) {
      globalAddLog(level, 'system', message, details);
    }
    console.log(`[LiveKit] ${level.toUpperCase()}: ${message}`, details || '');
  }, []);

  // Connect to room
  const connectToRoom = useCallback(async (agentName: string = 'TaxPlannerAgent') => {
    if (isConnecting || isConnected) return;
    
    setIsConnecting(true);
    setError(null);
    addLog('info', 'Starting voice connection', `Connecting to ${agentName}`);

    try {
      // Simulate connection for now - bypass LiveKit temporarily
      addLog('info', 'Simulating voice connection', 'Using fallback mode');
      
      // Simulate connection delay
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      setIsConnected(true);
      setIsConnecting(false);
      setConnectionState(ConnectionState.Connected);
      setIsListening(true);
      
      // Add welcome message
      setChatMessages(prev => [...prev, {
        id: Date.now().toString(),
        content: "Hello! I'm your tax assistant. Voice mode is temporarily in simulation mode. How can I help you with your taxes today?",
        sender: 'ai',
        timestamp: new Date(),
        type: 'text'
      }]);

      addLog('success', 'Voice connection established', 'Ready for voice interaction (simulation mode)');

    } catch (err) {
      addLog('error', 'Connection failed', err instanceof Error ? err.message : 'Failed to connect to voice service');
      setError(err instanceof Error ? err.message : 'Failed to connect to voice service');
      setIsConnecting(false);
      setConnectionState(ConnectionState.Disconnected);
    }
  }, [isConnecting, isConnected, addLog]);

  // Disconnect from room
  const disconnectFromRoom = useCallback(() => {
    if (roomRef.current) {
      addLog('info', 'Disconnecting from room', 'Ending voice chat session');
      roomRef.current.disconnect();
      roomRef.current = null;
    }
    setRoom(null);
    setIsConnected(false);
    setIsListening(false);
    setIsConnecting(false);
    setConnectionState(ConnectionState.Disconnected);
    setChatMessages([]);
    setError(null);
  }, [addLog]);

  // Send text message
  const sendTextMessage = useCallback(async (message: string) => {
    if (!room || !isConnected) return;
    
    setIsTextSending(true);
    
    // Add user message to chat
    const userMessage: Message = {
      id: Date.now().toString(),
      content: message,
      sender: 'user',
      timestamp: new Date(),
      type: 'text'
    };
    
    setChatMessages(prev => [...prev, userMessage]);
    
    try {
      // Send message via data channel
      const messageData = {
        type: 'chat',
        content: message,
        timestamp: new Date().toISOString()
      };
      
      const encoder = new TextEncoder();
      await room.localParticipant.publishData(encoder.encode(JSON.stringify(messageData)));
      
      setIsAgentTyping(true);
      addLog('info', 'Text message sent', message);
    } catch (error) {
      addLog('error', 'Failed to send message', error instanceof Error ? error.message : 'Unknown error');
      setError('Failed to send message');
    } finally {
      setIsTextSending(false);
    }
  }, [room, isConnected, addLog]);

  // Toggle mute
  const toggleMute = useCallback(async () => {
    if (!room || !room.localParticipant) return;
    
    try {
      const newMutedState = !isMuted;
      await room.localParticipant.setMicrophoneEnabled(!newMutedState);
      setIsMuted(newMutedState);
      setIsListening(!newMutedState);
      addLog('info', newMutedState ? 'Microphone muted' : 'Microphone unmuted', 'Microphone state changed');
    } catch (error) {
      addLog('error', 'Failed to toggle microphone', error instanceof Error ? error.message : 'Unknown error');
      setError('Failed to toggle microphone');
    }
  }, [room, isMuted, addLog]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (roomRef.current) {
        roomRef.current.disconnect();
      }
    };
  }, []);

  const contextValue: LiveKitContextType = {
    // Room state
    room,
    isConnected,
    isConnecting,
    connectionState,
    
    // Audio state
    isMuted,
    isListening,
    
    // Chat state
    chatMessages,
    isTextSending,
    isAgentTyping,
    
    // Actions
    connectToRoom,
    disconnectFromRoom,
    sendTextMessage,
    toggleMute,
    
    // Error state
    error,
  };

  return (
    <LiveKitContext.Provider value={contextValue}>
      {children}
    </LiveKitContext.Provider>
  );
}

export function useLiveKitContext() {
  const context = useContext(LiveKitContext);
  if (context === undefined) {
    throw new Error('useLiveKitContext must be used within a LiveKitProvider');
  }
  return context;
}
