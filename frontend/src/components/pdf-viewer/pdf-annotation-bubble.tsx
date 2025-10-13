"use client";

import React from 'react';
import { cn } from '@/lib/utils';
import { Info, CheckCircle, AlertCircle, HelpCircle } from 'lucide-react';

export interface AnnotationBubbleProps {
  title?: string;
  message: string;
  type?: 'info' | 'success' | 'warning' | 'help';
  pinCite?: string; // e.g., "From W-2 Acme, Box 1"
  className?: string;
}

export function PdfAnnotationBubble({
  title,
  message,
  type = 'info',
  pinCite,
  className
}: AnnotationBubbleProps) {
  const getIconAndColor = () => {
    switch (type) {
      case 'success':
        return {
          icon: <CheckCircle className="h-4 w-4" />,
          bg: 'bg-green-50 border-green-200',
          text: 'text-green-800',
          iconColor: 'text-green-600'
        };
      case 'warning':
        return {
          icon: <AlertCircle className="h-4 w-4" />,
          bg: 'bg-yellow-50 border-yellow-200',
          text: 'text-yellow-800',
          iconColor: 'text-yellow-600'
        };
      case 'help':
        return {
          icon: <HelpCircle className="h-4 w-4" />,
          bg: 'bg-purple-50 border-purple-200',
          text: 'text-purple-800',
          iconColor: 'text-purple-600'
        };
      default:
        return {
          icon: <Info className="h-4 w-4" />,
          bg: 'bg-blue-50 border-blue-200',
          text: 'text-blue-800',
          iconColor: 'text-blue-600'
        };
    }
  };

  const { icon, bg, text, iconColor } = getIconAndColor();

  return (
    <div
      className={cn(
        "rounded-lg border-2 shadow-lg max-w-xs",
        bg,
        className
      )}
    >
      {/* Header */}
      {title && (
        <div className="flex items-center space-x-2 px-3 py-2 border-b border-current/20">
          <div className={iconColor}>{icon}</div>
          <span className={cn("font-semibold text-sm", text)}>{title}</span>
        </div>
      )}

      {/* Body */}
      <div className="px-3 py-2">
        <p className={cn("text-sm", text)}>{message}</p>

        {/* Pin cite */}
        {pinCite && (
          <div className="mt-2 pt-2 border-t border-current/20">
            <p className={cn("text-xs font-medium", text, "opacity-70")}>
              📎 {pinCite}
            </p>
          </div>
        )}
      </div>

      {/* Arrow pointing down to the field */}
      <div
        className={cn(
          "absolute top-full left-4 w-0 h-0",
          "border-l-8 border-r-8 border-t-8",
          "border-l-transparent border-r-transparent",
          type === 'success' && "border-t-green-200",
          type === 'warning' && "border-t-yellow-200",
          type === 'help' && "border-t-purple-200",
          type === 'info' && "border-t-blue-200"
        )}
        style={{ marginTop: '-1px' }}
      />
    </div>
  );
}

export default PdfAnnotationBubble;
