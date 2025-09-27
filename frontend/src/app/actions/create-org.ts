// app/actions/create-org.ts
'use server';

import { clerkClient, currentUser } from '@clerk/nextjs/server';

type Result =
  | { ok: true; orgId: string; created: boolean }
  | { ok: false; error: string };

export async function createOrgIfMissing(): Promise<Result> {
  try {
    const user = await currentUser();
    if (!user) return { ok: false, error: 'Not signed in' };

    const client = await clerkClient(); // v6: callable client

    // 1) Already in an org?
    const memberships = await client.users.getOrganizationMembershipList({
      userId: user.id,
      limit: 1,
    });

    if (memberships.data.length > 0) {
      const orgId = memberships.data[0].organization.id;
      return { ok: true, orgId, created: false };
    }

    // 2) Create "<FirstName>'s Organization"
    const first = user.firstName || 'New';
    const org = await client.organizations.createOrganization({
      name: `${first}'s Organization`,
      createdBy: user.id, // creator becomes admin
    });

    return { ok: true, orgId: org.id, created: true };
  } catch (e: any) {
    // You’ll see this on the onboarding page now
    return { ok: false, error: e?.message ?? 'Unknown error' };
  }
}
