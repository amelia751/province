import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@clerk/nextjs/server';
import { v4 as uuidv4 } from 'uuid';

// Helper function to determine the current tax year
function getCurrentTaxYear(): number {
  const now = new Date();
  const currentYear = now.getFullYear();
  
  // Tax year is typically the previous year if we're before April 15th
  // For simplicity, we'll use the current year for 2025 filings
  if (currentYear === 2025) {
    return 2025;
  }
  
  // After April 15th, we're working on next year's taxes
  const taxDeadline = new Date(currentYear, 3, 15); // April 15th
  return now > taxDeadline ? currentYear + 1 : currentYear;
}

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

    const { filingYear } = await request.json();
    
    // Use provided filing year or determine current tax year
    const taxYear = filingYear || getCurrentTaxYear();

    // Call backend to create engagement
    const backendResponse = await fetch(`${process.env.BACKEND_URL || 'http://localhost:8000'}/api/v1/tax-engagements`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        filing_year: taxYear,
        status: 'draft'
      }),
    });

    if (!backendResponse.ok) {
      const errorData = await backendResponse.json();
      throw new Error(`Backend error: ${errorData.detail || 'Failed to create engagement'}`);
    }

    const result = await backendResponse.json();

    return NextResponse.json({
      success: true,
      engagementId: result.engagement_id,  // This is now just the UUID
      filingYear: result.filing_year,
      status: result.status,
      createdAt: result.created_at,
    });

  } catch (error) {
    console.error('Tax engagement creation error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  try {
    // Get the authenticated user
    const { userId } = await auth();
    
    if (!userId) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const { searchParams } = new URL(request.url);
    const filingYear = searchParams.get('filingYear');

    // Get user's tax engagements
    const backendResponse = await fetch(`${process.env.BACKEND_URL || 'http://localhost:8000'}/api/v1/tax-engagements?user_id=${userId}${filingYear ? `&filing_year=${filingYear}` : ''}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!backendResponse.ok) {
      // Return empty array if backend endpoint doesn't exist yet
      return NextResponse.json({
        success: true,
        engagements: [],
      });
    }

    const result = await backendResponse.json();

    // Transform backend response to match frontend expectations
    const transformedEngagements = (result.engagements || []).map((engagement: any) => ({
      engagementId: engagement.engagement_id,
      userId: engagement.user_id,
      filingYear: engagement.filing_year,
      status: engagement.status,
      createdAt: engagement.created_at,
      updatedAt: engagement.updated_at,
    }));

    return NextResponse.json({
      success: true,
      engagements: transformedEngagements,
    });

  } catch (error) {
    console.error('Tax engagement fetch error:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
