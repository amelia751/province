import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@clerk/nextjs/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export async function DELETE(request: NextRequest) {
  try {
    // Get the authenticated user
    const { userId } = await auth();
    
    if (!userId) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const { document_key } = await request.json();
    
    if (!document_key) {
      return NextResponse.json(
        { error: 'Document key is required' },
        { status: 400 }
      );
    }

    console.log('🗑️ Deleting document for user:', userId, 'document:', document_key);

    // Call backend API
    const response = await fetch(`${BACKEND_URL}/api/v1/documents/delete`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        document_key: document_key
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ Backend error deleting document:', response.status, errorText);
      return NextResponse.json(
        { error: `Backend error: ${response.status} - ${errorText}` },
        { status: response.status }
      );
    }

    const result = await response.json();
    console.log('✅ Document deleted successfully:', document_key);

    return NextResponse.json(result);

  } catch (error) {
    console.error('❌ Error in delete document API:', error);
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
