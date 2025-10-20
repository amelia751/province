"use client";

import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { ExternalLink, Download } from 'lucide-react';

export interface PdfAnnotation {
  page: number;
  bbox: { x: number; y: number; w: number; h: number };
  content: React.ReactNode;
  id: string;
}

interface PdfViewerProps {
  url: string;
  annotations?: PdfAnnotation[];
  className?: string;
  onPageChange?: (page: number) => void;
}

export default function PdfViewer({ url, annotations = [], className, onPageChange }: PdfViewerProps) {
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const handleLoad = () => {
    setLoading(false);
    setError(null);
  };

  const handleError = () => {
    setLoading(false);
    setError('Failed to load PDF. The file may be corrupted or unavailable.');
  };

  if (error) {
    return (
      <div className={cn("flex flex-col items-center justify-center h-96 bg-red-50 rounded-lg border border-red-200", className)}>
        <div className="text-center p-6">
          <div className="text-red-600 mb-4">
            <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h3 className="text-lg font-medium text-red-800 mb-2">Error Loading PDF</h3>
          <p className="text-sm text-red-600 mb-4">{error}</p>
          <div className="flex gap-2 justify-center">
            <a
              href={url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center px-4 py-2 bg-paper-white text-gray-600 rounded hover:bg-true-turquoise hover:text-white transition-colors"
            >
              <ExternalLink className="w-4 h-4 mr-2" />
              Open in New Tab
            </a>
            <a
              href={url}
              download
              className="inline-flex items-center px-4 py-2 bg-true-turquoise text-white rounded hover:bg-true-turquoise/90 transition-colors"
            >
              <Download className="w-4 h-4 mr-2" />
              Download
            </a>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("flex flex-col bg-white rounded-lg shadow-sm border", className)}>
      {/* Toolbar */}
      <div className="flex items-center justify-between p-4 border-b bg-gray-50">
        <div className="flex items-center space-x-2">
          <h3 className="text-sm font-medium text-gray-700">PDF Document</h3>
        </div>
        <div className="flex items-center space-x-2">
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center px-3 py-1.5 text-sm bg-paper-white text-gray-600 rounded hover:bg-true-turquoise hover:text-white transition-colors"
          >
            <ExternalLink className="w-4 h-4 mr-1" />
            Open
          </a>
          <a
            href={url}
            download
            className="inline-flex items-center px-3 py-1.5 text-sm bg-true-turquoise text-white rounded hover:bg-true-turquoise/90 transition-colors"
          >
            <Download className="w-4 h-4 mr-1" />
            Download
          </a>
        </div>
      </div>

      {/* PDF Content */}
      <div className="flex-1 relative">
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-50 z-10">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
              <p className="text-sm text-gray-600">Loading PDF...</p>
            </div>
          </div>
        )}
        
        <iframe
          src={url}
          className="w-full h-96 border-0"
          onLoad={handleLoad}
          onError={handleError}
          title="PDF Document"
        />
      </div>
    </div>
  );
}