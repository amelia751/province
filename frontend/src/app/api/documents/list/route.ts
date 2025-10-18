import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@clerk/nextjs/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    // Get the authenticated user
    const { userId } = await auth();
    
    if (!userId) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    console.log('📋 Listing documents for user:', userId);

    // Call backend API
    const response = await fetch(`${BACKEND_URL}/api/v1/documents/list`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ Backend error listing documents:', response.status, errorText);
      return NextResponse.json(
        { error: `Backend error: ${response.status} - ${errorText}` },
        { status: response.status }
      );
    }

    const result = await response.json();
    console.log('✅ Documents listed successfully:', result.count, 'documents');

    return NextResponse.json(result);

  } catch (error) {
    console.error('❌ Error in list documents API:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
