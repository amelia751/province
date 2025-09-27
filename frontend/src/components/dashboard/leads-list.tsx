'use client';

import { useState, useMemo } from 'react';
import { useRouter } from 'next/navigation';
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

interface LeadsListProps {
  leads: Lead[];
}

interface Filters {
  practiceArea: string;
  jurisdiction: string;
  confidence: string;
  date: string;
  status: string;
}

const ITEMS_PER_PAGE = 10;

export default function LeadsList({ leads }: LeadsListProps) {
  const router = useRouter();
  const [filters, setFilters] = useState<Filters>({
    practiceArea: 'all',
    jurisdiction: 'all',
    confidence: 'all',
    date: 'all',
    status: 'all'
  });
  
  const [currentPage, setCurrentPage] = useState(1);

  // Filter leads based on current filters
  const filteredLeads = useMemo(() => {
    return leads.filter(lead => {
      if (filters.practiceArea !== 'all' && lead.practiceArea !== filters.practiceArea) {
        return false;
      }
      
      if (filters.jurisdiction !== 'all' && lead.jurisdiction !== filters.jurisdiction) {
        return false;
      }
      
      if (filters.confidence !== 'all') {
        const confidenceLevel = lead.confidence >= 0.8 ? 'high' : 
                               lead.confidence >= 0.6 ? 'medium' : 'low';
        if (confidenceLevel !== filters.confidence) {
          return false;
        }
      }
      
      if (filters.date !== 'all' && lead.publishedAt) {
        const leadDate = new Date(lead.publishedAt);
        const now = new Date();
        const daysDiff = (now.getTime() - leadDate.getTime()) / (1000 * 60 * 60 * 24);
        
        switch (filters.date) {
          case 'today':
            if (daysDiff > 1) return false;
            break;
          case 'week':
            if (daysDiff > 7) return false;
            break;
          case 'month':
            if (daysDiff > 30) return false;
            break;
        }
      }
      
      return true;
    });
  }, [leads, filters]);

  // Paginate filtered leads
  const paginatedLeads = useMemo(() => {
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
    return filteredLeads.slice(startIndex, startIndex + ITEMS_PER_PAGE);
  }, [filteredLeads, currentPage]);

  const totalPages = Math.ceil(filteredLeads.length / ITEMS_PER_PAGE);

  const handleFilterChange = (filterType: keyof Filters, value: string) => {
    setFilters(prev => ({ ...prev, [filterType]: value }));
    setCurrentPage(1); // Reset to first page when filters change
  };

  const clearFilters = () => {
    setFilters({
      practiceArea: 'all',
      jurisdiction: 'all',
      confidence: 'all',
      date: 'all',
      status: 'all'
    });
    setCurrentPage(1);
  };
  // Get unique values for filter options
  const practiceAreas = [...new Set(leads.map(lead => lead.practiceArea))];
  const jurisdictions = [...new Set(leads.map(lead => lead.jurisdiction).filter(Boolean))];

  if (leads.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-gray-400 mb-4">
          <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <h3 className="text-sm font-medium text-gray-900 mb-2">No leads found</h3>
        <p className="text-sm text-gray-500 mb-6">
          Try adjusting your practice areas or check back later for new cases.
        </p>
        <button className="px-4 py-2 bg-black text-white text-sm rounded-md hover:bg-gray-800 transition-colors">
          Run Pipeline Now
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Filters */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <select 
            value={filters.practiceArea}
            onChange={(e) => handleFilterChange('practiceArea', e.target.value)}
            className="px-3 py-2 border border-gray-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
          >
            <option value="all">Practice area</option>
            {practiceAreas.map(area => (
              <option key={area} value={area}>{area}</option>
            ))}
          </select>
          
          <select 
            value={filters.jurisdiction}
            onChange={(e) => handleFilterChange('jurisdiction', e.target.value)}
            className="px-3 py-2 border border-gray-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
          >
            <option value="all">Jurisdiction</option>
            {jurisdictions.map(jurisdiction => (
              <option key={jurisdiction} value={jurisdiction}>{jurisdiction}</option>
            ))}
          </select>
          
          <select 
            value={filters.confidence}
            onChange={(e) => handleFilterChange('confidence', e.target.value)}
            className="px-3 py-2 border border-gray-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
          >
            <option value="all">Confidence</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
          
          <select 
            value={filters.date}
            onChange={(e) => handleFilterChange('date', e.target.value)}
            className="px-3 py-2 border border-gray-200 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
          >
            <option value="all">Date</option>
            <option value="today">Today</option>
            <option value="week">This Week</option>
            <option value="month">This Month</option>
          </select>
        </div>
        
        <div className="flex items-center space-x-4">
          <span className="text-sm text-gray-600">
            {filteredLeads.length} of {leads.length} leads
          </span>
          {(filters.practiceArea !== 'all' || filters.jurisdiction !== 'all' || 
            filters.confidence !== 'all' || filters.date !== 'all') && (
            <button 
              onClick={clearFilters}
              className="text-sm text-gray-600 hover:text-black underline"
            >
              Clear filters
            </button>
          )}
        </div>
      </div>

      {/* Bulk Actions */}
      <div className="flex items-center space-x-4 mb-6">
        <span className="text-sm font-medium text-black">Bulk actions</span>
        <button className="text-sm text-gray-600 hover:text-black">mark useful</button>
        <button className="text-sm text-gray-600 hover:text-black">snooze</button>
        <button className="text-sm text-gray-600 hover:text-black">assign</button>
      </div>

      {/* Empty state for filtered results */}
      {filteredLeads.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-gray-400 mb-4">
            <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <h3 className="text-sm font-medium text-gray-900 mb-2">No leads match your filters</h3>
          <p className="text-sm text-gray-500 mb-6">
            Try adjusting your filters or clearing them to see more results.
          </p>
          <button 
            onClick={clearFilters}
            className="px-4 py-2 bg-black text-white text-sm rounded-md hover:bg-gray-800 transition-colors"
          >
            Clear Filters
          </button>
        </div>
      ) : (
        <>
          {/* Leads List */}
          <div className="space-y-4">
            {paginatedLeads.map((lead) => (
              <div 
                key={lead.id} 
                className="border border-gray-200 rounded-lg p-6 hover:shadow-sm transition-shadow cursor-pointer bg-white"
                onClick={() => router.push(`/app/leads/${lead.id}`)}
              >
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-medium text-black mb-2 leading-tight">
                      {lead.title}
                    </h3>
                    <p className="text-sm text-gray-600 leading-relaxed mb-4">
                      {lead.summary}
                    </p>
                    <div className="flex items-center space-x-4 text-xs text-gray-500">
                      <span>Source {lead.source === 'courtlistener' ? '1' : lead.source === 'openfda' ? '2' : '3'}</span>
                      {lead.url && (
                        <a 
                          href={lead.url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-gray-500 hover:text-black"
                          onClick={(e) => e.stopPropagation()}
                        >
                          why fit
                        </a>
                      )}
                      {lead.publishedAt && (
                        <span>
                          {new Date(lead.publishedAt).toLocaleDateString()}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center space-x-3 ml-6">
                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                      lead.confidence >= 0.8 ? 'bg-black text-white' :
                      lead.confidence >= 0.6 ? 'bg-gray-600 text-white' :
                      'bg-gray-300 text-gray-700'
                    }`}>
                      {lead.confidence >= 0.8 ? 'High' : lead.confidence >= 0.6 ? 'Medium' : 'Low'}
                    </span>
                    <button 
                      className="p-1 text-gray-400 hover:text-black"
                      onClick={(e) => {
                        e.stopPropagation();
                        router.push(`/app/leads/${lead.id}`);
                      }}
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between border-t border-gray-200 pt-6">
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-600">
                  Showing {((currentPage - 1) * ITEMS_PER_PAGE) + 1} to {Math.min(currentPage * ITEMS_PER_PAGE, filteredLeads.length)} of {filteredLeads.length} results
                </span>
              </div>
              
              <div className="flex items-center space-x-2">
                <button
                  onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                  disabled={currentPage === 1}
                  className="px-3 py-2 text-sm border border-gray-200 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                
                <div className="flex items-center space-x-1">
                  {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
                    const pageNum = i + 1;
                    return (
                      <button
                        key={pageNum}
                        onClick={() => setCurrentPage(pageNum)}
                        className={`px-3 py-2 text-sm rounded-md ${
                          currentPage === pageNum
                            ? 'bg-black text-white'
                            : 'border border-gray-200 hover:bg-gray-50'
                        }`}
                      >
                        {pageNum}
                      </button>
                    );
                  })}
                  {totalPages > 5 && (
                    <>
                      <span className="px-2 text-gray-400">...</span>
                      <button
                        onClick={() => setCurrentPage(totalPages)}
                        className={`px-3 py-2 text-sm rounded-md ${
                          currentPage === totalPages
                            ? 'bg-black text-white'
                            : 'border border-gray-200 hover:bg-gray-50'
                        }`}
                      >
                        {totalPages}
                      </button>
                    </>
                  )}
                </div>
                
                <button
                  onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                  disabled={currentPage === totalPages}
                  className="px-3 py-2 text-sm border border-gray-200 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}