import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ form_type: string; engagement_id: string }> }
) {
  try {
    const { form_type, engagement_id } = await params;
    const searchParams = request.nextUrl.searchParams;
    const tax_year = searchParams.get('tax_year') || '2024';
    const limit = searchParams.get('limit') || '50';

    const response = await fetch(
      `${BACKEND_URL}/api/v1/forms/${form_type}/${engagement_id}/versions?tax_year=${tax_year}&limit=${limit}`,
      {
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    const data = await response.json();

    if (!response.ok) {
      return NextResponse.json(
        { error: data.detail || 'Failed to fetch form versions' },
        { status: response.status }
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error('Error proxying to form versions API:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

