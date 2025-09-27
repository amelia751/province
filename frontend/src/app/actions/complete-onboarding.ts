'use server';

import { createOrganization, CreateOrganizationData } from '@/lib/organization';
import { redirect } from 'next/navigation';

export async function completeOnboarding(formData: CreateOrganizationData) {
  try {
    const result = await createOrganization(formData);
    
    if (!result.success) {
      throw new Error(result.error || 'Failed to create organization');
    }

    // Redirect to the main app page after successful onboarding
    redirect('/app');
  } catch (error) {
    console.error('Error in completeOnboarding:', error);
    throw error;
  }
}