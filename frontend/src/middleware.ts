// middleware.ts (project root)
import { clerkMiddleware, createRouteMatcher } from '@clerk/nextjs/server';

const isAppRoute = createRouteMatcher(['/app(.*)']);

export default clerkMiddleware(async (auth, req) => {
  const { userId, redirectToSignIn } = await auth();

  // Handle /app routes - require auth
  if (isAppRoute(req)) {
    if (!userId) return redirectToSignIn();
    // Don't check orgId - Clerk handles org creation, we just sync to DB
  }

  // All other routes (including /) - no restrictions
});

export const config = {
  matcher: ['/((?!.+\\.[\\w]+$|_next).*)', '/', '/(api|trpc)(.*)'],
};
