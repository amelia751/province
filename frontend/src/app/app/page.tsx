import { auth } from '@clerk/nextjs/server';
import { redirect } from 'next/navigation';
import { getUserOrganization, getOrganizationName } from '@/lib/organization';
import InterfaceLayout from '@/components/ui/interface-layout';

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

  return (
    <InterfaceLayout organizationName={organizationName} />
  );
}