"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import { cn } from "@/lib/utils";
import {
  Mic,
  MicOff,
  Phone,
  PhoneOff,
  Volume2,
  VolumeX,
  Loader2,
  AlertCircle,
  Wifi,
  WifiOff,
} from "lucide-react";
import { Room, RemoteTrack, RemoteTrackPublication, RemoteParticipant } from "livekit-client";
import { ConnectionState, Track } from "livekit-client";

interface VoiceChatProps {
  selectedAgent: string;
  onDocumentCreate?: (document: any) => void;
  onMatterCreate?: (matter: any) => void;
  onDeadlineCreate?: (deadline: any) => void;
}

interface TranscriptMessage {
  id: string;
  type: 'user' | 'assistant';
  text: string;
  timestamp: Date;
}

const VoiceChat: React.FC<VoiceChatProps> = ({
  selectedAgent,
  onDocumentCreate,
  onMatterCreate,
  onDeadlineCreate,
}) => {
  const [isConnecting, setIsConnecting] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isSpeakerMuted, setIsSpeakerMuted] = useState(false);
  const [transcript, setTranscript] = useState<TranscriptMessage[]>([]);
  const [isAgentSpeaking, setIsAgentSpeaking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const transcriptEndRef = useRef<HTMLDivElement>(null);
  const roomRef = useRef<Room | null>(null);
  const [connectionState, setConnectionState] = useState<ConnectionState>(ConnectionState.Disconnected);

  // Auto-scroll transcript
  useEffect(() => {
    transcriptEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [transcript]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (roomRef.current) {
        roomRef.current.disconnect();
      }
    };
  }, []);

  const handleConnect = useCallback(async () => {
    setIsConnecting(true);
    setError(null);

    try {
      // 1. Get token from backend (updated path)
      const response = await fetch('http://localhost:8000/api/v1/livekit/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          room_name: `tax-session-${Date.now()}`,
          participant_identity: 'user-' + Math.random().toString(36).substr(2, 9),
          participant_name: 'Tax Client',
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Failed to get access token');
      }

      const { token, url } = await response.json();

      // 2. Create and connect to LiveKit room
      const room = new Room({
        adaptiveStream: true,
        dynacast: true,
      });

      roomRef.current = room;

      // Set up event listeners
      room.on('connected', async () => {
        console.log('Connected to LiveKit room');
        setIsConnected(true);
        setIsConnecting(false);
        setConnectionState(ConnectionState.Connected);
        addTranscript('assistant', 'Hello! I\'m your tax assistant. How can I help you with your taxes today?');

        // Enable microphone after connection
        try {
          await room.localParticipant.setMicrophoneEnabled(true);
        } catch (error) {
          console.error('Failed to enable microphone:', error);
          setError('Failed to access microphone. Please check permissions.');
        }
      });

      room.on('disconnected', () => {
        console.log('Disconnected from LiveKit room');
        setIsConnected(false);
        setConnectionState(ConnectionState.Disconnected);
      });

      room.on('trackSubscribed', (track: RemoteTrack, publication: RemoteTrackPublication, participant: RemoteParticipant) => {
        if (track.kind === Track.Kind.Audio) {
          console.log('Audio track received from participant:', participant.identity);
          setIsAgentSpeaking(true);

          // Attach audio track to audio element for playback
          const audioElement = document.createElement('audio');
          audioElement.autoplay = true;
          audioElement.muted = isSpeakerMuted;
          track.attach(audioElement);

          // Add to DOM
          document.body.appendChild(audioElement);
        }
      });

      room.on('trackUnsubscribed', (track: RemoteTrack) => {
        if (track.kind === Track.Kind.Audio) {
          setIsAgentSpeaking(false);
          // Detach and remove audio elements
          track.detach();
        }
      });

      // Listen for data messages (transcriptions, etc.)
      room.on('dataReceived', (payload: Uint8Array, participant?: RemoteParticipant) => {
        try {
          const decoder = new TextDecoder();
          const message = JSON.parse(decoder.decode(payload));

          if (message.type === 'transcript') {
            const senderType = participant?.identity.includes('agent') ? 'assistant' : 'user';
            addTranscript(senderType, message.text);
          }
        } catch (error) {
          console.error('Failed to parse data message:', error);
        }
      });

      room.on('connectionStateChanged', (state: ConnectionState) => {
        setConnectionState(state);
        if (state === ConnectionState.Reconnecting) {
          setError('Connection lost, reconnecting...');
        } else if (state === ConnectionState.Connected) {
          setError(null);
        }
      });

      // Connect to room
      await room.connect(url, token);

    } catch (err) {
      console.error('Connection error:', err);
      setError(err instanceof Error ? err.message : 'Failed to connect to voice service');
      setIsConnecting(false);
      setConnectionState(ConnectionState.Disconnected);
    }
  }, [isSpeakerMuted]);

  const handleDisconnect = useCallback(() => {
    if (roomRef.current) {
      roomRef.current.disconnect();
      roomRef.current = null;
    }
    setIsConnected(false);
    setTranscript([]);
    setError(null);
    setConnectionState(ConnectionState.Disconnected);
  }, []);

  const toggleMute = useCallback(async () => {
    if (roomRef.current) {
      const audioTrack = roomRef.current.localParticipant.getTrackPublication(Track.Source.Microphone);
      if (audioTrack) {
        await audioTrack.setMuted(!isMuted);
        setIsMuted(!isMuted);
      } else {
        // Enable microphone if not already enabled
        try {
          await roomRef.current.localParticipant.setMicrophoneEnabled(!isMuted);
          setIsMuted(!isMuted);
        } catch (error) {
          console.error('Failed to toggle microphone:', error);
          setError('Failed to access microphone');
        }
      }
    }
  }, [isMuted]);

  const toggleSpeaker = useCallback(() => {
    setIsSpeakerMuted(prev => {
      const newMuted = !prev;
      // Update all audio elements
      const audioElements = document.querySelectorAll('audio');
      audioElements.forEach(audio => {
        audio.muted = newMuted;
      });
      return newMuted;
    });
  }, []);

  const addTranscript = useCallback((type: 'user' | 'assistant', text: string) => {
    setTranscript(prev => [
      ...prev,
      {
        id: `${type}_${Date.now()}`,
        type,
        text,
        timestamp: new Date(),
      },
    ]);
  }, []);

  return (
    <div className="flex flex-col h-full">
      {!isConnected ? (
        /* Connection Screen */
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="text-center max-w-md">
            <div className="mb-6">
              <div className="w-20 h-20 bg-black rounded-full mx-auto flex items-center justify-center mb-4">
                <Mic className="h-10 w-10 text-white" />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Voice Tax Assistant
              </h3>
              <p className="text-sm text-gray-500">
                Start a voice conversation with your AI tax assistant. Speak naturally and get instant responses.
              </p>
            </div>

            {error && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
                <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />
                <div className="text-sm text-red-800 text-left">
                  {error}
                </div>
              </div>
            )}

            <button
              onClick={handleConnect}
              disabled={isConnecting}
              className={cn(
                "px-6 py-3 rounded-lg font-medium transition-colors inline-flex items-center gap-2",
                isConnecting
                  ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                  : "bg-black text-white hover:bg-gray-800"
              )}
            >
              {isConnecting ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  Connecting...
                </>
              ) : (
                <>
                  <Mic className="h-5 w-5" />
                  Start Voice Session
                </>
              )}
            </button>

            <div className="mt-6 text-xs text-gray-500">
              <p>Microphone access required</p>
            </div>
          </div>
        </div>
      ) : (
        /* Active Voice Chat */
        <>
          {/* Connection Status */}
          <div className="px-4 py-2 bg-white border-b border-gray-200 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1.5">
                <div className={cn(
                  "w-2 h-2 rounded-full",
                  connectionState === ConnectionState.Connected ? "bg-green-500 animate-pulse" :
                  connectionState === ConnectionState.Reconnecting ? "bg-yellow-500 animate-pulse" :
                  "bg-gray-400"
                )} />
                <span className="text-xs font-medium text-gray-700">
                  {connectionState === ConnectionState.Connected ? 'Connected' :
                   connectionState === ConnectionState.Reconnecting ? 'Reconnecting...' :
                   'Connecting...'}
                </span>
              </div>
            </div>
            <div className="text-xs text-gray-500">
              Tax Assistant
            </div>
          </div>

          {/* Transcript */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {transcript.length === 0 ? (
              <div className="flex items-center justify-center h-full text-gray-400">
                <div className="text-center">
                  <Mic className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">Transcript will appear here...</p>
                </div>
              </div>
            ) : (
              transcript.map((message) => (
                <div
                  key={message.id}
                  className={cn(
                    "flex",
                    message.type === 'user' ? "justify-end" : "justify-start"
                  )}
                >
                  <div
                    className={cn(
                      "max-w-[80%] rounded-lg px-3 py-2",
                      message.type === 'user'
                        ? "bg-black text-white"
                        : "bg-gray-100 text-gray-900"
                    )}
                  >
                    <div className="text-sm">{message.text}</div>
                    <div
                      className={cn(
                        "text-xs mt-1",
                        message.type === 'user' ? "text-gray-300" : "text-gray-500"
                      )}
                    >
                      {message.timestamp.toLocaleTimeString([], {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </div>
                  </div>
                </div>
              ))
            )}
            <div ref={transcriptEndRef} />
          </div>

          {/* Agent Speaking Indicator */}
          {isAgentSpeaking && (
            <div className="px-4 py-2 bg-gray-50 border-t border-gray-200">
              <div className="flex items-center gap-2 text-sm text-gray-700">
                <div className="flex gap-1">
                  <div className="w-1.5 h-1.5 bg-black rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-1.5 h-1.5 bg-black rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-1.5 h-1.5 bg-black rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
                Assistant is speaking...
              </div>
            </div>
          )}

          {/* Controls */}
          <div className="p-6 border-t border-gray-200 bg-white">
            <div className="flex items-center justify-center gap-4">
              {/* Mute Microphone */}
              <button
                onClick={toggleMute}
                className={cn(
                  "p-4 rounded-full transition-all",
                  isMuted
                    ? "bg-red-500 text-white hover:bg-red-600"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                )}
                title={isMuted ? "Unmute microphone" : "Mute microphone"}
              >
                {isMuted ? (
                  <MicOff className="h-6 w-6" />
                ) : (
                  <Mic className="h-6 w-6" />
                )}
              </button>

              {/* End Call */}
              <button
                onClick={handleDisconnect}
                className="p-5 bg-red-500 text-white rounded-full hover:bg-red-600 transition-all shadow-lg"
                title="End conversation"
              >
                <PhoneOff className="h-7 w-7" />
              </button>

              {/* Mute Speaker */}
              <button
                onClick={toggleSpeaker}
                className={cn(
                  "p-4 rounded-full transition-all",
                  isSpeakerMuted
                    ? "bg-red-500 text-white hover:bg-red-600"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                )}
                title={isSpeakerMuted ? "Unmute speaker" : "Mute speaker"}
              >
                {isSpeakerMuted ? (
                  <VolumeX className="h-6 w-6" />
                ) : (
                  <Volume2 className="h-6 w-6" />
                )}
              </button>
            </div>

            <div className="mt-4 text-center">
              <p className="text-xs text-gray-500">
                Speak naturally about your tax questions
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default VoiceChat;
