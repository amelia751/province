import React from 'react';
import { FileText, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { useDocumentNotifications, DocumentNotification } from '@/hooks/use-document-notifications';

interface DocumentProcessingNotificationsProps {
  engagementId?: string;
  className?: string;
}

export function DocumentProcessingNotifications({ 
  engagementId, 
  className = '' 
}: DocumentProcessingNotificationsProps) {
  const {
    notifications,
    isLoading,
    error,
    markAsRead,
    simulateProcessing,
    isProcessing,
    hasUnread
  } = useDocumentNotifications({
    engagementId,
    enabled: !!engagementId
  });

  if (!engagementId) return null;

  const handleMarkAllRead = () => {
    const unreadTimestamps = notifications
      .filter(n => !n.read)
      .map(n => n.timestamp);
    
    if (unreadTimestamps.length > 0) {
      markAsRead(unreadTimestamps);
    }
  };

  const getNotificationIcon = (notification: DocumentNotification) => {
    switch (notification.status) {
      case 'processing':
        return <Loader2 className="h-4 w-4 animate-spin text-blue-500" />;
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-500" />;
      default:
        return <FileText className="h-4 w-4 text-gray-500" />;
    }
  };

  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  if (error) {
    return (
      <div className={`bg-red-50 border border-red-200 rounded-lg p-3 ${className}`}>
        <div className="flex items-center space-x-2">
          <AlertCircle className="h-4 w-4 text-red-500" />
          <span className="text-sm text-red-700">Failed to load notifications: {error}</span>
        </div>
      </div>
    );
  }

  if (notifications.length === 0 && !isLoading) {
    return (
      <div className={`bg-gray-50 border border-gray-200 rounded-lg p-3 ${className}`}>
        <div className="text-center">
          <FileText className="h-8 w-8 text-gray-400 mx-auto mb-2" />
          <p className="text-sm text-gray-600">No document processing notifications</p>
          <button
            onClick={simulateProcessing}
            className="mt-2 text-xs text-blue-600 hover:text-blue-800 underline"
          >
            Simulate W2 Processing
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-2 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <FileText className="h-4 w-4 text-gray-600" />
          <span className="text-sm font-medium text-gray-800">
            Document Processing
          </span>
          {hasUnread && (
            <span className="bg-blue-500 text-white text-xs px-2 py-0.5 rounded-full">
              {notifications.filter(n => !n.read).length}
            </span>
          )}
        </div>
        
        {hasUnread && (
          <button
            onClick={handleMarkAllRead}
            className="text-xs text-blue-600 hover:text-blue-800"
          >
            Mark all read
          </button>
        )}
      </div>

      {/* Notifications List */}
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {notifications.map((notification) => (
          <div
            key={`${notification.engagement_id}-${notification.timestamp}`}
            className={`flex items-start space-x-3 p-3 rounded-lg border ${
              notification.read 
                ? 'bg-gray-50 border-gray-200' 
                : 'bg-white border-blue-200 shadow-sm'
            }`}
          >
            <div className="flex-shrink-0 mt-0.5">
              {getNotificationIcon(notification)}
            </div>
            
            <div className="flex-1 min-w-0">
              <p className={`text-sm ${
                notification.read ? 'text-gray-600' : 'text-gray-900'
              }`}>
                {notification.message}
              </p>
              
              <div className="flex items-center justify-between mt-1">
                <span className="text-xs text-gray-500">
                  {formatTimestamp(notification.timestamp)}
                </span>
                
                {notification.status === 'completed' && notification.data && (
                  <div className="text-xs text-green-600">
                    {notification.data.document_type} • 
                    ${notification.data.total_wages?.toLocaleString() || 0}
                  </div>
                )}
              </div>
              
              {!notification.read && (
                <button
                  onClick={() => markAsRead([notification.timestamp])}
                  className="text-xs text-blue-600 hover:text-blue-800 mt-1"
                >
                  Mark as read
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Processing Status */}
      {isProcessing && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
          <div className="flex items-center space-x-2">
            <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
            <span className="text-sm text-blue-700">
              Processing documents in background...
            </span>
          </div>
        </div>
      )}

      {/* Debug Actions */}
      <div className="pt-2 border-t border-gray-200">
        <button
          onClick={simulateProcessing}
          className="text-xs text-gray-500 hover:text-gray-700"
        >
          🧪 Simulate Processing
        </button>
      </div>
    </div>
  );
}
