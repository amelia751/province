# Setup Guide

## Environment Variables

Create a `.env.local` file in the `frontend` directory with the following variables:

```bash
# Clerk Keys
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=your_publishable_key
CLERK_SECRET_KEY=your_secret_key

# Clerk Redirect Paths
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/sign-in
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/sign-up
NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/app
NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/app

# IMPORTANT: Organization Redirect Paths
# This prevents Clerk from redirecting to /onboarding after creating an organization
NEXT_PUBLIC_CLERK_AFTER_CREATE_ORGANIZATION_URL=/app
NEXT_PUBLIC_CLERK_AFTER_LEAVE_ORGANIZATION_URL=/app

# Database
DATABASE_URL=your_database_url
```

## Critical Configuration

### Fix Clerk Organization Redirect

Add these two lines to your `.env.local` file to prevent the redirect to `/onboarding`:

```bash
NEXT_PUBLIC_CLERK_AFTER_CREATE_ORGANIZATION_URL=/app
NEXT_PUBLIC_CLERK_AFTER_LEAVE_ORGANIZATION_URL=/app
```

After adding these variables:
1. Stop your development server
2. Restart it: `npm run dev`
3. Create a new organization - it should now redirect to `/app` instead of `/onboarding`

## Clerk Dashboard Configuration

### Step 1: Go to Paths Settings
1. Visit [Clerk Dashboard](https://dashboard.clerk.com)
2. Select your application
3. Go to **Paths** in the sidebar

### Step 2: Configure Redirect URLs
Set these paths in the Clerk Dashboard:

- **After sign in**: `/app`
- **After sign up**: `/app`
- **After create organization**: `/app`  ← **CRITICAL**
- **After leave organization**: `/app`

### Step 3: Organization Settings
1. Go to **Organizations** in the sidebar
2. Make sure **"Enable Organizations"** is ON
3. Configure as needed for your use case

## Testing

1. Sign out and clear cookies
2. Create a new test user
3. After sign up, you should be redirected to `/app`
4. Create a new organization via the org switcher
5. After creating org, you should stay on `/app` (not redirect to `/onboarding`)

