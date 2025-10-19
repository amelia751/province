"use client";

import React, { useState, useEffect } from 'react';
import { ChevronUp, ChevronDown, Clock, FileText } from 'lucide-react';
import { PdfViewer } from '@/components/pdf-viewer';
import { cn } from '@/lib/utils';

interface FormVersion {
  version: string;
  version_number: number;
  s3_key: string;
  size: number;
  timestamp: string;
  last_modified: string;
  download_url: string;
}

interface FormVersionsData {
  engagement_id: string;
  form_type: string;
  tax_year: number;
  total_versions: number;
  versions: FormVersion[];
  latest_version: string;
}

interface Form1040ViewerProps {
  engagementId: string;
  className?: string;
}

export function Form1040Viewer({ engagementId, className }: Form1040ViewerProps) {
  const [versionsData, setVersionsData] = useState<FormVersionsData | null>(null);
  const [currentVersionIndex, setCurrentVersionIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showTooltip, setShowTooltip] = useState(false);

  // Load versions on mount
  useEffect(() => {
    loadVersions();
  }, [engagementId]);

  const loadVersions = async () => {
    try {
      setLoading(true);
      setError(null);

      const response = await fetch(
        `/api/forms/1040/${engagementId}/versions?tax_year=2024`
      );

      if (!response.ok) {
        throw new Error(`Failed to load form versions: ${response.statusText}`);
      }

      const data: FormVersionsData = await response.json();
      setVersionsData(data);
      setCurrentVersionIndex(0); // Start with latest version
    } catch (err) {
      console.error('Error loading form versions:', err);
      setError(err instanceof Error ? err.message : 'Failed to load form versions');
    } finally {
      setLoading(false);
    }
  };

  const goToNextVersion = () => {
    if (versionsData && currentVersionIndex < versionsData.versions.length - 1) {
      setCurrentVersionIndex(currentVersionIndex + 1);
    }
  };

  const goToPreviousVersion = () => {
    if (currentVersionIndex > 0) {
      setCurrentVersionIndex(currentVersionIndex - 1);
    }
  };

  const currentVersion = versionsData?.versions[currentVersionIndex];
  const isLatest = currentVersionIndex === 0;
  const isOldest = versionsData && currentVersionIndex === versionsData.versions.length - 1;

  if (loading) {
    return (
      <div className={cn("flex items-center justify-center h-full bg-gray-50", className)}>
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
          <p className="text-sm text-gray-600">Loading form versions...</p>
        </div>
      </div>
    );
  }

  if (error || !versionsData || !currentVersion) {
    return (
      <div className={cn("flex items-center justify-center h-full bg-red-50", className)}>
        <div className="text-center p-6">
          <FileText className="w-12 h-12 text-red-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-red-800 mb-2">No Form Versions Found</h3>
          <p className="text-sm text-red-600">
            {error || 'Please fill out Form 1040 first to see versions here.'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("flex flex-col h-full bg-white", className)}>
      {/* Cursor-Style Version Selector */}
      <div className="relative flex items-center justify-between px-4 py-3 border-b bg-white">
        {/* Left: Form Info */}
        <div className="flex items-center space-x-3">
          <FileText className="w-5 h-5 text-blue-600" />
          <div>
            <h3 className="text-sm font-semibold text-gray-900">
              Form {versionsData.form_type} - {versionsData.tax_year}
            </h3>
            <p className="text-xs text-gray-500">
              {versionsData.total_versions} version{versionsData.total_versions !== 1 ? 's' : ''} available
            </p>
          </div>
        </div>

        {/* Right: Version Navigator (Cursor Style) */}
        <div 
          className="relative"
          onMouseEnter={() => setShowTooltip(true)}
          onMouseLeave={() => setShowTooltip(false)}
        >
          {/* Tooltip */}
          {showTooltip && (
            <div className="absolute bottom-full right-0 mb-2 z-50 animate-in fade-in slide-in-from-bottom-2 duration-200">
              <div className="bg-gray-900 text-white text-xs rounded-lg shadow-lg px-3 py-2 min-w-[200px]">
                <div className="font-semibold mb-1">{currentVersion.version}</div>
                <div className="text-gray-300 space-y-0.5">
                  <div className="flex items-center space-x-1">
                    <Clock className="w-3 h-3" />
                    <span>{currentVersion.last_modified}</span>
                  </div>
                  <div>{(currentVersion.size / 1024).toFixed(0)} KB</div>
                  {isLatest && <div className="text-green-400">✓ Latest version</div>}
                </div>
                {/* Arrow */}
                <div className="absolute top-full right-4 -mt-1">
                  <div className="border-4 border-transparent border-t-gray-900"></div>
                </div>
              </div>
            </div>
          )}

          {/* Version Control */}
          <div className="flex items-center space-x-1 bg-gray-100 rounded-lg p-1">
            {/* Up Button (Newer) */}
            <button
              onClick={goToPreviousVersion}
              disabled={isLatest}
              className={cn(
                "p-1.5 rounded transition-all",
                isLatest
                  ? "text-gray-300 cursor-not-allowed"
                  : "text-gray-700 hover:bg-white hover:shadow-sm"
              )}
              title="Newer version"
            >
              <ChevronUp className="w-4 h-4" />
            </button>

            {/* Version Display */}
            <div className="px-3 py-1 bg-white rounded shadow-sm min-w-[60px] text-center">
              <div className="text-xs font-mono font-semibold text-gray-900">
                {currentVersion.version}
              </div>
            </div>

            {/* Down Button (Older) */}
            <button
              onClick={goToNextVersion}
              disabled={isOldest}
              className={cn(
                "p-1.5 rounded transition-all",
                isOldest
                  ? "text-gray-300 cursor-not-allowed"
                  : "text-gray-700 hover:bg-white hover:shadow-sm"
              )}
              title="Older version"
            >
              <ChevronDown className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Version Info Bar */}
      <div className="px-4 py-2 bg-gray-50 border-b text-xs text-gray-600 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <span>
            Viewing {currentVersionIndex + 1} of {versionsData.total_versions}
          </span>
          {isLatest ? (
            <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-green-100 text-green-700 font-medium">
              ✓ Latest
            </span>
          ) : (
            <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-yellow-100 text-yellow-700 font-medium">
              ⚠ Older Version
            </span>
          )}
        </div>
        <div className="text-gray-500">
          Last modified: {currentVersion.last_modified}
        </div>
      </div>

      {/* PDF Viewer */}
      <div className="flex-1 overflow-hidden">
        <PdfViewer
          url={currentVersion.download_url}
          className="w-full h-full"
        />
      </div>

      {/* Keyboard Shortcuts Hint */}
      <div className="px-4 py-2 bg-gray-50 border-t text-xs text-gray-500 text-center">
        Use ↑↓ arrow buttons to navigate between versions
      </div>
    </div>
  );
}

