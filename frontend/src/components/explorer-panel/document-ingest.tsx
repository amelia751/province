"use client";

import React, { useState, useCallback } from "react";
import { CloudUpload, X, File, CheckCircle, AlertCircle } from "lucide-react";
import { useUser } from '@clerk/nextjs';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface DocumentIngestProps {
  engagementId: string;
  folderName: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onUpload?: (files: File[], engagementId: string) => void;
}

interface UploadedFile {
  file: File;
  id: string;
  status: 'pending' | 'uploading' | 'success' | 'error';
  progress: number;
  error?: string;
}

export default function DocumentIngest({
  engagementId,
  folderName,
  open,
  onOpenChange,
  onUpload
}: DocumentIngestProps) {
  const { user } = useUser();
  const [isDragging, setIsDragging] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);

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
    handleFiles(files);
  }, []);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    handleFiles(files);
  }, []);

  const uploadFileToAPI = async (uploadedFile: UploadedFile) => {
    try {
      console.log('=== UPLOAD DEBUG START ===');
      console.log('Engagement ID:', engagementId);
      console.log('File:', uploadedFile.file.name, uploadedFile.file.type, uploadedFile.file.size);
      console.log('User:', user?.id);

      const formData = new FormData();
      formData.append('file', uploadedFile.file);
      formData.append('engagementId', engagementId);
      formData.append('documentPath', `uploads/${uploadedFile.file.name}`);

      console.log('Sending request to /api/documents/upload');
      const response = await fetch('/api/documents/upload', {
        method: 'POST',
        body: formData,
      });

      console.log('Response status:', response.status);
      console.log('Response headers:', Object.fromEntries(response.headers.entries()));

      if (!response.ok) {
        const errorText = await response.text();
        console.log('Error response text:', errorText);
        
        let errorData;
        try {
          errorData = JSON.parse(errorText);
        } catch {
          errorData = { error: errorText };
        }
        
        console.log('Parsed error data:', errorData);
        throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
      }

      const resultText = await response.text();
      console.log('Success response text:', resultText);
      
      const result = JSON.parse(resultText);
      console.log('Parsed result:', result);
      console.log('=== UPLOAD DEBUG END ===');
      
      return result;
    } catch (error) {
      console.error('=== UPLOAD ERROR ===');
      console.error('Error details:', error);
      console.error('Error message:', error instanceof Error ? error.message : String(error));
      console.error('Error stack:', error instanceof Error ? error.stack : 'No stack');
      throw error;
    }
  };

  const handleFiles = (files: File[]) => {
    if (!user) {
      console.error('User not authenticated');
      return;
    }

    const allowedTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg'];
    const allowedExtensions = ['.pdf', '.png', '.jpg', '.jpeg'];

    const newFiles: UploadedFile[] = files.map(file => {
      const fileExtension = '.' + file.name.split('.').pop()?.toLowerCase();
      const isValidType = allowedTypes.includes(file.type) || allowedExtensions.includes(fileExtension);

      if (!isValidType) {
        return {
          file,
          id: Math.random().toString(36).substr(2, 9),
          status: 'error' as const,
          progress: 0,
          error: 'Invalid file format. Only PDF, JPG, and PNG are supported.'
        };
      }

      return {
        file,
        id: Math.random().toString(36).substr(2, 9),
        status: 'pending' as const,
        progress: 0
      };
    });

    setUploadedFiles(prev => [...prev, ...newFiles]);
  };

  const handleUploadFiles = async () => {
    const pendingFiles = uploadedFiles.filter(f => f.status === 'pending');
    
    for (const uploadedFile of pendingFiles) {
      // Set status to uploading
      setUploadedFiles(prev =>
        prev.map(f =>
          f.id === uploadedFile.id
            ? { ...f, status: 'uploading' }
            : f
        )
      );

      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setUploadedFiles(prev =>
          prev.map(f => {
            if (f.id === uploadedFile.id && f.status === 'uploading' && f.progress < 90) {
              return { ...f, progress: Math.min(f.progress + 15, 90) };
            }
            return f;
          })
        );
      }, 300);

      try {
        // Actual upload
        const result = await uploadFileToAPI(uploadedFile);
        
        clearInterval(progressInterval);
        
        // Set success status
        setUploadedFiles(prev =>
          prev.map(f =>
            f.id === uploadedFile.id
              ? { ...f, status: 'success', progress: 100 }
              : f
          )
        );

        console.log('Upload successful:', result);
      } catch (error) {
        clearInterval(progressInterval);
        
        // Set error status
        setUploadedFiles(prev =>
          prev.map(f =>
            f.id === uploadedFile.id
              ? { ...f, status: 'error', progress: 0, error: error instanceof Error ? error.message : 'Upload failed' }
              : f
          )
        );

        console.error('Upload failed:', error);
      }
    }

    // Call onUpload callback for successful uploads
    if (onUpload) {
      const successfulFiles = uploadedFiles.filter(f => f.status === 'success').map(f => f.file);
      if (successfulFiles.length > 0) {
        onUpload(successfulFiles, engagementId);
      }
    }
  };

  const removeFile = (fileId: string) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const clearAllFiles = () => {
    setUploadedFiles([]);
  };

  const hasSuccessfulUploads = uploadedFiles.some(f => f.status === 'success');
  const hasPendingFiles = uploadedFiles.some(f => f.status === 'pending');
  const hasUploadingFiles = uploadedFiles.some(f => f.status === 'uploading');
  const allUploadsComplete = uploadedFiles.length > 0 && uploadedFiles.every(f => f.status === 'success' || f.status === 'error');


  const handleClose = () => {
    setUploadedFiles([]);
    onOpenChange(false);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[600px] bg-white">
        <DialogHeader>
          <DialogTitle className="text-lg font-normal">Upload Your {folderName}</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          {/* Drop Zone */}
          <div
            className={cn(
              "border-2 border-dashed rounded-lg p-8 text-center transition-colors bg-white",
              isDragging
                ? "border-black"
                : "border-gray-300 hover:border-gray-400"
            )}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <CloudUpload className="h-12 w-12 mx-auto mb-4 text-gray-400" strokeWidth={1} />
            <p className="text-sm text-gray-700 mb-2">
              Drag and drop your files
            </p>
            <p className="text-xs text-gray-500 mb-4">
              or
            </p>
            <label htmlFor="file-upload">
              <Button asChild className="bg-[#EFEEE8] hover:bg-[#E8E5D8] text-black border-0">
                <span className="cursor-pointer">
                  Browse Files
                </span>
              </Button>
            </label>
            <input
              id="file-upload"
              type="file"
              multiple
              className="hidden"
              onChange={handleFileInput}
              accept=".pdf,.png,.jpg,.jpeg"
            />
            <p className="text-xs text-gray-500 mt-4">
              Supported formats: PDF, JPG, PNG
            </p>
          </div>

          {/* Uploaded Files List */}
          {uploadedFiles.length > 0 && (
            <div className="space-y-2 max-h-[300px] overflow-y-auto">
              <h4 className="text-sm font-medium">Files ({uploadedFiles.length})</h4>
              {uploadedFiles.map((uploadedFile) => (
                <div
                  key={uploadedFile.id}
                  className="flex items-center space-x-3 p-3 rounded-lg bg-[#EFEEE8]"
                >
                  <File className="h-5 w-5 text-gray-400 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <p className="text-sm font-medium truncate">
                        {uploadedFile.file.name}
                      </p>
                      <span className="text-xs text-gray-500 ml-2">
                        {formatFileSize(uploadedFile.file.size)}
                      </span>
                    </div>
                    {uploadedFile.status === 'uploading' && (
                      <div className="w-full bg-gray-200 rounded-full h-1.5">
                        <div
                          className="bg-black h-1.5 rounded-full transition-all duration-300"
                          style={{ width: `${uploadedFile.progress}%` }}
                        />
                      </div>
                    )}
                    {uploadedFile.status === 'success' && (
                      <div className="flex items-center space-x-1 text-green-600">
                        <CheckCircle className="h-3 w-3" />
                        <span className="text-xs">Uploaded successfully</span>
                      </div>
                    )}
                    {uploadedFile.status === 'error' && (
                      <div className="flex items-center space-x-1 text-red-600">
                        <AlertCircle className="h-3 w-3" />
                        <span className="text-xs">{uploadedFile.error || 'Upload failed'}</span>
                      </div>
                    )}
                  </div>
                  {uploadedFile.status !== 'uploading' && (
                    <button
                      onClick={() => removeFile(uploadedFile.id)}
                      className="flex-shrink-0 text-gray-400 hover:text-gray-600"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end items-center space-x-2 pt-4 border-t">
            <Button
              onClick={handleClose}
              className="bg-[#EFEEE8] hover:bg-[#E8E5D8] text-black border-0"
            >
              {allUploadsComplete ? 'Close' : 'Cancel'}
            </Button>

            <Button
              onClick={handleUploadFiles}
              disabled={!hasPendingFiles || hasUploadingFiles}
              className="bg-true-turquoise hover:bg-true-turquoise/90 text-white border-0 disabled:bg-gray-300 disabled:text-gray-500"
            >
              {hasUploadingFiles ? 'Uploading...' : allUploadsComplete && hasSuccessfulUploads ? 'Done' : 'Save'}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
