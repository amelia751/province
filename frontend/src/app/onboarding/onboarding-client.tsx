'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import OnboardingForm from '@/components/onboarding/onboarding-form';
import { completeOnboarding } from '../actions/complete-onboarding';

interface OnboardingClientProps {
  orgId: string;
}

export default function OnboardingClient({ orgId }: OnboardingClientProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const handleComplete = async (formData: any) => {
    setLoading(true);
    setError(null);

    try {
      await completeOnboarding(formData);
      // The server action will redirect to /app
    } catch (err) {
      console.error('Onboarding error:', err);
      setError(err instanceof Error ? err.message : 'An error occurred during onboarding');
      setLoading(false);
    }
  };

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center p-4">
        <div className="bg-white p-6 rounded-lg shadow-lg max-w-md w-full text-center">
          <h2 className="text-xl font-bold text-red-600 mb-4">Setup Error</h2>
          <p className="text-gray-700 mb-4">{error}</p>
          <button
            onClick={() => {
              setError(null);
              setLoading(false);
            }}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <OnboardingForm 
      onComplete={handleComplete} 
      loading={loading} 
    />
  );
}