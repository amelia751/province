"use client";

import React, { useState, useCallback } from "react";
import { Upload, X, File, CheckCircle } from "lucide-react";
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
  folderId: string;
  folderName: string;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onUpload?: (files: File[], folderId: string) => void;
}

interface UploadedFile {
  file: File;
  id: string;
  status: 'pending' | 'uploading' | 'success' | 'error';
  progress: number;
}

export default function DocumentIngest({
  folderId,
  folderName,
  open,
  onOpenChange,
  onUpload
}: DocumentIngestProps) {
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

  const handleFiles = (files: File[]) => {
    const newFiles: UploadedFile[] = files.map(file => ({
      file,
      id: Math.random().toString(36).substr(2, 9),
      status: 'pending',
      progress: 0
    }));

    setUploadedFiles(prev => [...prev, ...newFiles]);

    // Simulate upload process
    newFiles.forEach((uploadedFile, index) => {
      setTimeout(() => {
        setUploadedFiles(prev =>
          prev.map(f =>
            f.id === uploadedFile.id
              ? { ...f, status: 'uploading' }
              : f
          )
        );

        // Simulate progress
        const progressInterval = setInterval(() => {
          setUploadedFiles(prev =>
            prev.map(f => {
              if (f.id === uploadedFile.id && f.progress < 100) {
                const newProgress = Math.min(f.progress + 10, 100);
                if (newProgress === 100) {
                  setTimeout(() => {
                    setUploadedFiles(prev =>
                      prev.map(file =>
                        file.id === uploadedFile.id
                          ? { ...file, status: 'success' }
                          : file
                      )
                    );
                  }, 200);
                }
                return { ...f, progress: newProgress };
              }
              return f;
            })
          );
        }, 200);

        setTimeout(() => {
          clearInterval(progressInterval);
        }, 2000);
      }, index * 100);
    });

    // Call onUpload callback
    if (onUpload) {
      onUpload(files, folderId);
    }
  };

  const handleRemoveFile = (fileId: string) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== fileId));
  };

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
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Upload Your {folderName}</DialogTitle>
          <DialogDescription>
            Drag and drop files here or click to browse your computer
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {/* Drop Zone */}
          <div
            className={cn(
              "border-2 border-dashed rounded-lg p-8 text-center transition-colors",
              isDragging
                ? "border-black bg-gray-50"
                : "border-gray-300 hover:border-gray-400"
            )}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <Upload className="h-12 w-12 mx-auto mb-4 text-gray-400" />
            <p className="text-sm text-gray-600 mb-2">
              Drag and drop your files here
            </p>
            <p className="text-xs text-gray-500 mb-4">
              or
            </p>
            <label htmlFor="file-upload">
              <Button variant="outline" asChild>
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
              accept=".pdf,.doc,.docx,.xls,.xlsx,.png,.jpg,.jpeg"
            />
            <p className="text-xs text-gray-500 mt-4">
              Supported formats: PDF, DOC, DOCX, XLS, XLSX, PNG, JPG
            </p>
          </div>

          {/* Uploaded Files List */}
          {uploadedFiles.length > 0 && (
            <div className="space-y-2 max-h-[300px] overflow-y-auto">
              <h4 className="text-sm font-medium">Files ({uploadedFiles.length})</h4>
              {uploadedFiles.map((uploadedFile) => (
                <div
                  key={uploadedFile.id}
                  className="flex items-center space-x-3 p-3 border rounded-lg"
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
                  </div>
                  {uploadedFile.status !== 'uploading' && (
                    <button
                      onClick={() => handleRemoveFile(uploadedFile.id)}
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
          <div className="flex justify-end space-x-2 pt-4 border-t">
            <Button variant="outline" onClick={handleClose}>
              Close
            </Button>
            {uploadedFiles.length > 0 && uploadedFiles.every(f => f.status === 'success') && (
              <Button onClick={handleClose}>
                Done
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
