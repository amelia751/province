import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'
import { auth } from '@clerk/nextjs/server'

export function createServerSupabaseClient() {
  const cookieStore = cookies()

  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    {
      cookies: {
        getAll() {
          return cookieStore.getAll()
        },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options)
            )
          } catch {
            // The `setAll` method was called from a Server Component.
            // This can be ignored if you have middleware refreshing
            // user sessions.
          }
        },
      },
    }
  )
}

/**
 * Creates a Supabase client with RLS context set for the current organization
 * This ensures all queries are automatically filtered by the user's organization
 */
export async function createTenantSupabaseClient() {
  const supabase = createServerSupabaseClient()
  const { orgId } = await auth()
  
  if (orgId) {
    // Set the RLS context to the current organization
    // This makes all subsequent queries automatically filtered by org_id
    await supabase.rpc('set_config', {
      setting_name: 'app.org_id',
      setting_value: orgId,
      is_local: true
    })
  }
  
  return supabase
}

/**
 * Helper function to ensure RLS context is set for raw SQL queries
 */
export async function setRLSContext(supabase: any, orgId: string) {
  await supabase.rpc('set_config', {
    setting_name: 'app.org_id', 
    setting_value: orgId,
    is_local: true
  })
}

/**
 * Type-safe organization ID validation
 */
export function isValidClerkOrgId(orgId: string): boolean {
  return orgId.startsWith('org_') && orgId.length > 10
}