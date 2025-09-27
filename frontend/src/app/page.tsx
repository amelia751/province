import { redirect } from 'next/navigation';
import { auth } from '@clerk/nextjs/server';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Navbar } from '@/components/navbar';
import { Shield, Zap, BarChart3 } from 'lucide-react';

export default async function Home() {
  const { userId } = await auth();
  
  // Auto-redirect signed-in users to onboarding (which will create org if needed)
  if (userId) {
    redirect('/onboarding');
  }

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Navigation */}
      <Navbar />

      {/* Hero Section */}
      <main className="relative">
        {/* Background gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-blue-900/20 via-black to-purple-900/20" />
        
        {/* Content */}
        <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 pt-20 pb-16">
          <div className="text-center">
            <h1 className="text-4xl font-bold tracking-tight sm:text-6xl lg:text-7xl">
              Professional
              <br />
              <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                Class AI
              </span>
            </h1>
            <p className="mx-auto mt-6 max-w-2xl text-lg leading-8 text-white/80">
              Domain-specific AI for law firms, professional service providers, and the Fortune 500.
            </p>
            <div className="mt-10 flex items-center justify-center gap-x-6">
              <Link href="/auth">
                <Button size="lg" className="bg-white text-black hover:bg-white/90">
                  Request a Demo
                </Button>
              </Link>
            </div>
          </div>
        </div>

        {/* Features Grid */}
        <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-16">
          <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-3">
            <div className="relative group">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg blur opacity-25 group-hover:opacity-75 transition duration-1000 group-hover:duration-200"></div>
              <div className="relative bg-black border border-white/10 rounded-lg p-6">
                <div className="w-12 h-12 bg-blue-500/20 rounded-lg flex items-center justify-center mb-4">
                  <Zap className="w-6 h-6 text-blue-400" />
                </div>
                <h3 className="text-xl font-semibold mb-2">Lightning Fast</h3>
                <p className="text-white/60">Process thousands of legal documents in seconds with our advanced AI engine.</p>
              </div>
            </div>

            <div className="relative group">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg blur opacity-25 group-hover:opacity-75 transition duration-1000 group-hover:duration-200"></div>
              <div className="relative bg-black border border-white/10 rounded-lg p-6">
                <div className="w-12 h-12 bg-purple-500/20 rounded-lg flex items-center justify-center mb-4">
                  <Shield className="w-6 h-6 text-purple-400" />
                </div>
                <h3 className="text-xl font-semibold mb-2">Enterprise Security</h3>
                <p className="text-white/60">Bank-grade security with end-to-end encryption and compliance certifications.</p>
              </div>
            </div>

            <div className="relative group">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg blur opacity-25 group-hover:opacity-75 transition duration-1000 group-hover:duration-200"></div>
              <div className="relative bg-black border border-white/10 rounded-lg p-6">
                <div className="w-12 h-12 bg-green-500/20 rounded-lg flex items-center justify-center mb-4">
                  <BarChart3 className="w-6 h-6 text-green-400" />
                </div>
                <h3 className="text-xl font-semibold mb-2">Smart Analytics</h3>
                <p className="text-white/60">Get actionable insights from your legal data with AI-powered analytics.</p>
              </div>
            </div>
          </div>
        </div>

        {/* Background decoration */}
        <div className="absolute inset-0 -z-10 overflow-hidden">
          <div className="absolute left-[calc(50%-4rem)] top-10 -z-10 transform-gpu blur-3xl sm:left-[calc(50%-18rem)] lg:left-48 lg:top-[calc(50%-30rem)] xl:left-[calc(50%-24rem)]">
            <div className="aspect-[1108/632] w-[69.25rem] bg-gradient-to-r from-[#80caff] to-[#4f46e5] opacity-20"></div>
          </div>
        </div>
      </main>
    </div>
  );
}
