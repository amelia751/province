// app/onboarding/set-active-client.tsx
'use client';

import { useEffect, useState } from 'react';
import { useOrganizationList } from '@clerk/nextjs';
import { useRouter } from 'next/navigation';

export default function SetActiveClient({
  orgId,
  created,
}: {
  orgId: string;
  created: boolean;
}) {
  const { setActive, isLoaded } = useOrganizationList();
  const [err, setErr] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    if (!isLoaded) return;

    (async () => {
      try {
        // This updates the active org and refreshes the session token
        await setActive?.({ organization: orgId });

        // Small safety delay is usually not necessary, but avoids race conditions
        // await new Promise((r) => setTimeout(r, 150));

        router.replace('/app');
      } catch (e: any) {
        setErr(e?.message ?? 'Failed to set active organization');
      }
    })();
  }, [isLoaded, orgId, setActive, router]);

  if (err) {
    return (
      <div style={{ padding: 24 }}>
        <h1>Onboarding</h1>
        <p style={{ color: 'crimson' }}>Error setting active org: {err}</p>
        <p>If this persists, try the Organization Switcher in the header.</p>
      </div>
    );
  }

  return (
    <div style={{ padding: 24 }}>
      {created ? 'Creating your organization…' : 'Finalizing your setup…'}
    </div>
  );
}
