// middleware.ts (project root)
import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server';
import { NextResponse } from 'next/server';

const isAppRoute = createRouteMatcher(['/app(.*)']);
const isOnboardingRoute = createRouteMatcher(['/onboarding']);
const isAuthRoute = createRouteMatcher(['/auth']);

export default clerkMiddleware(async (auth, req) => {
  const { userId, orgId, redirectToSignIn } = await auth();

  // Handle /app routes - require auth and org
  if (isAppRoute(req)) {
    if (!userId) return redirectToSignIn();

    if (!orgId) {
      const url = new URL(req.url);
      url.pathname = '/onboarding';
      return NextResponse.redirect(url);
    }
  }

  // Handle onboarding route - require auth but allow no org
  if (isOnboardingRoute(req)) {
    if (!userId) return redirectToSignIn();
    // Allow access to onboarding even without orgId
  }

  // Handle auth route - redirect signed-in users
  if (isAuthRoute(req)) {
    if (userId) {
      const url = new URL(req.url);
      url.pathname = '/onboarding';
      return NextResponse.redirect(url);
    }
    // Allow access to auth page for non-signed-in users
  }

  // All other routes (including /) - no restrictions, just let middleware run
  // This ensures auth() calls work anywhere in the app
});

export const config = {
  matcher: ['/((?!.+\\.[\\w]+$|_next).*)', '/', '/(api|trpc)(.*)'],
};
