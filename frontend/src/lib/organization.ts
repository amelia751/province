import { createServerSupabaseClient } from './supabase-server';
import { createClient } from '@supabase/supabase-js';
import { auth, clerkClient } from '@clerk/nextjs/server';

export interface Organization {
  org_id: string;
  created_at: string;
  updated_at: string;
}

export interface PersonalAccount {
  user_id: string;
  created_at: string;
  updated_at: string;
}

export interface OrganizationMember {
  org_id: string;
  user_id: string;
  role: 'admin' | 'member';
  created_at: string;
}



// Organization Functions

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
      input_org_id: orgId
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
    console.log('Organization found:', organization.org_id);
    return organization;
  } catch (error) {
    console.error('Error in getUserOrganization:', error);
    return null;
  }
}

export async function createOrganization(): Promise<{ success: boolean; organization?: Organization; error?: string }> {
  try {
    const { userId, orgId } = await auth();
    
    if (!userId || !orgId) {
      return { success: false, error: 'User not authenticated or no organization in Clerk' };
    }

    const supabase = createServerSupabaseClient();

    console.log('Creating organization with RPC function...');

    // Use the RPC function to create organization (bypasses RLS)
    const { data, error } = await supabase.rpc('create_organization_bypass_rls', {
      input_org_id: orgId
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

// Personal Account Functions

export async function getUserPersonalAccount(): Promise<PersonalAccount | null> {
  try {
    const { userId } = await auth();
    
    if (!userId) {
      console.log('No userId found');
      return null;
    }
    
    const supabase = createServerSupabaseClient();
    
    console.log('Fetching personal account with ID:', userId);
    
    // Use RPC function to bypass RLS
    const { data, error } = await supabase.rpc('get_personal_account_by_id', {
      input_user_id: userId
    });

    if (error) {
      console.error('Error fetching personal account via RPC:', error);
      return null;
    }

    if (!data || data.length === 0) {
      console.log('No personal account found for ID:', userId);
      return null;
    }

    const account = data[0] as PersonalAccount;
    console.log('Personal account found:', account.user_id);
    return account;
  } catch (error) {
    console.error('Error in getUserPersonalAccount:', error);
    return null;
  }
}

export async function createPersonalAccount(): Promise<{ success: boolean; account?: PersonalAccount; error?: string }> {
  try {
    const { userId } = await auth();
    
    if (!userId) {
      return { success: false, error: 'User not authenticated' };
    }

    const supabase = createServerSupabaseClient();

    console.log('Creating personal account with RPC function...');

    // Use the RPC function to create personal account (bypasses RLS)
    const { data, error } = await supabase.rpc('create_personal_account_bypass_rls', {
      input_user_id: userId
    });

    if (error) {
      console.error('Error creating personal account via RPC:', error);
      return { success: false, error: error.message };
    }

    if (!data || data.length === 0) {
      console.error('No data returned from RPC function');
      return { success: false, error: 'No personal account data returned' };
    }

    const account = data[0] as PersonalAccount;
    console.log('Personal account created successfully via RPC:', account);
    return { success: true, account };
  } catch (error) {
    console.error('Error in createPersonalAccount:', error);
    return { success: false, error: 'Unknown error occurred' };
  }
}

export async function getPersonalAccountName(): Promise<string | null> {
  try {
    const { userId } = await auth();
    
    if (!userId) {
      return null;
    }

    const client = await clerkClient();
    const user = await client.users.getUser(userId);
    
    if (user.firstName && user.lastName) {
      return `${user.firstName} ${user.lastName}`;
    } else if (user.firstName) {
      return user.firstName;
    } else if (user.emailAddresses[0]?.emailAddress) {
      return user.emailAddresses[0].emailAddress;
    }
    
    return 'Personal Account';
  } catch (error) {
    console.error('Error fetching personal account name from Clerk:', error);
    return 'Personal Account';
  }
}