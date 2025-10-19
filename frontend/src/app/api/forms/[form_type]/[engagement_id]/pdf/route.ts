import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

export async function GET(
  request: NextRequest,
  { params }: { params: { form_type: string; engagement_id: string } }
) {
  try {
    const { form_type, engagement_id } = params;
    const searchParams = request.nextUrl.searchParams;
    const version = searchParams.get('version') || 'latest';
    const taxpayer = searchParams.get('taxpayer') || '';
    const tax_year = searchParams.get('tax_year') || '2024';

    const url = new URL(`${BACKEND_URL}/api/v1/forms/${form_type}/${engagement_id}/pdf`);
    url.searchParams.set('version', version);
    url.searchParams.set('tax_year', tax_year);
    if (taxpayer) {
      url.searchParams.set('taxpayer', taxpayer);
    }

    const response = await fetch(url.toString(), {
      redirect: 'follow',
    });

    if (!response.ok) {
      const data = await response.json().catch(() => ({ error: response.statusText }));
      return NextResponse.json(
        { error: data.detail || 'Failed to fetch form PDF' },
        { status: response.status }
      );
    }

    // Redirect to the signed S3 URL
    return NextResponse.redirect(response.url);
  } catch (error) {
    console.error('Error proxying to form PDF API:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
