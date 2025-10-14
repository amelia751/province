import { SignedIn, SignedOut, SignInButton } from '@clerk/nextjs';
import { auth } from '@clerk/nextjs/server';
import { Button } from '@/components/ui/button';
import Sidebar from '@/components/ui/sidebar';
import { getOrganizationName, getPersonalAccountName } from '@/lib/organization';

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  const { userId, orgId } = await auth();

  let accountName: string | null = null;
  let isPersonalAccount = false;

  if (userId) {
    if (orgId) {
      accountName = await getOrganizationName();
      isPersonalAccount = false;
    } else {
      accountName = await getPersonalAccountName();
      isPersonalAccount = true;
    }
  }

  return (
    <div className="min-h-screen bg-white">
      <SignedIn>
        <div className="flex h-screen overflow-hidden">
          {/* Sidebar */}
          <Sidebar organizationName={accountName} isPersonalAccount={isPersonalAccount} />

          {/* Main content */}
          <div className="flex-1 overflow-auto">
            {children}
          </div>
        </div>
      </SignedIn>

      <SignedOut>
        <div className="min-h-screen flex items-center justify-center">
          <SignInButton>
            <Button>Sign In</Button>
          </SignInButton>
        </div>
      </SignedOut>
    </div>
  );
}
