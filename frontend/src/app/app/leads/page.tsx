import { auth } from '@clerk/nextjs/server';
import { redirect } from 'next/navigation';
import { getUserOrganization, getOrganizationName, getUserPersonalAccount, getPersonalAccountName } from '@/lib/organization';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default async function LeadsPage() {
  const { userId, orgId } = await auth();
  
  if (!userId) {
    redirect('/');
  }

  let accountName: string | null = null;
  let hasOrganization = false;

  if (orgId) {
    // User has organization context
    const organization = await getUserOrganization();
    if (organization) {
      accountName = await getOrganizationName();
      hasOrganization = true;
    }
  } else {
    // Personal account
    const personalAccount = await getUserPersonalAccount();
    if (personalAccount) {
      accountName = await getPersonalAccountName();
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-4">
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="text-center py-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Leads
          </h1>
          <p className="text-xl text-gray-600">
            {hasOrganization 
              ? `Manage leads for ${accountName}` 
              : `Personal leads for ${accountName}`
            }
          </p>
        </div>

        {!hasOrganization && (
          <Card className="border-blue-200 bg-blue-50">
            <CardHeader>
              <CardTitle className="text-blue-800">Personal Account</CardTitle>
              <CardDescription className="text-blue-700">
                You're using a personal account. Lead detection works best with organization settings.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-blue-700 text-sm">
                Create an organization to set up practice areas, jurisdictions, and keyword preferences for better lead detection.
              </p>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader>
            <CardTitle>Lead Detection</CardTitle>
            <CardDescription>
              {hasOrganization 
                ? "Leads are detected based on your organization's practice areas and preferences."
                : "Lead detection is available but works best with organization settings."
              }
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <p className="text-sm text-gray-600">
                Lead detection analyzes recent cases from CourtListener, OpenFDA, and DOJ to find relevant opportunities.
              </p>
              
              {hasOrganization ? (
                <div className="text-sm text-gray-600">
                  <p>✅ Organization configured</p>
                  <p>✅ Practice areas and preferences set</p>
                  <p>✅ Ready for lead detection</p>
                </div>
              ) : (
                <div className="text-sm text-gray-600">
                  <p>ℹ️ Using personal account</p>
                  <p>ℹ️ Limited lead detection available</p>
                  <p>💡 Create an organization for full features</p>
                </div>
              )}

              <div className="pt-4">
                <a 
                  href="/test/leads" 
                  className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  Test Lead Detection →
                </a>
              </div>
            </div>
          </CardContent>
        </Card>

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
