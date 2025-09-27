'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

interface Lead {
  id: string;
  confidence: number;
  practiceArea: string;
  source: string;
  publishedAt?: string;
}

interface Organization {
  practice_areas: string[];
  jurisdictions: string[];
  source_courtlistener: boolean;
  source_openfda: boolean;
  source_doj: boolean;
  source_rss: boolean;
  digest_enabled: boolean;
  billing: string;
  trial_ends_at?: string;
}

interface StatsOverviewProps {
  leads: Lead[];
  organization: Organization;
}

export default function StatsOverview({ leads, organization }: StatsOverviewProps) {
  // Calculate stats
  const totalLeads = leads.length;
  const highConfidenceLeads = leads.filter(lead => lead.confidence >= 0.7).length;
  const todayLeads = leads.filter(lead => {
    if (!lead.publishedAt) return false;
    const today = new Date();
    const leadDate = new Date(lead.publishedAt);
    return leadDate.toDateString() === today.toDateString();
  }).length;

  // Practice area breakdown
  const practiceAreaStats = organization.practice_areas.reduce((acc, area) => {
    acc[area] = leads.filter(lead => lead.practiceArea === area).length;
    return acc;
  }, {} as Record<string, number>);

  // Source breakdown
  const sourceStats = {
    courtlistener: leads.filter(lead => lead.source === 'courtlistener').length,
    openfda: leads.filter(lead => lead.source === 'openfda').length,
    doj: leads.filter(lead => lead.source === 'doj').length,
  };

  const activeSources = [
    organization.source_courtlistener && 'CourtListener',
    organization.source_openfda && 'OpenFDA', 
    organization.source_doj && 'DOJ ADA',
    organization.source_rss && 'RSS Feeds'
  ].filter(Boolean).length;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {/* Total Leads */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Leads</CardTitle>
          <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{totalLeads}</div>
          <p className="text-xs text-muted-foreground">
            {todayLeads} new today
          </p>
        </CardContent>
      </Card>

      {/* High Confidence */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">High Confidence</CardTitle>
          <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{highConfidenceLeads}</div>
          <p className="text-xs text-muted-foreground">
            {totalLeads > 0 ? Math.round((highConfidenceLeads / totalLeads) * 100) : 0}% of total
          </p>
        </CardContent>
      </Card>

      {/* Active Sources */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Active Sources</CardTitle>
          <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9v-9m0-9v9" />
          </svg>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{activeSources}</div>
          <p className="text-xs text-muted-foreground">
            Data sources enabled
          </p>
        </CardContent>
      </Card>

      {/* Account Status */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Account Status</CardTitle>
          <svg className="h-4 w-4 text-muted-foreground" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
          </svg>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold capitalize">{organization.billing}</div>
          <p className="text-xs text-muted-foreground">
            {organization.trial_ends_at && organization.billing === 'trial' 
              ? `Ends ${new Date(organization.trial_ends_at).toLocaleDateString()}`
              : 'Active subscription'
            }
          </p>
        </CardContent>
      </Card>

      {/* Practice Areas Breakdown */}
      {Object.keys(practiceAreaStats).length > 0 && (
        <Card className="md:col-span-2">
          <CardHeader>
            <CardTitle className="text-sm font-medium">Practice Areas</CardTitle>
            <CardDescription>Lead distribution by practice area</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(practiceAreaStats).map(([area, count]) => (
                <div key={area} className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    <span className="text-sm font-medium">{area}</span>
                  </div>
                  <span className="text-sm text-gray-600">{count} leads</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Source Performance */}
      <Card className="md:col-span-2">
        <CardHeader>
          <CardTitle className="text-sm font-medium">Source Performance</CardTitle>
          <CardDescription>Leads by data source</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${organization.source_courtlistener ? 'bg-green-500' : 'bg-gray-300'}`}></div>
                <span className="text-sm font-medium">CourtListener</span>
              </div>
              <span className="text-sm text-gray-600">{sourceStats.courtlistener} leads</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${organization.source_openfda ? 'bg-green-500' : 'bg-gray-300'}`}></div>
                <span className="text-sm font-medium">OpenFDA</span>
              </div>
              <span className="text-sm text-gray-600">{sourceStats.openfda} leads</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${organization.source_doj ? 'bg-green-500' : 'bg-gray-300'}`}></div>
                <span className="text-sm font-medium">DOJ ADA</span>
              </div>
              <span className="text-sm text-gray-600">{sourceStats.doj} leads</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}