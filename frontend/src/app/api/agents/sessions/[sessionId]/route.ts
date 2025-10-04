import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function GET(
  request: NextRequest,
  { params }: { params: { sessionId: string } }
) {
  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/agents/sessions/${params.sessionId}`);
    
    if (!response.ok) {
      if (response.status === 404) {
        return NextResponse.json({ error: 'Session not found' }, { status: 404 });
      }
      throw new Error(`Backend responded with ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error proxying to backend:', error);
    return NextResponse.json(
      { error: 'Failed to communicate with backend' },
      { status: 500 }
    );
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { sessionId: string } }
) {
  try {
    const response = await fetch(`${BACKEND_URL}/api/v1/agents/sessions/${params.sessionId}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error(`Backend responded with ${response.status}`);
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error proxying to backend:', error);
    return NextResponse.json(
      { error: 'Failed to communicate with backend' },
      { status: 500 }
    );
  }
}