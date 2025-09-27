import { createServerSupabaseClient } from '@/lib/supabase-server';
import { auth } from '@clerk/nextjs/server';

export interface IngestedItem {
  source: string;
  title: string;
  url?: string;
  court?: string;
  jurisdiction?: string;
  published_at?: string | null;
  raw: any;
}

export interface ProcessedDocument {
  id: string;
  source: string;
  source_ref: string;
  title: string;
  text: string;
  token_count: number;
  metadata: Record<string, any>;
}

export class TextProcessor {
  private supabase = createServerSupabaseClient();

  async processItems(items: IngestedItem[]): Promise<{ success: boolean; processed: number; errors: string[] }> {
    const { userId, orgId } = await auth();
    
    if (!userId || !orgId) {
      throw new Error('User not authenticated or no organization');
    }

    let processed = 0;
    const errors: string[] = [];

    for (const item of items) {
      try {
        await this.processItem(item, orgId);
        processed++;
      } catch (error) {
        const errorMsg = error instanceof Error ? error.message : 'Unknown error';
        errors.push(`Failed to process ${item.title}: ${errorMsg}`);
        console.error('Error processing item:', item.title, error);
      }
    }

    return { success: errors.length === 0, processed, errors };
  }

  private async processItem(item: IngestedItem, orgId: string): Promise<void> {
    // Extract clean text from the item
    const cleanText = this.extractText(item);
    
    if (!cleanText || cleanText.trim().length === 0) {
      throw new Error('No text content found');
    }

    // Calculate token count (rough estimate: 1 token ≈ 4 characters)
    const tokenCount = Math.ceil(cleanText.length / 4);

    // Create a hash for deduplication
    const hash = await this.createHash(cleanText);

    // Create source reference
    const sourceRef = this.createSourceRef(item);

    // Check if document already exists
    const existingDoc = await this.findExistingDocument(orgId, hash);
    if (existingDoc) {
      console.log(`Document already exists: ${item.title}`);
      return;
    }

    // Store document
    const documentId = await this.storeDocument(orgId, item, sourceRef, hash);

    // Store normalized text
    await this.storeDocumentText(orgId, documentId, cleanText, tokenCount);

    console.log(`Processed document: ${item.title} (${tokenCount} tokens)`);
  }

  private extractText(item: IngestedItem): string {
    const parts: string[] = [];

    // Add title
    if (item.title) {
      parts.push(item.title);
    }

    // Extract text based on source type
    switch (item.source) {
      case 'courtlistener':
        parts.push(...this.extractCourtListenerText(item));
        break;
      case 'openfda':
        parts.push(...this.extractOpenFDAText(item));
        break;
      case 'doj':
        parts.push(...this.extractDOJText(item));
        break;
      default:
        // Generic extraction
        parts.push(...this.extractGenericText(item));
    }

    return parts.filter(Boolean).join('\n\n');
  }

  private extractCourtListenerText(item: IngestedItem): string[] {
    const parts: string[] = [];
    const raw = item.raw;

    if (raw.snippet) parts.push(raw.snippet);
    if (raw.caseName) parts.push(`Case: ${raw.caseName}`);
    if (raw.court) parts.push(`Court: ${raw.court}`);
    if (raw.dateFiled) parts.push(`Filed: ${raw.dateFiled}`);
    if (raw.docketNumber) parts.push(`Docket: ${raw.docketNumber}`);
    if (raw.text) parts.push(raw.text);

    return parts;
  }

  private extractOpenFDAText(item: IngestedItem): string[] {
    const parts: string[] = [];
    const raw = item.raw;

    if (raw.product_description) parts.push(`Product: ${raw.product_description}`);
    if (raw.reason_for_recall) parts.push(`Reason: ${raw.reason_for_recall}`);
    if (raw.recalling_firm) parts.push(`Firm: ${raw.recalling_firm}`);
    if (raw.distribution_pattern) parts.push(`Distribution: ${raw.distribution_pattern}`);
    if (raw.product_quantity) parts.push(`Quantity: ${raw.product_quantity}`);
    if (raw.recall_initiation_date) parts.push(`Recall Date: ${raw.recall_initiation_date}`);

    return parts;
  }

  private extractDOJText(item: IngestedItem): string[] {
    const parts: string[] = [];
    const raw = item.raw;

    if (raw.description) parts.push(raw.description);
    if (raw.content) parts.push(raw.content);
    if (raw.summary) parts.push(raw.summary);
    if (raw.body) parts.push(raw.body);

    return parts;
  }

  private extractGenericText(item: IngestedItem): string[] {
    const parts: string[] = [];
    const raw = item.raw;

    // Try common text fields
    const textFields = ['text', 'content', 'description', 'summary', 'body', 'snippet'];
    
    for (const field of textFields) {
      if (raw[field] && typeof raw[field] === 'string') {
        parts.push(raw[field]);
      }
    }

    return parts;
  }

  private async createHash(text: string): Promise<string> {
    const encoder = new TextEncoder();
    const data = encoder.encode(text);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  }

  private createSourceRef(item: IngestedItem): string {
    // Create a unique reference for this source item
    const timestamp = new Date().toISOString();
    const titleSlug = item.title.toLowerCase().replace(/[^a-z0-9]/g, '-').slice(0, 50);
    return `${item.source}-${titleSlug}-${timestamp}`;
  }

  private async findExistingDocument(orgId: string, hash: string): Promise<any> {
    const { data } = await this.supabase
      .from('document')
      .select('id')
      .eq('org_id', orgId)
      .eq('hash', hash)
      .single();

    return data;
  }

  private async storeDocument(
    orgId: string, 
    item: IngestedItem, 
    sourceRef: string, 
    hash: string
  ): Promise<string> {
    // Set RLS context
    await this.supabase.rpc('set_config', {
      setting_name: 'app.org_id',
      setting_value: orgId,
      is_local: true
    });

    const { data, error } = await this.supabase
      .from('document')
      .insert({
        org_id: orgId,
        source: item.source,
        source_ref: sourceRef,
        object_key: item.url || sourceRef, // Use URL as object key if available
        mime_type: 'application/json', // API responses are JSON
        hash: hash,
        ingested_at: new Date().toISOString(),
        processed_at: new Date().toISOString()
      })
      .select('id')
      .single();

    if (error) {
      throw new Error(`Failed to store document: ${error.message}`);
    }

    return data.id;
  }

  private async storeDocumentText(
    orgId: string,
    documentId: string,
    text: string,
    tokenCount: number
  ): Promise<void> {
    // Set RLS context
    await this.supabase.rpc('set_config', {
      setting_name: 'app.org_id',
      setting_value: orgId,
      is_local: true
    });

    const { error } = await this.supabase
      .from('doc_text')
      .insert({
        org_id: orgId,
        document_id: documentId,
        version: 1,
        text: text,
        token_count: tokenCount
      });

    if (error) {
      throw new Error(`Failed to store document text: ${error.message}`);
    }
  }
}

export const textProcessor = new TextProcessor();