import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@clerk/nextjs/server';

export async function POST(request: NextRequest) {
  try {
    const { userId } = auth();
    
    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const body = await request.json();
    const targetUserId = body.userId || userId;

    // Call backend service to cleanup user data
    const backendUrl = process.env.BACKEND_URL || 'http://localhost:8000';
    
    const response = await fetch(`${backendUrl}/file-structure/dev/cleanup-user-data`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${userId}`, // Use Clerk user ID as auth
      },
      body: JSON.stringify({
        userId: targetUserId,
        requestedBy: userId
      }),
    });

    if (!response.ok) {
      throw new Error(`Backend request failed: ${response.statusText}`);
    }

    const result = await response.json();

    return NextResponse.json(result);

  } catch (error) {
    console.error('Error cleaning up user data:', error);
    return NextResponse.json(
      { error: 'Failed to cleanup user data' },
      { status: 500 }
    );
  }
}

