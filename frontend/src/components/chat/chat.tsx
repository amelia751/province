"use client";

import React, { useState, useEffect } from "react";
import { cn } from "@/lib/utils";
import {
  Send,
  Paperclip,
  Mic,
  MoreHorizontal,
  User,
  Bot,
  Copy,
  ThumbsUp,
  ThumbsDown,
  RotateCcw
} from "lucide-react";

interface ChatProps {
  onWidthChange?: (width: number) => void;
}

interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

const mockMessages: ChatMessage[] = [
  {
    id: "1",
    type: "user",
    content: "Can you help me create a resizable sidebar component?",
    timestamp: new Date(Date.now() - 300000)
  },
  {
    id: "2",
    type: "assistant",
    content: "I'll help you create a resizable sidebar component. Here's a React component that includes drag-to-resize functionality:\n\n```tsx\nconst ResizableSidebar = () => {\n  const [width, setWidth] = useState(256);\n  // ... implementation\n};\n```\n\nThis component includes mouse event handlers for dragging and maintains the sidebar width state.",
    timestamp: new Date(Date.now() - 240000)
  },
  {
    id: "3",
    type: "user",
    content: "How can I make the resize handle more elegant?",
    timestamp: new Date(Date.now() - 120000)
  },
  {
    id: "4",
    type: "assistant",
    content: "To make the resize handle more elegant, you can:\n\n1. Make it thinner (1px instead of 2px)\n2. Use subtle colors (transparent by default, gray on hover)\n3. Add smooth transitions\n4. Remove thick backgrounds during dragging\n\nHere's the improved styling:\n\n```css\n.resize-handle {\n  width: 1px;\n  background: transparent;\n  transition: all 200ms;\n}\n\n.resize-handle:hover {\n  background: #9ca3af;\n}\n```",
    timestamp: new Date(Date.now() - 60000)
  }
];

const Chat: React.FC<ChatProps> = ({ onWidthChange }) => {
  const [messages, setMessages] = useState(mockMessages);
  const [inputValue, setInputValue] = useState("");



  const sendMessage = () => {
    if (!inputValue.trim()) return;
    
    const newMessage: ChatMessage = {
      id: Date.now().toString(),
      type: "user",
      content: inputValue,
      timestamp: new Date()
    };
    
    setMessages([...messages, newMessage]);
    setInputValue("");
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };



  return (
    <div className="chat-container flex bg-white h-full w-full">
      <div className="flex flex-col h-full flex-1">
        {/* Header */}
        <div className="flex items-center justify-between p-3 border-b border-gray-100">
          <h3 className="text-sm font-medium text-gray-900">Chat</h3>
          <div className="flex items-center space-x-1">
            <button className="p-1 hover:bg-gray-100 rounded">
              <RotateCcw className="h-4 w-4 text-gray-500" />
            </button>
            <button className="p-1 hover:bg-gray-100 rounded">
              <MoreHorizontal className="h-4 w-4 text-gray-500" />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                "flex space-x-3",
                message.type === 'user' ? "justify-end" : "justify-start"
              )}
            >
              {message.type === 'assistant' && (
                <div className="w-8 h-8 bg-black rounded-full flex items-center justify-center flex-shrink-0">
                  <Bot className="h-4 w-4 text-white" />
                </div>
              )}
              
              <div className={cn(
                "max-w-[80%] rounded-lg px-3 py-2",
                message.type === 'user' 
                  ? "bg-black text-white" 
                  : "bg-gray-100 text-gray-900"
              )}>
                <div className="text-sm whitespace-pre-wrap">{message.content}</div>
                <div className={cn(
                  "text-xs mt-1",
                  message.type === 'user' ? "text-gray-300" : "text-gray-500"
                )}>
                  {message.timestamp.toLocaleTimeString([], { 
                    hour: '2-digit', 
                    minute: '2-digit' 
                  })}
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
          ))}
        </div>

        {/* Input */}
        <div className="p-4 border-t border-gray-100">
          <div className="flex items-end space-x-2">
            <div className="flex-1 relative">
              <textarea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
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
                disabled={!inputValue.trim()}
                className={cn(
                  "p-2 rounded",
                  inputValue.trim()
                    ? "bg-black text-white hover:bg-gray-800"
                    : "bg-gray-100 text-gray-400 cursor-not-allowed"
                )}
              >
                <Send className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Chat;