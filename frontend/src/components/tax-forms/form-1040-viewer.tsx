"use client";

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { ChevronUp, ChevronDown, Clock, Files, Rabbit, RefreshCw, ExternalLink, Download } from 'lucide-react';
import { PdfViewer } from '@/components/pdf-viewer';
import { Spinner } from '@/components/ui/spinner';
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
  userId?: string;
  className?: string;
  onVersionChange?: (versionInfo: {
    currentVersion: number;
    totalVersions: number;
    isLatest: boolean;
    lastModified: string;
  }) => void;
}

export function Form1040Viewer({ engagementId, userId, className, onVersionChange }: Form1040ViewerProps) {
  const [versionsData, setVersionsData] = useState<FormVersionsData | null>(null);
  const [currentVersionIndex, setCurrentVersionIndex] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<number>(Date.now());
  const [forceReloadKey, setForceReloadKey] = useState(0); // Force complete reload on version change

  // Use ref to avoid stale closure in interval
  const versionsDataRef = useRef(versionsData);
  useEffect(() => {
    versionsDataRef.current = versionsData;
  }, [versionsData]);

  // Ref to always call the latest checkForNewVersions
  const checkRef = useRef<() => void>(() => {});

  // Derived state - must be declared before useEffects that use it
  const currentVersion = versionsData?.versions[currentVersionIndex];
  const isLatest = currentVersionIndex === 0;
  const isOldest = versionsData && currentVersionIndex === versionsData.versions.length - 1;

  const loadVersions = async () => {
    try {
      setLoading(true);
      setError(null);

      // Include user_id in query if available
      const url = userId 
        ? `/api/forms/1040/${engagementId}/versions?tax_year=2024&user_id=${userId}`
        : `/api/forms/1040/${engagementId}/versions?tax_year=2024`;

      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`Failed to load form versions: ${response.statusText}`);
      }

      const data: FormVersionsData = await response.json();
      setVersionsData(data);
      setCurrentVersionIndex(0); // Start with latest version
      setLastChecked(Date.now());
    } catch (err) {
      console.error('Error loading form versions:', err);
      setError(err instanceof Error ? err.message : 'Failed to load form versions');
    } finally {
      setLoading(false);
    }
  };

  // Check for new versions without showing loading state
  const checkForNewVersions = useCallback(async () => {
    try {
      // Cache-busting both at the fetch layer and URL to defeat CDN/browser caches
      const ts = Date.now();
      const urlBase = userId
        ? `/api/forms/1040/${engagementId}/versions?tax_year=2024&user_id=${encodeURIComponent(userId)}`
        : `/api/forms/1040/${engagementId}/versions?tax_year=2024`;

      const response = await fetch(`${urlBase}&_=${ts}`, {
        cache: 'no-store',
        headers: {
          'Cache-Control': 'no-cache, no-store, max-age=0',
          'Pragma': 'no-cache',
        },
      });

      if (response.status === 404) {
        // Treat as "no versions yet" but still update lastChecked so UI doesn't look stuck
        setLastChecked(Date.now());
        return;
      }
      if (!response.ok) {
        setLastChecked(Date.now());
        return;
      }

      const data: FormVersionsData = await response.json();

      const current = versionsDataRef.current;
      const currentTotal = current?.total_versions ?? 0;
      const currentLatest = current?.latest_version ?? '';

      // Prefer numeric comparison; fall back to latest_version string if needed
      const newLatestNum = data.versions?.[0]?.version_number ?? 0;
      const curLatestNum = current?.versions?.[0]?.version_number ?? 0;
      const hasNewVersion =
        data.total_versions > currentTotal ||
        newLatestNum > curLatestNum ||
        (!!data.latest_version && data.latest_version !== currentLatest);

      if (hasNewVersion) {
        console.log('🔄 New form version detected!');
        console.log(`   Previous: ${currentTotal} versions, latest: ${currentLatest}, num: ${curLatestNum}`);
        console.log(`   New: ${data.total_versions} versions, latest: ${data.latest_version}, num: ${newLatestNum}`);
        
        // Sort versions to ensure newest-first (by version_number descending)
        const normalized = {
          ...data,
          versions: [...(data.versions ?? [])].sort((a, b) => (b.version_number ?? 0) - (a.version_number ?? 0)),
        };
        
        setVersionsData(normalized);
        setCurrentVersionIndex(0); // jump to newest (index 0)
        setForceReloadKey(prev => prev + 1); // force a hard remount of the PDF viewer
      }
      setLastChecked(Date.now());
    } catch (err) {
      // Keep this silent in prod; during debug you can log it
      console.debug('Background version check failed:', err);
      setLastChecked(Date.now());
    }
  }, [engagementId, userId]);

  // Load versions on mount
  useEffect(() => {
    loadVersions();
  }, [engagementId]);

  // Auto-refresh: Poll for new versions every 5 seconds
  useEffect(() => {
    checkRef.current = checkForNewVersions; // always point to the latest function
  }, [checkForNewVersions]);

  useEffect(() => {
    const id = setInterval(() => {
      checkRef.current(); // call the *current* checker
    }, 5000);
    return () => clearInterval(id);
  }, [engagementId, userId]); // only reset when identity changes

  // Notify parent of version changes
  useEffect(() => {
    if (versionsData && currentVersion && onVersionChange) {
      onVersionChange({
        currentVersion: currentVersionIndex + 1,
        totalVersions: versionsData.total_versions,
        isLatest: currentVersionIndex === 0,
        lastModified: currentVersion.last_modified,
      });
    }
  }, [versionsData, currentVersionIndex, currentVersion, onVersionChange]);

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

  if (loading) {
    return (
      <div className={cn("flex items-center justify-center h-full bg-gray-50", className)}>
        <div className="text-center">
          <Spinner className="h-6 w-6 mx-auto mb-2 text-gray-600" />
          <p className="text-sm text-gray-600">Loading form versions...</p>
        </div>
      </div>
    );
  }

  if (error || !versionsData || !currentVersion) {
    // Show template form as Version 0 when no versions are available
    const templateUrl = `/api/forms/1040/template?tax_year=2024`;
    
    return (
      <div className={cn("flex flex-col h-full bg-white", className)}>
        {/* Cursor-Style Version Selector (Version 0) */}
        <div className="relative flex items-center justify-between px-4 py-3 border-b bg-white">
          {/* Left: Form Info */}
          <div className="flex items-center space-x-3">
            <Files className="w-5 h-5 text-black" strokeWidth={1.5} />
            <div>
              <h3 className="text-sm font-semibold text-gray-900">
                Form 1040 - 2024
              </h3>
              <p className="text-xs text-gray-500">
                No versions yet
              </p>
            </div>
          </div>

          {/* Center: Version Navigator (disabled) */}
          <div className="flex items-center space-x-2">
            {/* Manual Refresh Button */}
            <button
              onClick={loadVersions}
              className="p-2 rounded-md hover:bg-gray-100 transition-colors"
              title="Refresh versions"
            >
              <RefreshCw className="w-4 h-4 text-gray-600" />
            </button>

            {/* Version Navigator (Cursor Style) - Disabled */}
            <div className="flex items-center space-x-1 bg-gray-100 rounded-lg p-1">
              {/* Up Button (Disabled) */}
              <button
                disabled
                className="p-1.5 rounded transition-all text-gray-300 cursor-not-allowed"
              >
                <ChevronUp className="w-4 h-4" />
              </button>

              {/* Version Display - v000 */}
              <div className="px-3 py-1 bg-white rounded shadow-sm min-w-[60px] text-center">
                <div className="text-xs font-mono font-semibold text-gray-900">
                  v000
                </div>
              </div>

              {/* Down Button (Disabled) */}
              <button
                disabled
                className="p-1.5 rounded transition-all text-gray-300 cursor-not-allowed"
              >
                <ChevronDown className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Right: Open & Download Buttons */}
          <div className="flex items-center space-x-2">
            <a
              href={templateUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center px-3 py-1.5 text-sm bg-paper-white text-gray-600 rounded hover:bg-darker-ecru transition-colors"
            >
              <ExternalLink className="w-4 h-4 mr-1" />
              Open
            </a>
            <a
              href={templateUrl}
              download
              className="inline-flex items-center px-3 py-1.5 text-sm bg-true-turquoise text-white rounded hover:bg-true-turquoise/90 transition-colors"
            >
              <Download className="w-4 h-4 mr-1" />
              Download
            </a>
          </div>
        </div>

        {/* PDF Viewer for Template */}
        <div className="flex-1 overflow-hidden">
          <PdfViewer
            key="template-1040"
            url={templateUrl}
            className="w-full h-full"
          />
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
          <Files className="w-5 h-5 text-black" strokeWidth={1.5} />
          <div>
            <h3 className="text-sm font-semibold text-gray-900">
              Form {versionsData.form_type} - {versionsData.tax_year}
            </h3>
            <p className="text-xs text-gray-500">
              {versionsData.total_versions} version{versionsData.total_versions !== 1 ? 's' : ''} available
            </p>
          </div>
        </div>

        {/* Center: Version Navigator */}
        <div className="flex items-center space-x-2">
          {/* Manual Refresh Button */}
          <button
            onClick={loadVersions}
            className="p-2 rounded-md hover:bg-gray-100 transition-colors"
            title="Refresh versions"
          >
            <RefreshCw className="w-4 h-4 text-gray-600" />
          </button>

          {/* Version Navigator (Cursor Style) */}
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
            >
              <ChevronDown className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Right: Open & Download Buttons */}
        <div className="flex items-center space-x-2">
          <a
            href={currentVersion.download_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center px-3 py-1.5 text-sm bg-paper-white text-gray-600 rounded hover:bg-darker-ecru transition-colors"
          >
            <ExternalLink className="w-4 h-4 mr-1" />
            Open
          </a>
          <a
            href={currentVersion.download_url}
            download
            className="inline-flex items-center px-3 py-1.5 text-sm bg-true-turquoise text-white rounded hover:bg-true-turquoise/90 transition-colors"
          >
            <Download className="w-4 h-4 mr-1" />
            Download
          </a>
        </div>
      </div>

      {/* PDF Viewer */}
      <div className="flex-1 overflow-hidden">
        {(() => {
          const v = currentVersion.version;
          const t = currentVersion.timestamp;
          const cacheKey = `${v}-${t}`;
          const sep = currentVersion.download_url.includes('?') ? '&' : '?';

          // Version-based cache buster (stable while same version) + a force key that changes on detection
          const urlWithCache = `${currentVersion.download_url}${sep}v=${encodeURIComponent(cacheKey)}&r=${forceReloadKey}`;

          return (
            <PdfViewer
              key={`${cacheKey}-${forceReloadKey}`} // changes when new version or forced
              url={urlWithCache}
              className="w-full h-full"
            />
          );
        })()}
      </div>
    </div>
  );
}

