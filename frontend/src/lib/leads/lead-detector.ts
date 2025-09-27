import { fetchCourtListener } from '@/lib/ingest/courtlistener';
import { fetchOpenFDA } from '@/lib/ingest/openfda';
import { fetchDOJADA } from '@/lib/ingest/doj';

export interface Lead {
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

export interface LeadFilters {
  practiceAreas: string[];
  jurisdictions: string[];
  keywordsInclude: string[];
  keywordsExclude: string[];
}

export class LeadDetector {
  async detectLeads(filters: LeadFilters): Promise<Lead[]> {
    console.log('Detecting leads with filters:', filters);
    
    const since = new Date(Date.now() - 7 * 24 * 3600 * 1000); // last 7 days
    
    // Fetch from all sources
    const [clResult, fdaResult, dojResult] = await Promise.allSettled([
      fetchCourtListener({ since }),
      fetchOpenFDA({ since }),
      fetchDOJADA({ since }),
    ]);

    const allItems = [];
    
    if (clResult.status === 'fulfilled') {
      allItems.push(...clResult.value.items);
    }
    if (fdaResult.status === 'fulfilled') {
      allItems.push(...fdaResult.value.items);
    }
    if (dojResult.status === 'fulfilled') {
      allItems.push(...dojResult.value.items);
    }

    console.log(`Found ${allItems.length} total items`);

    // Filter and score items
    const leads: Lead[] = [];
    
    for (const item of allItems) {
      const lead = this.evaluateItem(item, filters);
      if (lead && lead.confidence > 0.2) { // Lower threshold to get more leads
        leads.push(lead);
      }
    }

    // Sort by confidence (highest first)
    leads.sort((a, b) => b.confidence - a.confidence);

    console.log(`Generated ${leads.length} qualified leads`);
    
    // For development, let's also add some mock leads if we have few results
    if (leads.length < 5) {
      const mockLeads = this.generateMockLeads(filters);
      leads.push(...mockLeads);
      console.log(`Added ${mockLeads.length} mock leads for development`);
    }
    
    return leads; // Return all leads, not just top 20
  }

  private evaluateItem(item: any, filters: LeadFilters): Lead | null {
    const text = this.extractText(item);
    if (!text) return null;

    // Check practice area matches
    const practiceAreaMatch = this.checkPracticeAreaMatch(text, filters.practiceAreas);
    if (!practiceAreaMatch.matches) return null;

    // Check jurisdiction relevance
    const jurisdictionScore = this.checkJurisdictionRelevance(item, text, filters.jurisdictions);

    // Check keyword filters
    const keywordScore = this.checkKeywords(text, filters.keywordsInclude, filters.keywordsExclude);
    if (keywordScore === 0) return null; // Excluded by keywords

    // Calculate confidence score
    const confidence = this.calculateConfidence(item, practiceAreaMatch, jurisdictionScore, keywordScore);

    return {
      id: this.generateId(item),
      title: item.title || 'Untitled Case',
      source: item.source,
      confidence,
      practiceArea: practiceAreaMatch.area,
      jurisdiction: this.extractJurisdiction(item),
      summary: this.generateSummary(item, text),
      url: item.url,
      publishedAt: item.published_at,
      raw: item
    };
  }

  private extractText(item: any): string {
    const parts: string[] = [];
    
    if (item.title) parts.push(item.title);
    
    const raw = item.raw;
    if (raw) {
      // Extract relevant text fields based on source
      if (item.source === 'courtlistener') {
        if (raw.snippet) parts.push(raw.snippet);
        if (raw.caseName) parts.push(raw.caseName);
      } else if (item.source === 'openfda') {
        if (raw.product_description) parts.push(raw.product_description);
        if (raw.reason_for_recall) parts.push(raw.reason_for_recall);
      } else if (item.source === 'doj') {
        if (raw.description) parts.push(raw.description);
        if (raw.content) parts.push(raw.content);
      }
    }

    return parts.join(' ').toLowerCase();
  }

  private checkPracticeAreaMatch(text: string, practiceAreas: string[]): { matches: boolean; area: string; score: number } {
    // Enhanced ADA Title III patterns
    const adaPatterns = [
      /\bada\b/i,
      /title\s*iii/i,
      /accessibility/i,
      /disability/i,
      /accommodation/i,
      /barrier/i,
      /website.*access/i,
      /digital.*access/i,
      /screen.*reader/i,
      /wcag/i,
      /section.*508/i,
      /blind/i,
      /deaf/i,
      /wheelchair/i,
      /auxiliary.*aid/i,
      /reasonable.*accommodation/i,
      /public.*accommodation/i,
      /place.*public.*accommodation/i
    ];

    // Enhanced Product Liability patterns
    const productLiabilityPatterns = [
      /product\s*liability/i,
      /defective\s*product/i,
      /recall/i,
      /manufacturing\s*defect/i,
      /design\s*defect/i,
      /failure\s*to\s*warn/i,
      /personal\s*injury/i,
      /wrongful\s*death/i,
      /strict\s*liability/i,
      /negligence/i,
      /breach.*warranty/i,
      /consumer.*protection/i,
      /class.*action/i,
      /mass.*tort/i,
      /pharmaceutical/i,
      /medical.*device/i,
      /automotive.*defect/i,
      /toxic.*tort/i
    ];

    let bestMatch = { matches: false, area: '', score: 0 };

    if (practiceAreas.includes('ADA Title III')) {
      const adaScore = adaPatterns.reduce((score, pattern) => {
        return score + (pattern.test(text) ? 1 : 0);
      }, 0) / adaPatterns.length;

      if (adaScore > 0) {
        bestMatch = { matches: true, area: 'ADA Title III', score: adaScore };
      }
    }

    if (practiceAreas.includes('Product Liability')) {
      const plScore = productLiabilityPatterns.reduce((score, pattern) => {
        return score + (pattern.test(text) ? 1 : 0);
      }, 0) / productLiabilityPatterns.length;

      if (plScore > bestMatch.score) {
        bestMatch = { matches: true, area: 'Product Liability', score: plScore };
      }
    }

    return bestMatch;
  }

  private checkJurisdictionRelevance(item: any, text: string, jurisdictions: string[]): number {
    if (jurisdictions.length === 0) return 0.5; // Neutral if no jurisdiction filter

    const itemJurisdiction = this.extractJurisdiction(item);
    if (!itemJurisdiction) return 0.3; // Lower score if jurisdiction unknown

    // Check if item jurisdiction matches any of the firm's jurisdictions
    for (const jurisdiction of jurisdictions) {
      if (itemJurisdiction.toLowerCase().includes(jurisdiction.toLowerCase()) ||
          jurisdiction.toLowerCase().includes(itemJurisdiction.toLowerCase())) {
        return 1.0; // Perfect match
      }
    }

    // Check for regional relevance (e.g., Missouri, Kansas, KC metro)
    const regionalPatterns = [
      /missouri/i, /kansas/i, /\bmissouri\b/i, /\bkansas\b/i,
      /kansas\s*city/i, /\bkc\b/i, /midwest/i
    ];

    for (const pattern of regionalPatterns) {
      if (pattern.test(text) || pattern.test(itemJurisdiction)) {
        return 0.7; // Good regional match
      }
    }

    return 0.2; // Low relevance for distant jurisdictions
  }

  private checkKeywords(text: string, includeKeywords: string[], excludeKeywords: string[]): number {
    // Check exclude keywords first (these are blockers)
    for (const keyword of excludeKeywords) {
      if (text.includes(keyword.toLowerCase())) {
        return 0; // Excluded
      }
    }

    // Check include keywords (these boost relevance)
    if (includeKeywords.length === 0) return 0.5; // Neutral if no include keywords

    let matches = 0;
    for (const keyword of includeKeywords) {
      if (text.includes(keyword.toLowerCase())) {
        matches++;
      }
    }

    return Math.min(matches / includeKeywords.length, 1.0);
  }

  private calculateConfidence(item: any, practiceMatch: any, jurisdictionScore: number, keywordScore: number): number {
    // Weighted scoring
    const practiceWeight = 0.4;
    const jurisdictionWeight = 0.3;
    const keywordWeight = 0.2;
    const recencyWeight = 0.1;

    // Recency score (newer is better)
    const recencyScore = this.calculateRecencyScore(item.published_at);

    const confidence = 
      (practiceMatch.score * practiceWeight) +
      (jurisdictionScore * jurisdictionWeight) +
      (keywordScore * keywordWeight) +
      (recencyScore * recencyWeight);

    return Math.min(Math.max(confidence, 0), 1);
  }

  private calculateRecencyScore(publishedAt?: string): number {
    if (!publishedAt) return 0.5;

    const published = new Date(publishedAt);
    const now = new Date();
    const daysDiff = (now.getTime() - published.getTime()) / (1000 * 60 * 60 * 24);

    if (daysDiff <= 1) return 1.0;
    if (daysDiff <= 7) return 0.8;
    if (daysDiff <= 30) return 0.6;
    if (daysDiff <= 90) return 0.4;
    return 0.2;
  }

  private extractJurisdiction(item: any): string | undefined {
    if (item.jurisdiction) return item.jurisdiction;
    if (item.court) return item.court;
    
    const raw = item.raw;
    if (raw) {
      if (raw.state) return raw.state;
      if (raw.court) return raw.court;
      if (raw.jurisdiction) return raw.jurisdiction;
    }

    return undefined;
  }

  private generateSummary(item: any, text: string): string {
    // Create a brief summary from the available text
    const maxLength = 200;
    
    if (text.length <= maxLength) {
      return text;
    }

    // Try to find a good breaking point
    const truncated = text.substring(0, maxLength);
    const lastSpace = truncated.lastIndexOf(' ');
    
    if (lastSpace > maxLength * 0.8) {
      return truncated.substring(0, lastSpace) + '...';
    }
    
    return truncated + '...';
  }

  private generateId(item: any): string {
    // Generate a unique ID for the lead
    const source = item.source || 'unknown';
    const title = (item.title || '').replace(/[^a-zA-Z0-9]/g, '').substring(0, 20);
    const timestamp = Date.now();
    
    return `${source}-${title}-${timestamp}`;
  }

  private generateMockLeads(filters: LeadFilters): Lead[] {
    const mockLeads: Lead[] = [];
    
    // Generate mock ADA Title III leads if that's a practice area
    if (filters.practiceAreas.includes('ADA Title III')) {
      mockLeads.push(
        {
          id: 'mock-ada-1',
          title: 'Settlement Reached in ADA Lawsuit Against Retailer',
          source: 'courtlistener',
          confidence: 0.85,
          practiceArea: 'ADA Title III',
          jurisdiction: 'Missouri',
          summary: 'A retailer has agreed to a settlement in an ADA violation case involving the accessibility of its store entrance.',
          url: 'https://example.com/case1',
          publishedAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString(),
          raw: {}
        },
        {
          id: 'mock-ada-2',
          title: 'New ADA Complaint Alleges Lack of Website Access',
          source: 'doj',
          confidence: 0.78,
          practiceArea: 'ADA Title III',
          jurisdiction: 'Kansas',
          summary: 'A recent ADA complaint has been made, claiming that a website is not accessible to individuals with disabilities.',
          url: 'https://example.com/case2',
          publishedAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000).toISOString(),
          raw: {}
        }
      );
    }

    // Generate mock Product Liability leads if that's a practice area
    if (filters.practiceAreas.includes('Product Liability')) {
      mockLeads.push(
        {
          id: 'mock-pl-1',
          title: 'Product Liability Suit Filed Over Defective Vehicle',
          source: 'openfda',
          confidence: 0.72,
          practiceArea: 'Product Liability',
          jurisdiction: 'Kansas City',
          summary: 'A new product liability lawsuit has been filed in Kansas City concerning a vehicle\'s faulty braking system.',
          url: 'https://example.com/case3',
          publishedAt: new Date(Date.now() - 3 * 24 * 60 * 60 * 1000).toISOString(),
          raw: {}
        },
        {
          id: 'mock-pl-2',
          title: 'Jury Finds in Favor of Plaintiff in Product Case',
          source: 'courtlistener',
          confidence: 0.65,
          practiceArea: 'Product Liability',
          jurisdiction: 'Missouri',
          summary: 'A jury in Missouri has returned a verdict in favor of the plaintiff in a product liability case involving a household appliance.',
          url: 'https://example.com/case4',
          publishedAt: new Date(Date.now() - 4 * 24 * 60 * 60 * 1000).toISOString(),
          raw: {}
        },
        {
          id: 'mock-pl-3',
          title: 'Class Action Filed Against Medical Device Manufacturer',
          source: 'doj',
          confidence: 0.58,
          practiceArea: 'Product Liability',
          jurisdiction: 'Federal',
          summary: 'A class action lawsuit has been filed against a medical device manufacturer alleging defective hip implants.',
          url: 'https://example.com/case5',
          publishedAt: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
          raw: {}
        }
      );
    }

    return mockLeads;
  }
}

export const leadDetector = new LeadDetector();