// lib/supabase-client.ts
'use client';

import { createClient } from '@supabase/supabase-js';
import { useSession } from '@clerk/nextjs';

export function useClerkSupabase() {
  const { session } = useSession();

  const client = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_KEY!,
    {
      async accessToken() {
        return session?.getToken() ?? null;
      },
    }
  );

  return client;
}
