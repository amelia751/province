import { SignedOut, SignInButton } from '@clerk/nextjs';
import { redirect } from 'next/navigation';
import { auth } from '@clerk/nextjs/server';
import { Button } from '@/components/ui/button';
import { Navbar } from '@/components/navbar';
import { ArrowRight, CheckCircle2, Zap, Shield, Brain } from 'lucide-react';

export default async function Home() {
  const { userId } = await auth();

  // Auto-redirect signed-in users to app
  if (userId) {
    redirect('/app');
  }

  return (
    <div className="min-h-screen bg-white">
      <Navbar />

      {/* Hero Section */}
      <section className="container mx-auto px-4 pt-20 pb-32">
        <div className="max-w-4xl mx-auto text-center space-y-8">
          <h1 className="text-6xl md:text-7xl font-bold tracking-tight text-black">
            Your AI-native tax filing system
          </h1>
          <p className="text-xl md:text-2xl text-gray-600 max-w-2xl mx-auto leading-relaxed">
            Province transforms tax preparation with intelligent automation, making complex tax work simple and efficient.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center pt-4">
            <SignedOut>
              <SignInButton mode="modal">
                <Button size="lg" className="bg-black hover:bg-gray-800 text-white px-8 py-6 text-lg rounded-lg">
                  Get started free
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </SignInButton>
            </SignedOut>
            <Button size="lg" variant="outline" className="px-8 py-6 text-lg rounded-lg border-2">
              Watch demo
            </Button>
          </div>
          <p className="text-sm text-gray-500">No credit card required • Free forever</p>
        </div>
      </section>

      {/* Features Grid */}
      <section className="container mx-auto px-4 py-20 border-t">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-4xl font-bold text-center mb-16 text-black">
            Everything you need for tax preparation
          </h2>
          <div className="grid md:grid-cols-3 gap-12">
            <div className="space-y-4">
              <div className="w-12 h-12 bg-black rounded-lg flex items-center justify-center">
                <Brain className="h-6 w-6 text-white" />
              </div>
              <h3 className="text-2xl font-semibold text-black">AI-powered</h3>
              <p className="text-gray-600 leading-relaxed">
                Intelligent agents automatically extract W-2 data, calculate deductions, and generate tax forms with precision.
              </p>
            </div>
            <div className="space-y-4">
              <div className="w-12 h-12 bg-black rounded-lg flex items-center justify-center">
                <Zap className="h-6 w-6 text-white" />
              </div>
              <h3 className="text-2xl font-semibold text-black">Lightning fast</h3>
              <p className="text-gray-600 leading-relaxed">
                Complete tax returns in minutes, not hours. Upload documents and get instant analysis and calculations.
              </p>
            </div>
            <div className="space-y-4">
              <div className="w-12 h-12 bg-black rounded-lg flex items-center justify-center">
                <Shield className="h-6 w-6 text-white" />
              </div>
              <h3 className="text-2xl font-semibold text-black">Secure & compliant</h3>
              <p className="text-gray-600 leading-relaxed">
                Bank-level encryption and IRS-compliant workflows ensure your data is always protected and accurate.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Social Proof */}
      <section className="container mx-auto px-4 py-20 border-t">
        <div className="max-w-4xl mx-auto">
          <div className="space-y-8">
            <h2 className="text-4xl font-bold text-center text-black">
              Trusted by tax professionals
            </h2>
            <div className="grid md:grid-cols-2 gap-8">
              <div className="space-y-4 p-8 border rounded-lg hover:border-gray-400 transition-colors">
                <div className="flex items-start space-x-4">
                  <CheckCircle2 className="h-6 w-6 text-black flex-shrink-0 mt-1" />
                  <div>
                    <h4 className="font-semibold text-lg text-black mb-2">Automated W-2 extraction</h4>
                    <p className="text-gray-600">
                      Upload any W-2 form and watch as AI extracts all relevant data with 99.9% accuracy.
                    </p>
                  </div>
                </div>
              </div>
              <div className="space-y-4 p-8 border rounded-lg hover:border-gray-400 transition-colors">
                <div className="flex items-start space-x-4">
                  <CheckCircle2 className="h-6 w-6 text-black flex-shrink-0 mt-1" />
                  <div>
                    <h4 className="font-semibold text-lg text-black mb-2">Smart deadline tracking</h4>
                    <p className="text-gray-600">
                      Never miss a filing deadline with intelligent reminders and calendar integration.
                    </p>
                  </div>
                </div>
              </div>
              <div className="space-y-4 p-8 border rounded-lg hover:border-gray-400 transition-colors">
                <div className="flex items-start space-x-4">
                  <CheckCircle2 className="h-6 w-6 text-black flex-shrink-0 mt-1" />
                  <div>
                    <h4 className="font-semibold text-lg text-black mb-2">Real-time collaboration</h4>
                    <p className="text-gray-600">
                      Work together with your team seamlessly with live updates and shared workspaces.
                    </p>
                  </div>
                </div>
              </div>
              <div className="space-y-4 p-8 border rounded-lg hover:border-gray-400 transition-colors">
                <div className="flex items-start space-x-4">
                  <CheckCircle2 className="h-6 w-6 text-black flex-shrink-0 mt-1" />
                  <div>
                    <h4 className="font-semibold text-lg text-black mb-2">Instant calculations</h4>
                    <p className="text-gray-600">
                      Get immediate tax calculations and refund estimates as you work through returns.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-4 py-32 border-t">
        <div className="max-w-3xl mx-auto text-center space-y-8">
          <h2 className="text-5xl font-bold text-black">
            Ready to transform your tax workflow?
          </h2>
          <p className="text-xl text-gray-600">
            Join thousands of tax professionals who trust Province for their tax preparation needs.
          </p>
          <SignedOut>
            <SignInButton mode="modal">
              <Button size="lg" className="bg-black hover:bg-gray-800 text-white px-8 py-6 text-lg rounded-lg">
                Start for free
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </SignInButton>
          </SignedOut>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t py-12">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center space-x-2 mb-4 md:mb-0">
              <span className="font-semibold text-black">Province</span>
            </div>
            <p className="text-sm text-gray-600">
              © 2025 Province. All rights reserved.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
