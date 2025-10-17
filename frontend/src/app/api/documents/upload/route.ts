import { NextRequest, NextResponse } from 'next/server';
import { auth } from '@clerk/nextjs/server';

export async function POST(request: NextRequest) {
  try {
    console.log('=== FRONTEND API UPLOAD DEBUG START ===');
    
    // Get the authenticated user
    const { userId } = await auth();
    console.log('User ID:', userId);
    
    if (!userId) {
      console.log('No user ID found, returning 401');
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const formData = await request.formData();
    const file = formData.get('file') as File;
    const engagementId = formData.get('engagementId') as string;
    const documentPath = formData.get('documentPath') as string;

    console.log('Form data received:');
    console.log('- File:', file?.name, file?.type, file?.size);
    console.log('- Engagement ID:', engagementId);
    console.log('- Document Path:', documentPath);

    if (!file || !engagementId || !documentPath) {
      console.log('Missing required fields');
      return NextResponse.json(
        { error: 'Missing required fields: file, engagementId, or documentPath' },
        { status: 400 }
      );
    }

    // Convert file to base64
    const arrayBuffer = await file.arrayBuffer();
    const buffer = Buffer.from(arrayBuffer);
    const base64Content = buffer.toString('base64');

    // Call the backend save_document function
    const backendUrl = `${process.env.BACKEND_URL || 'http://localhost:8000'}/api/v1/documents/save`;
    const requestBody = {
      engagement_id: engagementId,
      path: documentPath,
      content_b64: base64Content,
      mime_type: file.type || 'application/octet-stream',
    };
    
    console.log('Calling backend URL:', backendUrl);
    console.log('Request body (without base64):', { ...requestBody, content_b64: `[${base64Content.length} chars]` });
    
    const backendResponse = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(requestBody),
    });

    console.log('Backend response status:', backendResponse.status);
    console.log('Backend response headers:', Object.fromEntries(backendResponse.headers.entries()));

    if (!backendResponse.ok) {
      const errorText = await backendResponse.text();
      console.log('Backend error response text:', errorText);
      
      let errorData;
      try {
        errorData = JSON.parse(errorText);
      } catch {
        errorData = { error: errorText };
      }
      
      console.log('Parsed backend error:', errorData);
      return NextResponse.json(
        { error: `Backend error: ${errorData.error || errorData.detail || 'Unknown error'}` },
        { status: backendResponse.status }
      );
    }

    const resultText = await backendResponse.text();
    console.log('Backend success response text:', resultText);
    
    const result = JSON.parse(resultText);
    console.log('Parsed backend result:', result);
    console.log('=== FRONTEND API UPLOAD DEBUG END ===');

    return NextResponse.json({
      success: true,
      documentId: result.document_id,
      s3Key: result.s3_key,
      hash: result.hash,
      sizeBytes: result.size_bytes,
      fileName: file.name,
      fileSize: file.size,
      uploadedAt: new Date().toISOString(),
    });

  } catch (error) {
    console.error('=== FRONTEND API UPLOAD ERROR ===');
    console.error('Document upload error:', error);
    console.error('Error message:', error instanceof Error ? error.message : String(error));
    console.error('Error stack:', error instanceof Error ? error.stack : 'No stack');
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
