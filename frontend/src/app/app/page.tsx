import { auth } from '@clerk/nextjs/server';
import { redirect } from 'next/navigation';
import { getUserOrganization, getOrganizationName } from '@/lib/organization';
import { createServerSupabaseClient } from '@/lib/supabase-server';
import InterfaceLayout from '@/components/ui/interface-layout';

export default async function AppPage() {
  const { userId, orgId } = await auth();
  
  if (!userId) {
    redirect('/');
  }

  // If no organization context, user needs to create one via Clerk
  if (!orgId) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="bg-white p-8 rounded-lg shadow-lg max-w-md text-center">
          <div className="mx-auto w-16 h-16 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center mb-4">
            <div className="w-8 h-8 bg-white rounded-md"></div>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-4">Welcome to Province</h1>
          <p className="text-gray-600 mb-6">
            You need to create or join an organization to get started. Please use the organization menu in the top left.
          </p>
          <p className="text-sm text-gray-500">
            Click on your profile picture, then select "Create Organization"
          </p>
        </div>
      </div>
    );
  }

  // Check if organization exists in our database
  const organization = await getUserOrganization();
  
  if (!organization) {
    // Organization exists in Clerk but not in database - sync it
    const supabase = createServerSupabaseClient();
    
    const { error: dbError } = await supabase.rpc('create_organization_bypass_rls', {
      org_id: orgId,
      org_region: '',
      org_website: null,
      org_timezone: 'America/Chicago',
      org_practice_areas: [],
      org_jurisdictions: [],
      org_keywords_include: [],
      org_keywords_exclude: [],
      org_digest_cadence: 'weekly',
      org_digest_hour_local: 9,
    });

    if (dbError) {
      console.error('Failed to sync organization to database:', dbError);
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
          <div className="bg-white p-8 rounded-lg shadow-lg max-w-md">
            <h1 className="text-2xl font-bold text-red-600 mb-4">Database Sync Error</h1>
            <p className="text-gray-700 mb-4">
              Your organization exists in Clerk but we couldn't sync it to our database: {dbError.message}
            </p>
            <p className="text-sm text-gray-600">
              Please contact support or try refreshing the page.
            </p>
          </div>
        </div>
      );
    }

    // Successfully synced, redirect to refresh
    redirect('/app');
  }

  const organizationName = await getOrganizationName();

  return (
    <InterfaceLayout organizationName={organizationName} />
  );
}