import { auth } from '@clerk/nextjs/server';
import { redirect } from 'next/navigation';
import { getUserOrganization, getOrganizationName } from '@/lib/organization';
import { leadDetector } from '@/lib/leads/lead-detector';
import DashboardLayout from '@/components/dashboard/dashboard-layout';
import LeadsList from '@/components/dashboard/leads-list';
import StatsOverview from '@/components/dashboard/stats-overview';

export default async function AppPage() {
  const { userId } = await auth();
  
  if (!userId) {
    redirect('/');
  }

  const organization = await getUserOrganization();
  
  if (!organization) {
    redirect('/onboarding');
  }

  const organizationName = await getOrganizationName();

  // Fetch recent leads for this organization
  const leads = await leadDetector.detectLeads({
    practiceAreas: organization.practice_areas || [],
    jurisdictions: organization.jurisdictions || [],
    keywordsInclude: organization.keywords_include || [],
    keywordsExclude: organization.keywords_exclude || []
  });

  return (
    <DashboardLayout organizationName={organizationName}>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-semibold text-black">Leads Dashboard</h1>
        </div>

        {/* Filters - will be handled by LeadsList component */}

        {/* Bulk Actions */}
        <div className="flex items-center space-x-4 mb-6">
          <span className="text-sm font-medium text-black">Bulk actions</span>
          <button className="text-sm text-gray-600 hover:text-black">mark useful</button>
          <button className="text-sm text-gray-600 hover:text-black">snooze</button>
          <button className="text-sm text-gray-600 hover:text-black">assign</button>
        </div>

        {/* Leads List */}
        <LeadsList leads={leads} />
      </div>
    </DashboardLayout>
  );
}