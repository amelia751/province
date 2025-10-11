import { auth } from '@clerk/nextjs/server';
import { redirect } from 'next/navigation';
import { getUserOrganization, getOrganizationName, getUserPersonalAccount, createPersonalAccount, getPersonalAccountName, createOrganization } from '@/lib/organization';
import { createServerSupabaseClient } from '@/lib/supabase-server';
import StartScreenClient from '@/app/app/start-screen-client';
import Sidebar from '@/components/ui/sidebar';

export default async function AppPage() {
  const { userId, orgId } = await auth();
  
  console.log('🔍 Auth Debug:', { userId: !!userId, orgId: !!orgId, orgIdValue: orgId });
  
  if (!userId) {
    redirect('/');
  }

  // Add temporary debug info
  if (orgId) {
    console.log('⚠️ User has orgId, this means Clerk is forcing organization context');
  } else {
    console.log('✅ No orgId found, proceeding with personal account');
  }

  let accountName: string | null = null;
  let isPersonalAccount = false;

  if (orgId) {
    // User has an organization context - check if organization exists in our database
    const organization = await getUserOrganization();
    
    if (!organization) {
      // Organization exists in Clerk but not in database - create it
      const { success, error: createError } = await createOrganization();
      
      if (!success) {
        console.error('Failed to create organization:', createError);
        return (
          <div className="min-h-screen flex items-center justify-center bg-gray-50">
            <div className="bg-white p-8 rounded-lg shadow-lg max-w-md">
              <h1 className="text-2xl font-bold text-red-600 mb-4">Organization Setup Error</h1>
              <p className="text-gray-700 mb-4">
                We couldn't set up your organization: {createError}
              </p>
              <p className="text-sm text-gray-600">
                Please contact support or try refreshing the page.
              </p>
            </div>
          </div>
        );
      }

      // Successfully created, redirect to refresh
      redirect('/app');
    }

    accountName = await getOrganizationName();
    isPersonalAccount = false;
  } else {
    // No organization context - use personal account
    let personalAccount = await getUserPersonalAccount();
    
    if (!personalAccount) {
      // Personal account doesn't exist in database - create it
      const { success, error: createError } = await createPersonalAccount();
      
      if (!success) {
        console.error('Failed to create personal account:', createError);
        return (
          <div className="min-h-screen flex items-center justify-center bg-gray-50">
            <div className="bg-white p-8 rounded-lg shadow-lg max-w-md">
              <h1 className="text-2xl font-bold text-red-600 mb-4">Account Setup Error</h1>
              <p className="text-gray-700 mb-4">
                We couldn't set up your personal account: {createError}
              </p>
              <p className="text-sm text-gray-600">
                Please contact support or try refreshing the page.
              </p>
            </div>
          </div>
        );
      }

      // Successfully created, redirect to refresh
      redirect('/app');
    }

    accountName = await getPersonalAccountName();
    isPersonalAccount = true;
  }

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <Sidebar organizationName={accountName} isPersonalAccount={isPersonalAccount} />
      
      {/* Main content - Start Screen */}
      <div className="flex-1 overflow-auto">
        <StartScreenClient />
      </div>
    </div>
  );
}