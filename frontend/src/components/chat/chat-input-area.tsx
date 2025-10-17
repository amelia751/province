import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Mic, Keyboard, FileText, Send, Image, ChevronDown, MessageSquare, Calculator, FileCheck, FileInput, Search, BarChart3, Upload, X } from 'lucide-react';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface ChatInputAreaProps {
    hasReceivedFirstResponse: boolean;
    isConnected?: boolean;
    isContextSwitching?: boolean;
    isTextSending?: boolean;
    inputValue?: string;
    setInputValue?: (value: string) => void;
    handleSendMessage?: () => void;
    handleKeyPress?: (e: React.KeyboardEvent) => void;
    engagementId?: string;
}

const ChatInputArea: React.FC<ChatInputAreaProps> = ({
    hasReceivedFirstResponse,
    isConnected = true,
    isContextSwitching = false,
    isTextSending = false,
    inputValue = '',
    setInputValue = () => { },
    handleSendMessage = () => { },
    handleKeyPress = () => { },
    engagementId
}) => {
    const [inputMode, setInputMode] = useState<'voice' | 'text'>('voice');
    const [isConnecting, setIsConnecting] = useState(false);
    const [isListening, setIsListening] = useState(false);
    const [isMuted, setIsMuted] = useState(false);
    const [selectedMode, setSelectedMode] = useState<'ask' | 'agents'>('agents');
    const [isDragging, setIsDragging] = useState(false);
    const [uploadingFiles, setUploadingFiles] = useState<File[]>([]);
    const [isUploading, setIsUploading] = useState(false);
    const inputRef = useRef<HTMLInputElement>(null);

    const modes = [
        { id: 'ask', name: 'Ask', description: 'General conversation', Icon: MessageSquare, shortcut: '⌘K' },
        { id: 'agents', name: 'Agents', description: 'AI tax agents', icon: '∞', shortcut: '⌘I' },
    ];

    useEffect(() => {
        if (hasReceivedFirstResponse) {
            setIsListening(isConnected);
        }
    }, [isConnected, hasReceivedFirstResponse]);

    const triggerMute = () => {
        setIsListening(!isListening);
        setIsMuted((prev) => !prev);
    }

    const handleMicClick = async () => {
        if (!isConnected) {
            setIsConnecting(true);
            // Simulate connection
            setTimeout(() => {
                setIsConnecting(false);
            }, 1000);
        }
        triggerMute();
    };

    const handleKeyboardClick = () => {
        setInputMode('text');
        setTimeout(() => {
            inputRef.current?.focus();
        }, 100);
        if (!isMuted) {
            triggerMute()
        }
    };

    const isInputDisabled = !isConnected;

    // Drag and drop handlers
    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);
    }, []);

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setIsDragging(false);

        const files = Array.from(e.dataTransfer.files);
        if (files.length > 0 && engagementId) {
            handleFileUpload(files);
        }
    }, [engagementId]);

    const handleFileUpload = async (files: File[]) => {
        if (!engagementId) {
            console.error('No engagement ID available for file upload');
            return;
        }

        setUploadingFiles(files);
        setIsUploading(true);

        try {
            for (const file of files) {
                const formData = new FormData();
                formData.append('file', file);
                formData.append('engagementId', engagementId);
                formData.append('documentPath', `chat-uploads/${file.name}`);

                const response = await fetch('/api/documents/upload', {
                    method: 'POST',
                    body: formData,
                });

                if (!response.ok) {
                    throw new Error(`Upload failed for ${file.name}`);
                }

                const result = await response.json();
                console.log(`Successfully uploaded ${file.name}:`, result);
                
                // Add a message to the chat about the uploaded file
                const uploadMessage = `📎 Uploaded: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
                setInputValue(prev => prev ? `${prev}\n${uploadMessage}` : uploadMessage);
            }
        } catch (error) {
            console.error('File upload error:', error);
            // You could add a toast notification here
        } finally {
            setIsUploading(false);
            setUploadingFiles([]);
        }
    };

    // Keep focus on input only when switching to text mode
    useEffect(() => {
        if (inputRef.current && inputMode === 'text') {
            // Only focus when explicitly switching to text mode, not on every render
            const timer = setTimeout(() => {
                inputRef.current?.focus();
            }, 100);
            return () => clearTimeout(timer);
        }
    }, [inputMode]);

    // Global key handler → keyboard shortcuts and focus management
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            // Check for mode switching shortcuts (⌘K for Ask, ⌘I for Agents)
            if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
                e.preventDefault();
                setSelectedMode('ask');
                return;
            }

            if ((e.metaKey || e.ctrlKey) && e.key === 'i') {
                e.preventDefault();
                setSelectedMode('agents');
                return;
            }

            // ignore if typing inside a textarea/input already
            if (
                document.activeElement &&
                (document.activeElement.tagName === "INPUT" ||
                    document.activeElement.tagName === "TEXTAREA" ||
                    (document.activeElement as HTMLElement).isContentEditable)
            ) {
                return;
            }

            // ignore if user has text selected (they might be trying to copy)
            const selection = window.getSelection();
            if (selection && selection.toString().length > 0) {
                return;
            }

            // Don't auto-focus - let users explicitly click into the input
            // This prevents interference with text selection in chat messages
            // if (inputRef.current && inputMode === 'text') {
            //     inputRef.current.focus();
            // }
        };

        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, [inputMode]);

    const currentMode = modes.find(m => m.id === selectedMode) || modes[0];

    return (
        <div className="flex-shrink-0 p-4 bg-transparent" data-tour="mic-button">
            <div className="max-w-4xl mx-auto">
                {inputMode === 'voice' ? (
                    // Voice Mode Layout
                    <div className="flex flex-col items-center space-y-4">
                        {/* Voice Controls Row */}
                        <div className="flex items-center space-x-6">
                            {/* Documents Button */}
                            <button
                                className="p-3 rounded-full border-2 transition-all duration-200 hover:shadow-md border-gray-300 hover:border-gray-400 disabled:opacity-50 disabled:cursor-not-allowed"
                                title="Documents"
                            >
                                <FileText className="h-5 w-5 text-gray-600" />
                            </button>

                            {/* Main Mic Button with Animation */}
                            <div className="relative">
                                <button
                                    onClick={handleMicClick}
                                    disabled={isInputDisabled || isConnecting}
                                    className={`relative p-6 rounded-full bg-black transition-all duration-300 flex items-center justify-center overflow-hidden ${isListening
                                        ? " hover:bg-gray-700 shadow-lg scale-110"
                                        : " hover:bg-gray-800 shadow-md"
                                        } disabled:opacity-50 disabled:cursor-not-allowed`}
                                    title={isListening ? "Stop listening" : "Start voice input"}
                                >
                                    {isConnecting ? (
                                        <div className="h-6 w-6 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                    ) : !isListening ? (
                                        <Mic className="h-6 w-6 text-white" />
                                    ) : (
                                        <div className="flex items-center h-4 mt-0.5">
                                            <div className="w-[2px] h-[18px] bg-gray-300 mr-[2px] rounded-sm animate-equalizer [animation-delay:0s]" />
                                            <div className="w-[2px] h-[18px] bg-gray-300 mr-[2px] rounded-sm animate-equalizer [animation-delay:0.2s]" />
                                            <div className="w-[2px] h-[18px] bg-gray-300 mr-[2px] rounded-sm animate-equalizer [animation-delay:0.4s]" />
                                            <div className="w-[2px] h-[18px] bg-gray-300 mr-[2px] rounded-sm animate-equalizer [animation-delay:0.6s]" />
                                        </div>
                                    )}
                                </button>
                            </div>

                            {/* Keyboard Button */}
                            <button
                                onClick={handleKeyboardClick}
                                disabled={isInputDisabled}
                                className="p-3 rounded-full bg-white border-2 border-gray-300 hover:border-gray-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 hover:shadow-md"
                                title="Switch to keyboard input"
                            >
                                <Keyboard className="h-5 w-5 text-gray-600" />
                            </button>
                        </div>
                    </div>
                ) : (
                    // Text Mode Layout - Cursor-style with shadcn
                    <div className="space-y-2">
                        {/* Top row: Mode/Agent selector and action buttons */}
                        <div className="flex items-center justify-between px-1">
                            {/* Left: Mode/Agent selector with dropdown */}
                            <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                    <button className="flex items-center gap-1.5 px-2 py-1 rounded-md hover:bg-gray-100 transition-colors text-xs text-gray-600 hover:text-black">
                                        {currentMode.id === 'agents' ? (
                                            <span className="text-sm">{currentMode.icon}</span>
                                        ) : (
                                            <currentMode.Icon className="h-3.5 w-3.5" />
                                        )}
                                        <span>{currentMode.name}</span>
                                        <span className="text-[10px] bg-gray-100 px-1 py-0.5 rounded">{currentMode.shortcut}</span>
                                        <ChevronDown className="h-3 w-3" />
                                    </button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="start" className="w-48">
                                    {modes.map((mode) => (
                                        <DropdownMenuItem
                                            key={mode.id}
                                            onClick={() => setSelectedMode(mode.id as 'ask' | 'agents')}
                                            className="text-xs"
                                        >
                                            {mode.id === 'agents' ? (
                                                <span className="text-sm">{mode.icon}</span>
                                            ) : (
                                                <mode.Icon className="h-3.5 w-3.5" />
                                            )}
                                            <div className="flex-1">
                                                <div className="font-medium">{mode.name}</div>
                                                <div className="text-[10px] text-muted-foreground">{mode.description}</div>
                                            </div>
                                            <span className="text-[10px] text-muted-foreground">{mode.shortcut}</span>
                                            {selectedMode === mode.id && (
                                                <div className="w-1.5 h-1.5 rounded-full bg-black"></div>
                                            )}
                                        </DropdownMenuItem>
                                    ))}
                                </DropdownMenuContent>
                            </DropdownMenu>

                            {/* Right: Action buttons */}
                            <div className="flex items-center gap-0.5">
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    className="h-6 w-6 p-0"
                                    title="Attach image"
                                >
                                    <Image className="h-3.5 w-3.5" />
                                </Button>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    className="h-6 w-6 p-0"
                                    onClick={() => {
                                        setInputMode('voice');
                                        triggerMute();
                                    }}
                                    disabled={isInputDisabled}
                                    title="Switch to voice input"
                                >
                                    <Mic className="h-3.5 w-3.5" />
                                </Button>
                            </div>
                        </div>

                        {/* Text input area */}
                        <div 
                            className={`relative ${isDragging ? 'ring-2 ring-blue-500 ring-opacity-50' : ''}`}
                            onDragOver={handleDragOver}
                            onDragLeave={handleDragLeave}
                            onDrop={handleDrop}
                        >
                            <Textarea
                                ref={inputRef as any}
                                value={inputValue}
                                onChange={(e) => setInputValue(e.target.value)}
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter' && !e.shiftKey) {
                                        e.preventDefault();
                                        handleSendMessage();
                                    }
                                }}
                                placeholder={
                                    isDragging
                                        ? "Drop files here to upload..."
                                        : !isConnected
                                        ? "Connect to tax assistant to start chatting..."
                                        : selectedMode === 'ask'
                                            ? "Ask me anything... (or drag & drop files)"
                                            : "Ask your tax agents... (or drag & drop files)"
                                }
                                className={`min-h-[52px] max-h-[200px] pr-12 resize-none transition-all ${
                                    isDragging ? 'border-blue-500 bg-blue-50' : ''
                                }`}
                                disabled={isTextSending || isInputDisabled || isUploading}
                                data-tour="chat-input"
                            />

                            {/* Upload indicator */}
                            {isUploading && (
                                <div className="absolute inset-0 bg-blue-50 bg-opacity-90 flex items-center justify-center rounded-md">
                                    <div className="flex items-center space-x-2 text-blue-600">
                                        <Upload className="h-4 w-4 animate-pulse" />
                                        <span className="text-sm">Uploading {uploadingFiles.length} file(s)...</span>
                                    </div>
                                </div>
                            )}

                            {/* Send button - bottom right of textarea */}
                            <Button
                                onClick={handleSendMessage}
                                disabled={!inputValue.trim() || isInputDisabled}
                                size="sm"
                                className="absolute right-2 bottom-2 h-8 w-8 p-0 bg-black hover:bg-gray-800"
                                title="Send message"
                            >
                                <Send className="h-4 w-4" />
                            </Button>
                        </div>
                    </div>
                )}

                {/* Connection Status (shown in text mode) */}
                {inputMode === 'text' && !isConnected && (
                    <p className="text-xs text-gray-500 mt-2 text-center">
                        Use the voice interaction panel to talk to your tax assistant
                    </p>
                )}
            </div>
        </div>
    );
};

export default ChatInputArea;
