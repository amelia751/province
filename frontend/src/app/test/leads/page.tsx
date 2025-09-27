'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

interface Lead {
  id: string;
  title: string;
  source: string;
  confidence: number;
  practiceArea: string;
  jurisdiction?: string;
  summary: string;
  url?: string;
  publishedAt?: string;
}

export default function LeadsTestPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [leads, setLeads] = useState<Lead[]>([]);
  const [error, setError] = useState<string | null>(null);

  const fetchLeads = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/leads');
      const data = await response.json();

      if (data.success) {
        setLeads(data.leads);
      } else {
        setError(data.error || 'Failed to fetch leads');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-4">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="text-center py-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Leads Detection Test
          </h1>
          <p className="text-xl text-gray-600">
            Test the lead detection system with your organization's settings
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Fetch Leads</CardTitle>
            <CardDescription>
              This will fetch and analyze recent cases from CourtListener, OpenFDA, and DOJ based on your organization's practice areas and preferences.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button 
              onClick={fetchLeads} 
              disabled={isLoading}
              className="w-full"
            >
              {isLoading ? 'Analyzing Cases...' : 'Fetch Relevant Leads'}
            </Button>
          </CardContent>
        </Card>

        {error && (
          <Card className="border-red-200">
            <CardHeader>
              <CardTitle className="text-red-600">Error</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-red-600">{error}</p>
            </CardContent>
          </Card>
        )}

        {leads.length > 0 && (
          <div className="space-y-4">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-gray-900">
                Found {leads.length} Relevant Leads
              </h2>
              <p className="text-gray-600">
                Sorted by relevance to your practice areas
              </p>
            </div>

            {leads.map((lead) => (
              <Card key={lead.id} className="hover:shadow-md transition-shadow">
                <CardHeader>
                  <div className="flex justify-between items-start">
                    <div className="flex-1">
                      <CardTitle className="text-lg">{lead.title}</CardTitle>
                      <CardDescription className="mt-1">
                        {lead.source.toUpperCase()} • {lead.practiceArea}
                        {lead.jurisdiction && ` • ${lead.jurisdiction}`}
                      </CardDescription>
                    </div>
                    <div className="ml-4 flex flex-col items-end">
                      <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                        lead.confidence >= 0.8 ? 'bg-green-100 text-green-800' :
                        lead.confidence >= 0.6 ? 'bg-yellow-100 text-yellow-800' :
                        lead.confidence >= 0.4 ? 'bg-orange-100 text-orange-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {Math.round(lead.confidence * 100)}% match
                      </div>
                      {lead.publishedAt && (
                        <div className="text-xs text-gray-500 mt-1">
                          {new Date(lead.publishedAt).toLocaleDateString()}
                        </div>
                      )}
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-600 mb-3 leading-relaxed">
                    {lead.summary}
                  </p>
                  <div className="flex justify-between items-center">
                    {lead.url && (
                      <a 
                        href={lead.url} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline text-sm font-medium"
                      >
                        View Original Source →
                      </a>
                    )}
                    <div className="text-xs text-gray-400">
                      ID: {lead.id.slice(-8)}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        <div className="text-center py-4">
          <a 
            href="/app" 
            className="text-blue-600 hover:underline"
          >
            ← Back to Dashboard
          </a>
        </div>
      </div>
    </div>
  );
}