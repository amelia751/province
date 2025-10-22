import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ form_type: string }> }
) {
  try {
    const { form_type } = await params;
    const searchParams = request.nextUrl.searchParams;
    const tax_year = searchParams.get('tax_year') || '2024';

    // Fetch from backend - backend returns a redirect to S3
    const response = await fetch(
      `${BACKEND_URL}/api/v1/forms/${form_type}/template?tax_year=${tax_year}`,
      {
        redirect: 'manual', // Don't follow redirects automatically
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    // If backend returns a redirect (307), forward it to the client
    if (response.status === 307 || response.status === 302 || response.status === 301) {
      const location = response.headers.get('location');
      if (location) {
        return NextResponse.redirect(location);
      }
    }

    // If backend returns 404, return 404
    if (response.status === 404) {
      const data = await response.json();
      return NextResponse.json(
        { error: data.detail || 'Template not found' },
        { status: 404 }
      );
    }

    // For any other response, try to parse and return
    const data = await response.json();
    
    if (!response.ok) {
      return NextResponse.json(
        { error: data.detail || 'Failed to fetch template form' },
        { status: response.status }
      );
    }

    return NextResponse.json(data);
  } catch (error) {
    console.error('Error proxying to template API:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}

