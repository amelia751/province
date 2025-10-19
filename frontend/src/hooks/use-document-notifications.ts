import { useState, useEffect, useCallback, useRef } from 'react';

export interface DocumentNotification {
  engagement_id: string;
  timestamp: number;
  message: string;
  status: 'processing' | 'completed' | 'error';
  type: string;
  read: boolean;
  data?: any;
}

export interface UseDocumentNotificationsOptions {
  engagementId?: string;
  pollingInterval?: number; // milliseconds
  enabled?: boolean;
}

export function useDocumentNotifications({
  engagementId,
  pollingInterval = 3000, // 3 seconds
  enabled = true
}: UseDocumentNotificationsOptions = {}) {
  const [notifications, setNotifications] = useState<DocumentNotification[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastFetch, setLastFetch] = useState<number>(0);
  
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const mountedRef = useRef(true);

  const fetchNotifications = useCallback(async (since?: number) => {
    if (!engagementId || !enabled) return;

    try {
      setIsLoading(true);
      setError(null);

      const params = new URLSearchParams({
        engagement_id: engagementId,
        limit: '20'
      });

      if (since) {
        params.append('since', since.toString());
      }

      const response = await fetch(`/api/documents/notifications?${params}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch notifications: ${response.statusText}`);
      }

      const data = await response.json();
      
      if (mountedRef.current) {
        if (since) {
          // Append new notifications
          setNotifications(prev => [...data.notifications, ...prev]);
        } else {
          // Replace all notifications
          setNotifications(data.notifications || []);
        }
        setLastFetch(Date.now());
      }

    } catch (err) {
      if (mountedRef.current) {
        setError(err instanceof Error ? err.message : 'Failed to fetch notifications');
        console.error('Error fetching document notifications:', err);
      }
    } finally {
      if (mountedRef.current) {
        setIsLoading(false);
      }
    }
  }, [engagementId, enabled]);

  const markAsRead = useCallback(async (timestamps: number[]) => {
    if (!engagementId || timestamps.length === 0) return;

    try {
      const response = await fetch('/api/documents/notifications', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          engagement_id: engagementId,
          timestamps
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to mark notifications as read: ${response.statusText}`);
      }

      // Update local state
      setNotifications(prev => 
        prev.map(notification => 
          timestamps.includes(notification.timestamp)
            ? { ...notification, read: true }
            : notification
        )
      );

    } catch (err) {
      console.error('Error marking notifications as read:', err);
    }
  }, [engagementId]);

  const simulateProcessing = useCallback(async () => {
    if (!engagementId) return;

    try {
      const response = await fetch(`/api/documents/notifications?engagement_id=${engagementId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          action: 'simulate-processing'
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to simulate processing: ${response.statusText}`);
      }

      // Refresh notifications after simulation
      setTimeout(() => fetchNotifications(), 1000);

    } catch (err) {
      console.error('Error simulating processing:', err);
    }
  }, [engagementId, fetchNotifications]);

  // Initial fetch
  useEffect(() => {
    if (enabled && engagementId) {
      fetchNotifications();
    }
  }, [fetchNotifications, enabled, engagementId]);

  // Set up polling
  useEffect(() => {
    if (!enabled || !engagementId) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }

    intervalRef.current = setInterval(() => {
      // Only fetch new notifications (since last fetch)
      fetchNotifications(lastFetch);
    }, pollingInterval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [enabled, engagementId, pollingInterval, lastFetch, fetchNotifications]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      mountedRef.current = false;
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  // Get unread notifications
  const unreadNotifications = notifications.filter(n => !n.read);
  const processingNotifications = notifications.filter(n => n.status === 'processing');
  const completedNotifications = notifications.filter(n => n.status === 'completed');
  const errorNotifications = notifications.filter(n => n.status === 'error');

  return {
    notifications,
    unreadNotifications,
    processingNotifications,
    completedNotifications,
    errorNotifications,
    isLoading,
    error,
    fetchNotifications: () => fetchNotifications(),
    markAsRead,
    simulateProcessing,
    hasUnread: unreadNotifications.length > 0,
    isProcessing: processingNotifications.length > 0,
    hasErrors: errorNotifications.length > 0
  };
}
