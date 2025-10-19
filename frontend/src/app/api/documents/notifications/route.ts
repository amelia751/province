import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@clerk/nextjs/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function GET(request: NextRequest) {
  try {
    const { userId } = auth();

    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    // Get engagement_id from query parameters
    const { searchParams } = new URL(request.url);
    const engagementId = searchParams.get('engagement_id');
    const since = searchParams.get('since');
    const limit = searchParams.get('limit') || '10';

    if (!engagementId) {
      return NextResponse.json({ error: 'engagement_id is required' }, { status: 400 });
    }

    // Build query parameters
    const queryParams = new URLSearchParams({
      limit,
      ...(since && { since })
    });

    // Call backend notifications API
    const backendResponse = await fetch(
      `${BACKEND_URL}/api/v1/documents/notifications/${engagementId}?${queryParams}`,
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId, // Pass user ID for authorization
        },
      }
    );

    if (!backendResponse.ok) {
      const errorData = await backendResponse.json().catch(() => ({ error: backendResponse.statusText }));
      throw new Error(errorData.detail || errorData.error || 'Failed to fetch notifications');
    }

    const data = await backendResponse.json();
    return NextResponse.json(data);

  } catch (error: any) {
    console.error('Error fetching document notifications:', error);
    return NextResponse.json({ error: error.message || 'Internal Server Error' }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const { userId } = auth();

    if (!userId) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }

    const body = await request.json();
    const { engagement_id, timestamps } = body;

    if (!engagement_id || !timestamps) {
      return NextResponse.json({ error: 'engagement_id and timestamps are required' }, { status: 400 });
    }

    // Call backend to mark notifications as read
    const backendResponse = await fetch(
      `${BACKEND_URL}/api/v1/documents/notifications/${engagement_id}/mark-read`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-ID': userId,
        },
        body: JSON.stringify({ timestamps }),
      }
    );

    if (!backendResponse.ok) {
      const errorData = await backendResponse.json().catch(() => ({ error: backendResponse.statusText }));
      throw new Error(errorData.detail || errorData.error || 'Failed to mark notifications as read');
    }

    const data = await backendResponse.json();
    return NextResponse.json(data);

  } catch (error: any) {
    console.error('Error marking notifications as read:', error);
    return NextResponse.json({ error: error.message || 'Internal Server Error' }, { status: 500 });
  }
}
