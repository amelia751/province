import { auth } from '@clerk/nextjs/server';
import { redirect } from 'next/navigation';
import { createOrgIfMissing } from '../actions/create-org';
import { getUserOrganization } from '@/lib/organization';
import SetActiveClient from './set-active-client';
import OnboardingClient from './onboarding-client';

export default async function OnboardingPage() {
  const { userId } = await auth();
  if (!userId) return null; // middleware/Clerk will handle auth

  // First, ensure user has a Clerk organization
  const clerkOrgResult = await createOrgIfMissing();

  if (!clerkOrgResult.ok) {
    return (
      <div style={{ padding: 24 }}>
        <h1>Onboarding</h1>
        <p style={{ color: 'crimson' }}>
          Couldn't create or fetch your organization: {clerkOrgResult.error}
        </p>
        <p>Tips:</p>
        <ul>
          <li>In Clerk Dashboard, ensure <b>Organizations</b> is enabled for your app.</li>
          <li>Check your env keys and try again.</li>
        </ul>
      </div>
    );
  }

  // Check if organization exists in our database
  const organization = await getUserOrganization();

  // If organization exists in our database, proceed to app
  if (organization) {
    return <SetActiveClient orgId={clerkOrgResult.orgId} created={false} />;
  }

  // If no organization in our database, show onboarding form
  return <OnboardingClient orgId={clerkOrgResult.orgId} />;
}
