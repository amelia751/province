import { notFound } from 'next/navigation';
import { auth } from '@clerk/nextjs/server';
import { redirect } from 'next/navigation';
import { getUserOrganization, getOrganizationName } from '@/lib/organization';
import { leadDetector } from '@/lib/leads/lead-detector';
import DashboardLayout from '@/components/dashboard/dashboard-layout';
import LeadDetailView from '@/components/leads/lead-detail-view';

interface LeadDetailPageProps {
  params: {
    id: string;
  };
}

export default async function LeadDetailPage({ params }: LeadDetailPageProps) {
  const { userId } = await auth();
  
  if (!userId) {
    redirect('/');
  }

  const organization = await getUserOrganization();
  
  if (!organization) {
    redirect('/onboarding');
  }

  const organizationName = await getOrganizationName();

  // Fetch all leads to find the specific one
  const leads = await leadDetector.detectLeads({
    practiceAreas: organization.practice_areas || [],
    jurisdictions: organization.jurisdictions || [],
    keywordsInclude: organization.keywords_include || [],
    keywordsExclude: organization.keywords_exclude || []
  });

  const lead = leads.find(l => l.id === params.id);

  if (!lead) {
    notFound();
  }

  return (
    <DashboardLayout organizationName={organizationName}>
      <LeadDetailView lead={lead} />
    </DashboardLayout>
  );
}