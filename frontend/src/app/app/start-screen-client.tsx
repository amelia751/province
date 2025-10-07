"use client";

import React, { useState } from "react";
import { useRouter } from 'next/navigation';
import { useUser } from '@clerk/nextjs';
import { cn } from "@/lib/utils";
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
  const { user } = useUser();
  const [selectedYear, setSelectedYear] = useState<number>(2025);
  const [isPastFilingsOpen, setIsPastFilingsOpen] = useState(false);
  const [selectedDate, setSelectedDate] = useState<Date | undefined>(new Date());

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
        return { label: 'Draft Ready', color: 'bg-yellow-500', icon: Clock };
      case 'waiting_approval':
        return { label: 'Waiting for approval', color: 'bg-yellow-500', icon: Clock };
      case 'filed':
        return { label: 'Filed', color: 'bg-green-500', icon: CheckCircle2 };
      case 'archived':
        return { label: 'Archived', color: 'bg-gray-500', icon: FileText };
      default:
        return { label: status, color: 'bg-gray-500', icon: FileText };
    }
  };

  const handleStartNewFiling = () => {
    // Create new project for tax filing
    const newProjectId = `tax-${selectedYear}-${Date.now()}`;
    router.push(`/app/project/${newProjectId}`);
  };

  const handleOpenFiling = (filing: TaxFiling) => {
    router.push(`/app/project/${filing.id}`);
  };

  const handleUploadDocuments = () => {
    router.push('/app/tax/upload');
  };

  const handleOpenChat = () => {
    router.push('/app/chat');
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Top Header Bar */}
      <div className="border-b bg-white sticky top-0 z-10">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Left: Title */}
            <div className="flex items-center space-x-4">
              <h1 className="text-xl font-semibold">Your Tax Workspace</h1>
            </div>

            {/* Right: Tax Year Switcher, Profile, Chat */}
            <div className="flex items-center space-x-4">
              <Select value={selectedYear.toString()} onValueChange={(val) => setSelectedYear(parseInt(val))}>
                <SelectTrigger className="w-32">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="2025">2025</SelectItem>
                  <SelectItem value="2024">2024</SelectItem>
                  <SelectItem value="2023">2023</SelectItem>
                  <SelectItem value="2022">2022</SelectItem>
                </SelectContent>
              </Select>

              {/* Help / Chat Icon */}
              <Button variant="ghost" size="icon" onClick={handleOpenChat}>
                <MessageSquare className="h-5 w-5" />
              </Button>

              {/* Profile Menu */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="flex items-center space-x-2">
                    <div className="h-8 w-8 rounded-full bg-black text-white flex items-center justify-center text-sm font-medium">
                      {user?.firstName?.[0] || user?.emailAddresses[0]?.emailAddress[0].toUpperCase() || 'U'}
                    </div>
                    <ChevronDown className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-48">
                  <DropdownMenuItem>
                    <Settings className="h-4 w-4 mr-2" />
                    Settings
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem>Sign out</DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-auto">
        <div className="max-w-7xl mx-auto px-6 py-8">

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Current Year Overview + Past Filings */}
          <div className="lg:col-span-2 space-y-6">
            {/* Current Year Overview Card */}
            {currentFiling ? (
              <Card className="border-2">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-2xl mb-2">
                        {currentFiling.year} {currentFiling.formType}
                      </CardTitle>
                      <div className="flex items-center space-x-3">
                        <Badge variant="secondary" className="flex items-center space-x-1">
                          <div className={cn("h-2 w-2 rounded-full", getStatusConfig(currentFiling.status).color)} />
                          <span>{getStatusConfig(currentFiling.status).label}</span>
                        </Badge>
                        {currentFiling.refundAmount && (
                          <div className="flex items-center space-x-1 text-green-600 font-medium">
                            <DollarSign className="h-4 w-4" />
                            <span>Refund estimate: ${currentFiling.refundAmount.toLocaleString()}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex space-x-3">
                    <Button onClick={() => handleOpenFiling(currentFiling)}>
                      <FileText className="h-4 w-4 mr-2" />
                      Open Folder
                    </Button>
                    <Button variant="outline" onClick={() => handleOpenFiling(currentFiling)}>
                      Continue Review
                      <ChevronRight className="h-4 w-4 ml-2" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card className="border-2 border-dashed">
                <CardHeader>
                  <CardTitle className="text-2xl">Let's start your {selectedYear} tax return</CardTitle>
                  <CardDescription className="text-base">
                    Upload your W-2, 1099, or other income documents to begin.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex space-x-3">
                    <Button onClick={handleStartNewFiling} size="lg">
                      <Plus className="h-5 w-5 mr-2" />
                      Start New Filing
                    </Button>
                    <Button variant="outline" onClick={handleUploadDocuments} size="lg">
                      <Upload className="h-5 w-5 mr-2" />
                      Upload Documents
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Past Filings Section */}
            {pastFilings.length > 0 && (
              <Collapsible open={isPastFilingsOpen} onOpenChange={setIsPastFilingsOpen}>
                <Card>
                  <CollapsibleTrigger asChild>
                    <CardHeader className="cursor-pointer hover:bg-muted/50 transition-colors">
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
                    <CardContent className="space-y-3 pt-0">
                      {pastFilings.map((filing) => {
                        const StatusIcon = getStatusConfig(filing.status).icon;
                        return (
                          <div
                            key={filing.year}
                            className="flex items-center justify-between p-4 border rounded-lg hover:bg-muted/50 transition-colors cursor-pointer"
                            onClick={() => handleOpenFiling(filing)}
                          >
                            <div className="flex items-center space-x-4">
                              <StatusIcon className="h-5 w-5 text-muted-foreground" />
                              <div>
                                <div className="font-medium">{filing.year} – {getStatusConfig(filing.status).label}</div>
                                {filing.refundAmount && (
                                  <div className="text-sm text-green-600">
                                    Refund: ${filing.refundAmount.toLocaleString()}
                                  </div>
                                )}
                              </div>
                            </div>
                            <div className="flex items-center space-x-2">
                              <Button variant="ghost" size="sm">
                                View Summary
                              </Button>
                              {filing.status === 'filed' && (
                                <Button variant="ghost" size="sm">
                                  <Download className="h-4 w-4 mr-1" />
                                  Download
                                </Button>
                              )}
                              {filing.status === 'archived' && (
                                <Button variant="ghost" size="sm">
                                  Reopen for Amendment
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
              {/* Mini Calendar */}
              <div className="flex justify-center">
                <Calendar
                  mode="single"
                  selected={selectedDate}
                  onSelect={setSelectedDate}
                  className="rounded-md border"
                  modifiers={{
                    deadline: deadlineDates,
                  }}
                  modifiersClassNames={{
                    deadline: "bg-red-100 text-red-900 font-bold rounded-md",
                  }}
                />
              </div>

              {/* Deadline List */}
              {deadlinesThisMonth.length > 0 ? (
                <div className="space-y-2">
                  {deadlinesThisMonth.map((deadline, idx) => {
                    const daysUntil = Math.ceil((deadline.date.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
                    const priorityColor = deadline.priority === 'high' ? 'text-red-600' : deadline.priority === 'medium' ? 'text-yellow-600' : 'text-gray-600';

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
                          <Badge variant={deadline.priority === 'high' ? 'destructive' : 'secondary'} className="text-xs">
                            {daysUntil} days
                          </Badge>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="text-center py-6">
                  <p className="text-sm text-muted-foreground">No deadlines this month</p>
                </div>
              )}
            </div>
          </div>
        </div>
        </div>
      </div>
    </div>
  );
}

