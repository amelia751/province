// middleware.ts (project root)
import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server';

const isAppRoute = createRouteMatcher(['/app(.*)']);

export default clerkMiddleware(async (auth, req) => {
  const { userId, redirectToSignIn } = await auth();

  // Handle /app routes - require auth only, allow personal accounts
  if (isAppRoute(req)) {
    if (!userId) return redirectToSignIn();
    // No orgId check - allow personal accounts without organizations
  }

  // All other routes (including /) - no restrictions
});

export const config = {
  matcher: ['/((?!.+\\.[\\w]+$|_next).*)', '/', '/(api|trpc)(.*)'],
};
