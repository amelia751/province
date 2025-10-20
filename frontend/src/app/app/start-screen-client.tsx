"use client";

import React, { useState, useEffect } from "react";
import { useRouter, usePathname } from 'next/navigation';
import { useUser } from '@clerk/nextjs';
import { cn } from "@/lib/utils";
import Lottie from 'lottie-react';
import managingActionsAnimation from '@/../public/animation/managing_actions.json';
import {
  Upload,
  Plus,
  CalendarIcon,
  ChevronDown,
  MessageSquare,
  Settings,
  Download,
  FileText,
  CheckCircle2,
  Clock,
  DollarSign,
  Users,
  ChevronRight,
  AlertCircle,
  FolderOpen,
  Archive,
  Send,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Calendar } from "@/components/ui/calendar";

// Mock data - replace with real data from backend
interface TaxFiling {
  id: string;
  year: number;
  status: 'draft' | 'waiting_approval' | 'filed' | 'archived';
  refundAmount?: number;
  lastUpdated: Date;
  formType: string;
}

const mockFilings: TaxFiling[] = [
  {
    id: 'tax-2025-001',
    year: 2025,
    status: 'draft',
    refundAmount: 192,
    lastUpdated: new Date('2025-10-05'),
    formType: 'Federal 1040',
  },
  {
    id: 'tax-2024-001',
    year: 2024,
    status: 'filed',
    refundAmount: 1240,
    lastUpdated: new Date('2024-04-15'),
    formType: 'Federal 1040',
  },
  {
    id: 'tax-2023-001',
    year: 2023,
    status: 'archived',
    refundAmount: 856,
    lastUpdated: new Date('2023-04-12'),
    formType: 'Federal 1040',
  },
];

// Mock tax deadlines
interface TaxDeadline {
  date: Date;
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
}

const mockDeadlines: TaxDeadline[] = [
  {
    date: new Date('2026-01-31'),
    title: 'W-2 Forms Due',
    description: 'Employers must send W-2 forms to employees',
    priority: 'medium',
  },
  {
    date: new Date('2026-04-15'),
    title: 'Tax Filing Deadline',
    description: 'Individual income tax returns due (Form 1040)',
    priority: 'high',
  },
  {
    date: new Date('2026-03-15'),
    title: 'S-Corp/Partnership Deadline',
    description: 'S-Corporation and Partnership returns due',
    priority: 'medium',
  },
  {
    date: new Date('2026-01-15'),
    title: 'Q4 2025 Estimated Tax',
    description: 'Fourth quarter estimated tax payment due',
    priority: 'high',
  },
];

export default function StartScreenClient() {
  const router = useRouter();
  const pathname = usePathname();
  const { user } = useUser();
  const [selectedYear, setSelectedYear] = useState<number>(2025);
  const [isPastFilingsOpen, setIsPastFilingsOpen] = useState(false);
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(new Date());
  const [currentEngagementId, setCurrentEngagementId] = useState<string | null>(null);
  const [isCreatingEngagement, setIsCreatingEngagement] = useState(false);
  const [hasCheckedEngagement, setHasCheckedEngagement] = useState(false);

  const currentFiling = mockFilings.find(f => f.year === selectedYear);
  const pastFilings = mockFilings.filter(f => f.year < selectedYear);


  // Get deadlines for selected calendar month
  const today = new Date();
  const calendarMonth = selectedDate?.getMonth() ?? today.getMonth();
  const calendarYear = selectedDate?.getFullYear() ?? today.getFullYear();

  const deadlinesThisMonth = mockDeadlines
    .filter(d => {
      const deadlineMonth = d.date.getMonth();
      const deadlineYear = d.date.getFullYear();
      return deadlineMonth === calendarMonth && deadlineYear === calendarYear;
    })
    .sort((a, b) => a.date.getTime() - b.date.getTime());

  // Get dates with deadlines for calendar highlighting
  const deadlineDates = mockDeadlines.map(d => d.date);

  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'draft':
        return { label: 'Draft Ready', color: 'bg-yellow-500', textColor: 'text-yellow-500', icon: Clock };
      case 'waiting_approval':
        return { label: 'Waiting for approval', color: 'bg-yellow-500', textColor: 'text-yellow-500', icon: Clock };
      case 'filed':
        return { label: 'Filed', color: 'bg-green-600', textColor: 'text-green-600', icon: Send };
      case 'archived':
        return { label: 'Archived', color: 'bg-gray-500', textColor: 'text-gray-500', icon: Archive };
      default:
        return { label: status, color: 'bg-gray-500', textColor: 'text-gray-500', icon: FileText };
    }
  };

  // Create or get tax engagement for the current year
  const createTaxEngagement = async (filingYear: number) => {
    if (!user) return null;

    setIsCreatingEngagement(true);
    try {
      const response = await fetch('/api/tax-engagements', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ filingYear }),
      });

      if (!response.ok) {
        throw new Error('Failed to create tax engagement');
      }

      const result = await response.json();
      setCurrentEngagementId(result.engagementId);
      setHasCheckedEngagement(true); // Mark as checked since we just created it
      return result.engagementId;
    } catch (error) {
      console.error('Error creating tax engagement:', error);
      return null;
    } finally {
      setIsCreatingEngagement(false);
    }
  };

  // Fetch existing tax engagement for the year
  const fetchTaxEngagement = async (filingYear: number) => {
    if (!user) return null;

    try {
      const response = await fetch(`/api/tax-engagements?filingYear=${filingYear}`);
      
      if (!response.ok) {
        return null;
      }

      const result = await response.json();
      const engagements = result.engagements || [];

      // Check if any engagement exists for this year
      const hasEngagement = engagements.length > 0;

      if (hasEngagement) {
        const engagement = engagements[0]; // Take the first engagement
        setCurrentEngagementId(engagement.engagementId);
        return engagement.engagementId;
      } else {
        setCurrentEngagementId(null);
      }
      
      return null;
    } catch (error) {
      console.error('Error fetching tax engagement:', error);
      return null;
    }
  };

  // Manual refresh function
  const refreshEngagementState = async () => {
    setHasCheckedEngagement(false);
    setCurrentEngagementId(null);
    if (user && selectedYear) {
      await fetchTaxEngagement(selectedYear);
      setHasCheckedEngagement(true);
    }
  };

  // Reset check flag when year changes
  useEffect(() => {
    setHasCheckedEngagement(false);
    setCurrentEngagementId(null);
  }, [selectedYear]);

  // Load engagement on component mount and year change
  useEffect(() => {
    if (user && selectedYear && !hasCheckedEngagement) {
      fetchTaxEngagement(selectedYear).then(() => {
        setHasCheckedEngagement(true);
      });
    }
  }, [user, selectedYear, hasCheckedEngagement]);

  // Reset and refetch when component becomes visible (user navigates back)
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden && user && selectedYear) {
        // Reset and refetch when page becomes visible
        setHasCheckedEngagement(false);
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    // Also reset on focus (when user comes back to tab/window)
    const handleFocus = () => {
      if (user && selectedYear) {
        setHasCheckedEngagement(false);
      }
    };

    window.addEventListener('focus', handleFocus);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('focus', handleFocus);
    };
  }, [user, selectedYear]);

  // Refresh engagement state when navigating back to this page
  useEffect(() => {
    if (pathname === '/app' && user && selectedYear) {
      refreshEngagementState();
    }
  }, [pathname, user, selectedYear]);

  const handleStartNewFiling = async () => {
    const engagementId = await createTaxEngagement(selectedYear);
    if (engagementId) {
      router.push(`/app/project/${engagementId}`);
    }
  };

  const handleOpenFiling = async (filing: TaxFiling) => {
    if (isCreatingEngagement) return; // Prevent duplicate calls
    
    // Check if we have an engagement for this year, create if not
    let engagementId = currentEngagementId;
    
    if (!engagementId) {
      engagementId = await createTaxEngagement(filing.year);
    }
    
    if (engagementId) {
      router.push(`/app/project/${engagementId}`);
    } else {
      // Fallback to old behavior
      router.push(`/app/project/${filing.id}`);
    }
  };

  const handleUploadDocuments = async () => {
    if (isCreatingEngagement) return; // Prevent duplicate calls
    
    // Ensure we have an engagement for document uploads
    let engagementId = currentEngagementId;
    
    if (!engagementId) {
      engagementId = await createTaxEngagement(selectedYear);
    }
    
    if (engagementId) {
      // For now, we'll redirect to project page where document upload will be available
      router.push(`/app/project/${engagementId}`);
    }
  };

  const handleUploadDocumentsOld = () => {
    router.push('/app/tax/upload');
  };

  const handleOpenChat = () => {
    router.push('/app/chat');
  };

  return (
    <div className="h-full bg-background overflow-auto">
      <div className="max-w-7xl mx-auto px-6 py-8">

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Current Year Overview + Past Filings */}
          <div className="lg:col-span-2 space-y-6">
            {/* Current Year Row - Split between filing and actions */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Current Year Overview Card */}
              {currentFiling ? (
                <Card className="border shadow-none">
                <CardHeader className="flex flex-col h-full">
                  <div className="flex items-center justify-between pb-4 border-b">
                    <CardTitle className="text-2xl">
                      {currentFiling.year} Return
                    </CardTitle>
                    <Button
                      onClick={() => handleOpenFiling(currentFiling)}
                      disabled={isCreatingEngagement}
                      className="bg-true-turquoise text-white hover:bg-true-turquoise/90 disabled:opacity-50"
                    >
                      {currentEngagementId ? (
                        <>
                          <FileText className="h-4 w-4 mr-2" />
                          {isCreatingEngagement ? 'Creating...' : 'Open Folder'}
                        </>
                      ) : (
                        <>
                          <Plus className="h-4 w-4 mr-2" />
                          {isCreatingEngagement ? 'Creating...' : 'Start Filing'}
                        </>
                      )}
                    </Button>
                  </div>
                  {currentEngagementId ? (
                    currentFiling.refundAmount && (
                      <div className="flex-1 flex items-center justify-center text-center">
                        <div>
                          <div className="text-5xl font-semibold text-gray-700 mb-2">
                            ${currentFiling.refundAmount.toLocaleString()}
                          </div>
                          <div className="text-sm text-muted-foreground tracking-wider uppercase">
                            Total {currentFiling.year} Tax Refund
                          </div>
                        </div>
                      </div>
                    )
                  ) : (
                    <div className="flex-1 flex items-center justify-center text-center">
                      <div>
                        <div className="text-lg text-gray-600 mb-2">
                          Ready to start your {currentFiling.year} tax return
                        </div>
                        <div className="text-sm text-muted-foreground">
                          Click "Start Filing" to create your tax engagement
                        </div>
                      </div>
                    </div>
                  )}
                </CardHeader>
              </Card>
              ) : (
                <Card className="border border-dashed shadow-none">
                <CardHeader>
                  <CardTitle className="text-2xl">Let's start your {selectedYear} tax return</CardTitle>
                  <CardDescription className="text-base">
                    Upload your W-2, 1099, or other income documents to begin.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex space-x-3">
                    <Button 
                      onClick={handleStartNewFiling} 
                      disabled={isCreatingEngagement}
                      size="lg"
                    >
                      <Plus className="h-5 w-5 mr-2" />
                      {isCreatingEngagement ? 'Creating...' : 'Start Filing'}
                    </Button>
                    <Button 
                      variant="outline" 
                      onClick={handleUploadDocuments} 
                      disabled={isCreatingEngagement}
                      size="lg"
                    >
                      <Upload className="h-5 w-5 mr-2" />
                      Upload Documents
                    </Button>
                  </div>
                </CardContent>
              </Card>
              )}

              {/* Managing Actions Animation */}
              <div className="hidden md:flex items-center justify-center overflow-hidden">
                <Lottie
                  animationData={managingActionsAnimation}
                  loop={true}
                  className="w-72 h-72"
                  style={{ transform: 'scale(1.2)' }}
                />
              </div>
            </div>

            {/* Past Filings Section */}
            {pastFilings.length > 0 && (
              <Collapsible open={isPastFilingsOpen} onOpenChange={setIsPastFilingsOpen}>
                <Card className="shadow-none">
                  <CollapsibleTrigger asChild>
                    <CardHeader className="cursor-pointer transition-colors">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-xl">Past Filings</CardTitle>
                        <ChevronDown className={cn(
                          "h-5 w-5 transition-transform",
                          isPastFilingsOpen && "transform rotate-180"
                        )} />
                      </div>
                    </CardHeader>
                  </CollapsibleTrigger>
                  <CollapsibleContent>
                    <CardContent className="space-y-3 pt-4">
                      {pastFilings.map((filing) => {
                        const StatusIcon = getStatusConfig(filing.status).icon;
                        return (
                          <div
                            key={filing.year}
                            className="flex items-center justify-between p-4 border border-gray-200 rounded-lg"
                          >
                            <div className="flex items-center space-x-4">
                              <StatusIcon className="h-5 w-5 text-gray-500" />
                              <div className="flex flex-col gap-2">
                                <div className="font-medium text-gray-700">
                                  {filing.year} – ${filing.refundAmount?.toLocaleString() || 0} Refund
                                </div>
                                <Badge variant="secondary" className={cn("flex items-center space-x-1 w-fit",
                                  filing.status === 'filed' ? "bg-true-turquoise text-white border-true-turquoise" :
                                  filing.status === 'archived' ? "bg-dark-ecru text-darker-ecru border-dark-ecru" :
                                  getStatusConfig(filing.status).textColor
                                )}>
                                  <div className={cn("h-1.5 w-1.5 rounded-full",
                                    filing.status === 'filed' ? "bg-white" :
                                    filing.status === 'archived' ? "bg-darker-ecru" :
                                    getStatusConfig(filing.status).color
                                  )} />
                                  <span>{getStatusConfig(filing.status).label}</span>
                                </Badge>
                              </div>
                            </div>
                            <div className="flex items-center space-x-2">
                              {filing.status === 'filed' && (
                                <Button size="sm" className="bg-paper-white text-gray-600 hover:bg-true-turquoise hover:text-white">
                                  <Download className="h-4 w-4 mr-1" />
                                  Download
                                </Button>
                              )}
                              {filing.status === 'archived' && (
                                <Button size="sm" className="bg-paper-white text-gray-600 hover:bg-true-turquoise hover:text-white">
                                  <FolderOpen className="h-4 w-4 mr-1" />
                                  Reopen
                                </Button>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </CardContent>
                  </CollapsibleContent>
                </Card>
              </Collapsible>
            )}
          </div>

          {/* Right Column - Calendar & Deadlines */}
          <div className="space-y-6">
            {/* Tax Calendar & Deadlines */}
            <div className="space-y-4">
              {/* Calendar and Deadlines Row */}
              <div className="flex flex-row justify-between items-end sm:items-start lg:items-end gap-4">
                {/* Mini Calendar */}
                <div className="flex justify-start bg-white w-auto">
                  <Calendar
                    mode="single"
                    selected={selectedDate}
                    onSelect={setSelectedDate}
                    className="rounded-md border bg-white"
                    modifiers={{
                      deadline: deadlineDates,
                    }}
                    modifiersClassNames={{
                      deadline: "bg-boysenberry text-white font-bold rounded-sm",
                    }}
                  />
                </div>
                {/* Deadline List on small and medium screens - horizontal next to calendar */}
                {deadlinesThisMonth.length > 0 && (
                  <div className="hidden sm:flex lg:hidden flex-col space-y-2 flex-1">
                    {deadlinesThisMonth.map((deadline, idx) => {
                      const daysUntil = Math.ceil((deadline.date.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
                      const priorityColor = deadline.priority === 'high' ? 'text-boysenberry' : deadline.priority === 'medium' ? 'text-terra-cotta' : 'text-gray-600';
                      const badgeColor = deadline.priority === 'high' ? 'bg-boysenberry text-white' : deadline.priority === 'medium' ? 'bg-terra-cotta text-white' : 'bg-gray-200 text-gray-800';

                      return (
                        <div key={idx} className="p-3 border rounded-lg space-y-1">
                          <div className="flex items-start justify-between">
                            <div className="flex items-start space-x-2">
                              <AlertCircle className={cn("h-4 w-4 mt-0.5", priorityColor)} />
                              <div>
                                <div className="font-medium text-sm">{deadline.title}</div>
                                <div className="text-xs text-muted-foreground">{deadline.description}</div>
                              </div>
                            </div>
                          </div>
                          <div className="flex items-center justify-between text-xs">
                            <span className="text-muted-foreground">
                              {deadline.date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                            </span>
                            <Badge className={cn("text-xs", badgeColor)}>
                              {daysUntil} days
                            </Badge>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Deadline List - default vertical layout on mobile and large screens */}
              {deadlinesThisMonth.length > 0 ? (
                <div className="sm:hidden lg:block space-y-2 max-w-[320px]">
                  {deadlinesThisMonth.map((deadline, idx) => {
                    const daysUntil = Math.ceil((deadline.date.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
                    const priorityColor = deadline.priority === 'high' ? 'text-boysenberry' : deadline.priority === 'medium' ? 'text-terra-cotta' : 'text-gray-600';
                    const badgeColor = deadline.priority === 'high' ? 'bg-boysenberry text-white' : deadline.priority === 'medium' ? 'bg-terra-cotta text-white' : 'bg-gray-200 text-gray-800';

                    return (
                      <div key={idx} className="p-3 border rounded-lg space-y-1">
                        <div className="flex items-start justify-between">
                          <div className="flex items-start space-x-2">
                            <AlertCircle className={cn("h-4 w-4 mt-0.5", priorityColor)} />
                            <div>
                              <div className="font-medium text-sm">{deadline.title}</div>
                              <div className="text-xs text-muted-foreground">{deadline.description}</div>
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-muted-foreground">
                            {deadline.date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                          </span>
                          <Badge className={cn("text-xs", badgeColor)}>
                            {daysUntil} days
                          </Badge>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="text-center py-6 max-w-[320px]">
                  <p className="text-sm text-muted-foreground">No deadlines this month</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
