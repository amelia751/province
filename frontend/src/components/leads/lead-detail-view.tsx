'use client';

import { useState } from 'react';
import Link from 'next/link';

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
  raw: any;
}

interface LeadDetailViewProps {
  lead: Lead;
}

interface FeedbackState {
  type: 'positive' | 'negative' | null;
  note: string;
  submitted: boolean;
}

export default function LeadDetailView({ lead }: LeadDetailViewProps) {
  const [feedback, setFeedback] = useState<FeedbackState>({
    type: null,
    note: '',
    submitted: false
  });

  const handleFeedbackSubmit = async () => {
    if (!feedback.type) return;

    // TODO: Implement feedback submission to API
    console.log('Submitting feedback:', {
      leadId: lead.id,
      type: feedback.type,
      note: feedback.note
    });

    setFeedback(prev => ({ ...prev, submitted: true }));
  };

  const generateBrief = () => {
    // Generate a mock brief based on the lead data
    return {
      whatHappened: `A ${lead.practiceArea.toLowerCase()} case has emerged involving ${lead.title.toLowerCase()}. The case presents potential litigation opportunities based on the circumstances described in the source documents.`,
      partiesStatutes: `The case involves parties in ${lead.jurisdiction || 'the relevant jurisdiction'} and may implicate statutes related to ${lead.practiceArea === 'ADA Title III' ? 'the Americans with Disabilities Act Title III' : 'product liability law'}.`,
      jurisdictionTiming: `This case is proceeding in ${lead.jurisdiction || 'the applicable jurisdiction'}. Published on ${lead.publishedAt ? new Date(lead.publishedAt).toLocaleDateString() : 'recent date'}, indicating ${lead.publishedAt ? 'recent' : 'current'} developments.`,
      whyItFits: `This case aligns with your firm's focus on ${lead.practiceArea} matters. The confidence score of ${Math.round(lead.confidence * 100)}% indicates strong relevance to your practice areas and jurisdictional preferences.`,
      nextSteps: `Consider reviewing the source documents for additional details, evaluating the potential for client outreach, and monitoring for related developments in similar cases within your target jurisdictions.`
    };
  };

  const brief = generateBrief();

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center space-x-2 text-sm text-gray-600 mb-4">
          <Link href="/app" className="hover:text-black">
            Leads Dashboard
          </Link>
          <span>›</span>
          <span className="text-black">Lead Detail</span>
        </div>
        
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h1 className="text-2xl font-semibold text-black mb-2">
              {lead.title}
            </h1>
            <div className="flex items-center space-x-4 text-sm text-gray-600">
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                {lead.practiceArea}
              </span>
              {lead.jurisdiction && (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  {lead.jurisdiction}
                </span>
              )}
              <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                lead.confidence >= 0.8 ? 'bg-green-100 text-green-800' :
                lead.confidence >= 0.6 ? 'bg-yellow-100 text-yellow-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {Math.round(lead.confidence * 100)}% confidence
              </span>
              {lead.publishedAt && (
                <span>{new Date(lead.publishedAt).toLocaleDateString()}</span>
              )}
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <button className="px-4 py-2 border border-gray-200 text-gray-700 rounded-md hover:bg-gray-50 transition-colors">
              Share
            </button>
            <button className="px-4 py-2 bg-black text-white rounded-md hover:bg-gray-800 transition-colors">
              Add to Pipeline
            </button>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Content - Brief */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-black mb-4">Case Brief</h2>
            
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-2">What Happened</h3>
                <p className="text-sm text-gray-600 leading-relaxed">
                  {brief.whatHappened}
                </p>
              </div>
              
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-2">Parties & Statutes</h3>
                <p className="text-sm text-gray-600 leading-relaxed">
                  {brief.partiesStatutes}
                </p>
              </div>
              
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-2">Jurisdiction & Timing</h3>
                <p className="text-sm text-gray-600 leading-relaxed">
                  {brief.jurisdictionTiming}
                </p>
              </div>
              
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-2">Why This Fits Your Firm</h3>
                <p className="text-sm text-gray-600 leading-relaxed">
                  {brief.whyItFits}
                </p>
              </div>
              
              <div>
                <h3 className="text-sm font-medium text-gray-900 mb-2">Recommended Next Steps</h3>
                <p className="text-sm text-gray-600 leading-relaxed">
                  {brief.nextSteps}
                </p>
              </div>
            </div>
          </div>

          {/* Summary */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-black mb-4">Summary</h2>
            <p className="text-sm text-gray-600 leading-relaxed">
              {lead.summary}
            </p>
          </div>

          {/* Feedback Section */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-black mb-4">Feedback</h2>
            
            {!feedback.submitted ? (
              <div className="space-y-4">
                <div>
                  <p className="text-sm text-gray-600 mb-3">
                    Is this lead useful for your practice?
                  </p>
                  <div className="flex items-center space-x-4">
                    <button
                      onClick={() => setFeedback(prev => ({ ...prev, type: 'positive' }))}
                      className={`flex items-center space-x-2 px-3 py-2 rounded-md transition-colors ${
                        feedback.type === 'positive'
                          ? 'bg-green-100 text-green-800 border border-green-200'
                          : 'border border-gray-200 hover:bg-gray-50'
                      }`}
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L9 7v3m-3 10v-5a2 2 0 012-2h2.5" />
                      </svg>
                      <span className="text-sm">Useful</span>
                    </button>
                    
                    <button
                      onClick={() => setFeedback(prev => ({ ...prev, type: 'negative' }))}
                      className={`flex items-center space-x-2 px-3 py-2 rounded-md transition-colors ${
                        feedback.type === 'negative'
                          ? 'bg-red-100 text-red-800 border border-red-200'
                          : 'border border-gray-200 hover:bg-gray-50'
                      }`}
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018c.163 0 .326.02.485.06L17 4m-7 10v2a2 2 0 002 2h.095c.5 0 .905-.405.905-.905 0-.714.211-1.412.608-2.006L15 17v-3m-6-10v5a2 2 0 01-2 2H4.5" />
                      </svg>
                      <span className="text-sm">Not Useful</span>
                    </button>
                  </div>
                </div>
                
                {feedback.type && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Additional notes (optional)
                    </label>
                    <textarea
                      value={feedback.note}
                      onChange={(e) => setFeedback(prev => ({ ...prev, note: e.target.value }))}
                      placeholder="Tell us more about why this lead is or isn't useful..."
                      className="w-full px-3 py-2 border border-gray-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
                      rows={3}
                    />
                  </div>
                )}
                
                {feedback.type && (
                  <button
                    onClick={handleFeedbackSubmit}
                    className="px-4 py-2 bg-black text-white text-sm rounded-md hover:bg-gray-800 transition-colors"
                  >
                    Submit Feedback
                  </button>
                )}
              </div>
            ) : (
              <div className="flex items-center space-x-2 text-green-600">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-sm">Thank you for your feedback!</span>
              </div>
            )}
          </div>
        </div>

        {/* Sidebar - Sources */}
        <div className="space-y-6">
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-black mb-4">Sources</h2>
            
            <div className="space-y-4">
              <div className="border border-gray-100 rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <h3 className="text-sm font-medium text-gray-900">
                      {lead.source === 'courtlistener' ? 'CourtListener' :
                       lead.source === 'openfda' ? 'OpenFDA' :
                       lead.source === 'doj' ? 'DOJ ADA' : 'Unknown Source'}
                    </h3>
                    <p className="text-xs text-gray-500">Primary source</p>
                  </div>
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                    Active
                  </span>
                </div>
                
                <p className="text-sm text-gray-600 mb-3">
                  Original document from {lead.source} containing the case information and details.
                </p>
                
                <div className="flex items-center space-x-3">
                  {lead.url ? (
                    <a
                      href={lead.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center space-x-1 text-sm text-blue-600 hover:text-blue-800"
                    >
                      <span>View Original</span>
                      <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    </a>
                  ) : (
                    <span className="text-sm text-gray-400">No direct link available</span>
                  )}
                  
                  <button className="text-sm text-gray-600 hover:text-black">
                    Copy Link
                  </button>
                </div>
              </div>
              
              {/* Additional mock sources */}
              <div className="border border-gray-100 rounded-lg p-4">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <h3 className="text-sm font-medium text-gray-900">Related Cases</h3>
                    <p className="text-xs text-gray-500">Similar cases database</p>
                  </div>
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                    Reference
                  </span>
                </div>
                
                <p className="text-sm text-gray-600 mb-3">
                  Similar cases in your practice area that may provide additional context.
                </p>
                
                <div className="flex items-center space-x-3">
                  <button className="text-sm text-blue-600 hover:text-blue-800">
                    View Similar Cases
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Lead Metadata */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-black mb-4">Lead Details</h2>
            
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Lead ID</span>
                <span className="text-sm font-mono text-gray-900">{lead.id}</span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Source</span>
                <span className="text-sm text-gray-900">{lead.source}</span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Confidence</span>
                <span className="text-sm text-gray-900">{Math.round(lead.confidence * 100)}%</span>
              </div>
              
              <div className="flex justify-between">
                <span className="text-sm text-gray-600">Practice Area</span>
                <span className="text-sm text-gray-900">{lead.practiceArea}</span>
              </div>
              
              {lead.jurisdiction && (
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Jurisdiction</span>
                  <span className="text-sm text-gray-900">{lead.jurisdiction}</span>
                </div>
              )}
              
              {lead.publishedAt && (
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Published</span>
                  <span className="text-sm text-gray-900">
                    {new Date(lead.publishedAt).toLocaleDateString()}
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}