"use client";

import React, { useState, useEffect } from 'react';
import { useUser } from '@clerk/nextjs';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '@/components/ui/alert-dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { RefreshCw, Trash2, Database, Cloud, User, FileText, Folder, Calendar } from 'lucide-react';
import { toast } from 'sonner';

interface UserDataItem {
  id: string;
  type: 'engagement' | 'document' | 's3_object';
  name: string;
  path?: string;
  size?: number;
  created_at?: string;
  updated_at?: string;
  metadata?: Record<string, any>;
}

interface UserDataSummary {
  engagements: UserDataItem[];
  documents: UserDataItem[];
  s3_objects: UserDataItem[];
  total_size: number;
  total_count: number;
}

export function DevDataManager() {
  const { user } = useUser();
  const [userData, setUserData] = useState<UserDataSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [cleanupLoading, setCleanupLoading] = useState(false);

  const fetchUserData = async () => {
    if (!user?.id) return;

    setLoading(true);
    try {
      const response = await fetch(`/api/dev/user-data?userId=${user.id}`, {
        headers: {
          'Authorization': `Bearer ${await user.getToken()}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch user data');
      }

      const data = await response.json();
      setUserData(data);
    } catch (error) {
      console.error('Error fetching user data:', error);
      toast.error('Failed to fetch user data');
    } finally {
      setLoading(false);
    }
  };

  const cleanupUserData = async () => {
    if (!user?.id) return;

    setCleanupLoading(true);
    try {
      const response = await fetch(`/api/dev/cleanup-user-data`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${await user.getToken()}`,
        },
        body: JSON.stringify({ userId: user.id }),
      });

      if (!response.ok) {
        throw new Error('Failed to cleanup user data');
      }

      const result = await response.json();
      toast.success(`Cleanup completed: ${result.deleted_items} items deleted`);
      
      // Refresh data
      await fetchUserData();
    } catch (error) {
      console.error('Error cleaning up user data:', error);
      toast.error('Failed to cleanup user data');
    } finally {
      setCleanupLoading(false);
    }
  };

  useEffect(() => {
    if (user?.id) {
      fetchUserData();
    }
  }, [user?.id]);

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString();
  };

  if (!user) {
    return (
      <Card>
        <CardContent className="p-6">
          <p className="text-muted-foreground">Please sign in to view developer data.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Developer Data Manager</h2>
          <p className="text-muted-foreground">
            Manage your development data for user: {user.emailAddresses[0]?.emailAddress}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            onClick={fetchUserData}
            disabled={loading}
            variant="outline"
            size="sm"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button
                variant="destructive"
                size="sm"
                disabled={!userData || userData.total_count === 0}
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Cleanup All Data
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Delete All User Data</AlertDialogTitle>
                <AlertDialogDescription>
                  This will permanently delete all your development data including:
                  <ul className="list-disc list-inside mt-2 space-y-1">
                    <li>{userData?.engagements.length || 0} engagements</li>
                    <li>{userData?.documents.length || 0} documents</li>
                    <li>{userData?.s3_objects.length || 0} S3 objects</li>
                  </ul>
                  <p className="mt-2 font-semibold text-destructive">
                    This action cannot be undone.
                  </p>
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction
                  onClick={cleanupUserData}
                  disabled={cleanupLoading}
                  className="bg-destructive hover:bg-destructive/90"
                >
                  {cleanupLoading ? (
                    <>
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                      Deleting...
                    </>
                  ) : (
                    'Delete All Data'
                  )}
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>
      </div>

      {/* Summary Cards */}
      {userData && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center space-x-2">
                <User className="h-4 w-4 text-blue-500" />
                <div>
                  <p className="text-sm font-medium">Engagements</p>
                  <p className="text-2xl font-bold">{userData.engagements.length}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center space-x-2">
                <FileText className="h-4 w-4 text-green-500" />
                <div>
                  <p className="text-sm font-medium">Documents</p>
                  <p className="text-2xl font-bold">{userData.documents.length}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center space-x-2">
                <Cloud className="h-4 w-4 text-orange-500" />
                <div>
                  <p className="text-sm font-medium">S3 Objects</p>
                  <p className="text-2xl font-bold">{userData.s3_objects.length}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center space-x-2">
                <Database className="h-4 w-4 text-purple-500" />
                <div>
                  <p className="text-sm font-medium">Total Size</p>
                  <p className="text-2xl font-bold">{formatBytes(userData.total_size)}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Data Details */}
      {userData && (
        <Tabs defaultValue="engagements" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="engagements">
              Engagements ({userData.engagements.length})
            </TabsTrigger>
            <TabsTrigger value="documents">
              Documents ({userData.documents.length})
            </TabsTrigger>
            <TabsTrigger value="s3">
              S3 Objects ({userData.s3_objects.length})
            </TabsTrigger>
          </TabsList>

          <TabsContent value="engagements">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <User className="h-5 w-5" />
                  Engagements
                </CardTitle>
                <CardDescription>
                  Tax engagements and client matters
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[400px]">
                  {userData.engagements.length === 0 ? (
                    <p className="text-muted-foreground text-center py-8">
                      No engagements found
                    </p>
                  ) : (
                    <div className="space-y-4">
                      {userData.engagements.map((item) => (
                        <div key={item.id} className="border rounded-lg p-4">
                          <div className="flex items-start justify-between">
                            <div className="space-y-2">
                              <h4 className="font-medium">{item.name}</h4>
                              <div className="flex gap-2">
                                <Badge variant="secondary">
                                  {item.metadata?.type || 'Unknown'}
                                </Badge>
                                <Badge variant="outline">
                                  {item.metadata?.year || 'No Year'}
                                </Badge>
                              </div>
                              {item.created_at && (
                                <p className="text-sm text-muted-foreground">
                                  <Calendar className="h-3 w-3 inline mr-1" />
                                  Created: {formatDate(item.created_at)}
                                </p>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </ScrollArea>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="documents">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-5 w-5" />
                  Documents
                </CardTitle>
                <CardDescription>
                  Files and documents in DynamoDB
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[400px]">
                  {userData.documents.length === 0 ? (
                    <p className="text-muted-foreground text-center py-8">
                      No documents found
                    </p>
                  ) : (
                    <div className="space-y-4">
                      {userData.documents.map((item) => (
                        <div key={item.id} className="border rounded-lg p-4">
                          <div className="flex items-start justify-between">
                            <div className="space-y-2">
                              <h4 className="font-medium">{item.name}</h4>
                              {item.path && (
                                <p className="text-sm text-muted-foreground font-mono">
                                  <Folder className="h-3 w-3 inline mr-1" />
                                  {item.path}
                                </p>
                              )}
                              <div className="flex gap-2">
                                <Badge variant="secondary">
                                  {item.metadata?.type || 'file'}
                                </Badge>
                                {item.size && (
                                  <Badge variant="outline">
                                    {formatBytes(item.size)}
                                  </Badge>
                                )}
                              </div>
                              {item.updated_at && (
                                <p className="text-sm text-muted-foreground">
                                  <Calendar className="h-3 w-3 inline mr-1" />
                                  Updated: {formatDate(item.updated_at)}
                                </p>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </ScrollArea>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="s3">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Cloud className="h-5 w-5" />
                  S3 Objects
                </CardTitle>
                <CardDescription>
                  Files stored in S3 bucket
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[400px]">
                  {userData.s3_objects.length === 0 ? (
                    <p className="text-muted-foreground text-center py-8">
                      No S3 objects found
                    </p>
                  ) : (
                    <div className="space-y-4">
                      {userData.s3_objects.map((item) => (
                        <div key={item.id} className="border rounded-lg p-4">
                          <div className="flex items-start justify-between">
                            <div className="space-y-2">
                              <h4 className="font-medium">{item.name}</h4>
                              {item.path && (
                                <p className="text-sm text-muted-foreground font-mono">
                                  <Cloud className="h-3 w-3 inline mr-1" />
                                  {item.path}
                                </p>
                              )}
                              <div className="flex gap-2">
                                {item.size && (
                                  <Badge variant="outline">
                                    {formatBytes(item.size)}
                                  </Badge>
                                )}
                                <Badge variant="secondary">
                                  {item.metadata?.contentType || 'unknown'}
                                </Badge>
                              </div>
                              {item.updated_at && (
                                <p className="text-sm text-muted-foreground">
                                  <Calendar className="h-3 w-3 inline mr-1" />
                                  Modified: {formatDate(item.updated_at)}
                                </p>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </ScrollArea>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}

      {loading && !userData && (
        <Card>
          <CardContent className="p-6">
            <div className="flex items-center justify-center space-x-2">
              <RefreshCw className="h-4 w-4 animate-spin" />
              <p>Loading user data...</p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

