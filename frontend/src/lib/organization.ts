import { createServerSupabaseClient } from './supabase-server';
import { createClient } from '@supabase/supabase-js';
import { auth, clerkClient } from '@clerk/nextjs/server';

export interface Organization {
  id: string;
  region?: string;
  website?: string;
  timezone: string;
  practice_areas: string[];
  jurisdictions: string[];
  keywords_include: string[];
  keywords_exclude: string[];
  source_courtlistener: boolean;
  source_openfda: boolean;
  source_doj: boolean;
  source_rss: boolean;
  digest_enabled: boolean;
  digest_cadence: string;
  digest_hour_local: number;
  billing: 'trial' | 'active' | 'past_due';
  trial_ends_at?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateOrganizationData {
  region?: string;
  website?: string;
  timezone?: string;
  practice_areas?: string[];
  jurisdictions?: string[];
  keywords_include?: string[];
  keywords_exclude?: string[];
  digest_cadence?: 'daily' | 'weekly';
  digest_hour_local?: number;
}



export async function getOrganizationName(): Promise<string | null> {
  try {
    const { userId, orgId } = await auth();
    
    if (!userId || !orgId) {
      return null;
    }

    const client = await clerkClient();
    const organization = await client.organizations.getOrganization({ organizationId: orgId });
    
    return organization.name;
  } catch (error) {
    console.error('Error fetching organization name from Clerk:', error);
    return null;
  }
}

export async function getUserOrganization(): Promise<Organization | null> {
  try {
    const { userId, orgId } = await auth();
    
    if (!userId || !orgId) {
      console.log('No userId or orgId found');
      return null;
    }
    
    const supabase = createServerSupabaseClient();
    
    console.log('Fetching organization with ID:', orgId);
    
    // Use RPC function to bypass RLS
    const { data, error } = await supabase.rpc('get_organization_by_id', {
      org_id: orgId
    });

    if (error) {
      console.error('Error fetching organization via RPC:', error);
      return null;
    }

    if (!data || data.length === 0) {
      console.log('No organization found for ID:', orgId);
      return null;
    }

    const organization = data[0] as Organization;
    console.log('Organization found:', organization.id);
    return organization;
  } catch (error) {
    console.error('Error in getUserOrganization:', error);
    return null;
  }
}

export async function createOrganization(orgData: CreateOrganizationData): Promise<{ success: boolean; organization?: Organization; error?: string }> {
  try {
    const { userId, orgId } = await auth();
    
    if (!userId || !orgId) {
      return { success: false, error: 'User not authenticated or no organization in Clerk' };
    }



    // Use regular supabase client with RPC function that bypasses RLS
    const supabase = createServerSupabaseClient();

    console.log('Creating organization with RPC function...');

    // Use the RPC function to create organization (bypasses RLS)
    const { data, error } = await supabase.rpc('create_organization_bypass_rls', {
      org_id: orgId,
      org_region: orgData.region || '',
      org_website: orgData.website || null,
      org_timezone: orgData.timezone || 'America/Chicago',
      org_practice_areas: orgData.practice_areas || [],
      org_jurisdictions: orgData.jurisdictions || [],
      org_keywords_include: orgData.keywords_include || [],
      org_keywords_exclude: orgData.keywords_exclude || [],
      org_digest_cadence: orgData.digest_cadence || 'weekly',
      org_digest_hour_local: orgData.digest_hour_local || 9,
    });

    if (error) {
      console.error('Error creating organization via RPC:', error);
      return { success: false, error: error.message };
    }

    if (!data || data.length === 0) {
      console.error('No data returned from RPC function');
      return { success: false, error: 'No organization data returned' };
    }

    const organization = data[0] as Organization;
    console.log('Organization created successfully via RPC:', organization);
    return { success: true, organization };
  } catch (error) {
    console.error('Error in createOrganization:', error);
    return { success: false, error: 'Unknown error occurred' };
  }
}

export async function updateOrganization(orgData: Partial<CreateOrganizationData>): Promise<{ success: boolean; organization?: Organization; error?: string }> {
  try {
    const { userId, orgId } = await auth();
    
    if (!userId || !orgId) {
      return { success: false, error: 'User not authenticated or no organization in Clerk' };
    }



    const supabase = createServerSupabaseClient();
    
    // Set RLS context for the current organization
    await supabase.rpc('set_config', {
      setting_name: 'app.org_id',
      setting_value: orgId,
      is_local: true
    });
    
    // Prepare update data (only include fields that are provided)
    const updateData: any = {};
    if (orgData.region !== undefined) updateData.region = orgData.region;
    if (orgData.website !== undefined) updateData.website = orgData.website;
    if (orgData.timezone !== undefined) updateData.timezone = orgData.timezone;
    if (orgData.practice_areas !== undefined) updateData.practice_areas = orgData.practice_areas;
    if (orgData.jurisdictions !== undefined) updateData.jurisdictions = orgData.jurisdictions;
    if (orgData.keywords_include !== undefined) updateData.keywords_include = orgData.keywords_include;
    if (orgData.keywords_exclude !== undefined) updateData.keywords_exclude = orgData.keywords_exclude;
    if (orgData.digest_cadence !== undefined) updateData.digest_cadence = orgData.digest_cadence;
    if (orgData.digest_hour_local !== undefined) updateData.digest_hour_local = orgData.digest_hour_local;

    const { data, error } = await supabase
      .from('organization')
      .update(updateData)
      .eq('id', orgId)
      .select()
      .single();

    if (error) {
      console.error('Error updating organization:', error);
      return { success: false, error: error.message };
    }

    return { success: true, organization: data as Organization };
  } catch (error) {
    console.error('Error in updateOrganization:', error);
    return { success: false, error: 'Unknown error occurred' };
  }
}