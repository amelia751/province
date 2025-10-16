import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@clerk/nextjs/server';

interface UserDataItem {
  id: string;
  type: 'engagement' | 'document' | 's3_object';
  name: string;
  path?: string;
  size?: number;
  created_at?: string;
  updated_at?: string;
  metadata?: Record<string, any>;
}

interface UserDataSummary {
  engagements: UserDataItem[];
  documents: UserDataItem[];
  s3_objects: UserDataItem[];
  total_size: number;
  total_count: number;
}

export async function GET(request: NextRequest) {
  try {
    const { userId } = auth();
    
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const searchParams = request.nextUrl.searchParams;
    const requestedUserId = searchParams.get('userId');

    // For development, allow checking any user's data
    // In production, you might want to restrict this
    const targetUserId = requestedUserId || userId;

    // Call backend service to get user data
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
    
    const response = await fetch(`${backendUrl}/file-structure/dev/user-data/${targetUserId}`, {
      headers: {
        'Authorization': `Bearer ${userId}`, // Use Clerk user ID as auth
      },
    });

    if (!response.ok) {
      throw new Error(`Backend request failed: ${response.statusText}`);
    }

    const userData: UserDataSummary = await response.json();

    return NextResponse.json(userData);

  } catch (error) {
    console.error('Error fetching user data:', error);
    return NextResponse.json(
      { error: 'Failed to fetch user data' },
      { status: 500 }
    );
  }
}

