import React, { useEffect, useRef, useState } from 'react';
import { Mic, Keyboard, FileText, Send } from 'lucide-react';

interface ChatInputAreaProps {
    hasReceivedFirstResponse: boolean;
    isConnected?: boolean;
    isContextSwitching?: boolean;
    isTextSending?: boolean;
    inputValue?: string;
    setInputValue?: (value: string) => void;
    handleSendMessage?: () => void;
    handleKeyPress?: (e: React.KeyboardEvent) => void;
}

const ChatInputArea: React.FC<ChatInputAreaProps> = ({
    hasReceivedFirstResponse,
    isConnected = true,
    isContextSwitching = false,
    isTextSending = false,
    inputValue = '',
    setInputValue = () => { },
    handleSendMessage = () => { },
    handleKeyPress = () => { }
}) => {
    const [inputMode, setInputMode] = useState<'voice' | 'text'>('voice');
    const [isConnecting, setIsConnecting] = useState(false);
    const [isListening, setIsListening] = useState(false);
    const [isMuted, setIsMuted] = useState(false);
    const inputRef = useRef<HTMLInputElement>(null);

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

    // Keep focus on input
    useEffect(() => {
        if (inputRef.current && inputMode === 'text') {
            inputRef.current?.focus();
        }
    }, [inputMode]);

    // Global key handler → always redirect typing into input
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            // ignore if typing inside a textarea/input already
            if (
                document.activeElement &&
                (document.activeElement.tagName === "INPUT" ||
                    document.activeElement.tagName === "TEXTAREA" ||
                    (document.activeElement as HTMLElement).isContentEditable)
            ) {
                return;
            }

            if (inputRef.current && inputMode === 'text') {
                inputRef.current.focus();
            }
        };

        window.addEventListener("keydown", handleKeyDown);
        return () => window.removeEventListener("keydown", handleKeyDown);
    }, [inputMode]);

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
                                className="p-3 rounded-full border-2 transition-all duration-200 hover:shadow-md border-slate-300 hover:border-slate-400 disabled:opacity-50 disabled:cursor-not-allowed"
                                title="Documents"
                            >
                                <FileText className="h-5 w-5 text-slate-600" />
                            </button>

                            {/* Main Mic Button with Animation */}
                            <div className="relative">
                                <button
                                    onClick={handleMicClick}
                                    disabled={isInputDisabled || isConnecting}
                                    className={`relative p-6 rounded-full bg-[#278EFF] transition-all duration-300 flex items-center justify-center overflow-hidden ${isListening
                                        ? " hover:bg-blue-400 shadow-lg scale-110"
                                        : " hover:bg-blue-500 shadow-md"
                                        } disabled:opacity-50 disabled:cursor-not-allowed`}
                                    title={isListening ? "Stop listening" : "Start voice input"}
                                >
                                    {isConnecting ? (
                                        <div className="h-6 w-6 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                    ) : !isListening ? (
                                        <Mic className="h-6 w-6 text-white" />
                                    ) : (
                                        <div className="flex items-center h-4 mt-0.5">
                                            <div className="w-[2px] h-[18px] bg-green-300 mr-[2px] rounded-sm animate-equalizer [animation-delay:0s]" />
                                            <div className="w-[2px] h-[18px] bg-green-300 mr-[2px] rounded-sm animate-equalizer [animation-delay:0.2s]" />
                                            <div className="w-[2px] h-[18px] bg-green-300 mr-[2px] rounded-sm animate-equalizer [animation-delay:0.4s]" />
                                            <div className="w-[2px] h-[18px] bg-green-300 mr-[2px] rounded-sm animate-equalizer [animation-delay:0.6s]" />
                                        </div>
                                    )}
                                </button>
                            </div>

                            {/* Keyboard Button */}
                            <button
                                onClick={handleKeyboardClick}
                                disabled={isInputDisabled}
                                className="p-3 rounded-full bg-white border-2 border-slate-300 hover:border-slate-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 hover:shadow-md"
                                title="Switch to keyboard input"
                            >
                                <Keyboard className="h-5 w-5 text-slate-600" />
                            </button>
                        </div>
                    </div>
                ) : (
                    // Text Mode Layout
                    <div className="space-x-2">
                        <div className="flex m-1 space-x-1 w-full items-center">
                            {/* Mic Button (Left Side) */}
                            <button
                                onClick={() => {
                                    setInputMode('voice');
                                    triggerMute();
                                }}
                                disabled={isInputDisabled}
                                className="w-12 h-12 flex items-center justify-center bg-[#278EFF] hover:bg-blue-700 rounded-full text-white transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                                title="Switch to voice input"
                            >
                                <Mic className="h-7 w-5" />
                            </button>
                            {/* Text Input */}
                            <input
                                ref={inputRef}
                                value={inputValue}
                                onChange={(e) => setInputValue(e.target.value)}
                                onKeyPress={handleKeyPress}
                                placeholder={
                                    !isConnected
                                        ? "Connect to tax assistant to start chatting..."
                                        : "Ask me anything about filing your taxes..."
                                }
                                className="flex-1 px-4 py-2 border border-slate-300 rounded-full 
                                focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 
                                disabled:bg-slate-100 disabled:cursor-not-allowed 
                                placeholder:text-sm placeholder:text-gray-400"
                                readOnly={isInputDisabled}
                                disabled={isTextSending}
                                data-tour="chat-input"
                            />

                            {/* Send Button */}
                            <button
                                onClick={handleSendMessage}
                                disabled={!inputValue.trim() || isInputDisabled}
                                className="w-12 h-12 flex items-center justify-center bg-blue-600 hover:bg-blue-700 rounded-full text-white transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                                title="Send message"
                            >
                                <Send className="h-5 w-5" />
                            </button>
                        </div>
                    </div>
                )}

                {/* Connection Status (shown in text mode) */}
                {inputMode === 'text' && !isConnected && (
                    <p className="text-xs text-slate-500 mt-2 text-center">
                        Use the voice interaction panel to talk to your tax assistant
                    </p>
                )}
            </div>
        </div>
    );
};

export default ChatInputArea;
