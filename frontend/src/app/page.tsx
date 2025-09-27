import { SignedOut, SignInButton } from '@clerk/nextjs';
import { redirect } from 'next/navigation';
import { auth } from '@clerk/nextjs/server';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default async function Home() {
  const { userId } = await auth();
  
  // Auto-redirect signed-in users to onboarding (which will create org if needed)
  if (userId) {
    redirect('/onboarding');
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center space-y-4">
          <div className="mx-auto w-16 h-16 bg-gradient-to-br from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
            <div className="w-8 h-8 bg-white rounded-md"></div>
          </div>
          <CardTitle className="text-2xl font-bold">Welcome to Province</CardTitle>
          <CardDescription className="text-base">
            Get started by signing in to your account
          </CardDescription>
        </CardHeader>
        <CardContent>
          <SignedOut>
            <SignInButton mode="modal">
              <Button size="lg" className="w-full">
                Sign In
              </Button>
            </SignInButton>
          </SignedOut>
        </CardContent>
      </Card>
    </div>
  );
}
