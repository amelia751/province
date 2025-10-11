import { SignedIn, SignedOut, SignInButton } from '@clerk/nextjs';
import { Button } from '@/components/ui/button';

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-white">
      <SignedIn>
        <div className="min-h-screen">
          {children}
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
