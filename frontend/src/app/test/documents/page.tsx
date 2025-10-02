import { auth } from '@clerk/nextjs/server';
import { redirect } from 'next/navigation';
import { createServerSupabaseClient } from '@/lib/supabase-server';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default async function DocumentsTestPage() {
  const { userId, orgId } = await auth();
  
  if (!userId) {
    redirect('/');
  }

  if (!orgId) {
    redirect('/app');
  }

  const supabase = createServerSupabaseClient();

  // Set RLS context
  await supabase.rpc('set_config', {
    setting_name: 'app.org_id',
    setting_value: orgId,
    is_local: true
  });

  // Fetch documents with their text
  const { data: documents, error } = await supabase
    .from('document')
    .select(`
      id,
      source,
      source_ref,
      object_key,
      hash,
      ingested_at,
      processed_at,
      doc_text (
        text,
        token_count,
        created_at
      )
    `)
    .order('processed_at', { ascending: false })
    .limit(20);

  if (error) {
    console.error('Error fetching documents:', error);
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-4">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="text-center py-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Processed Documents
          </h1>
          <p className="text-xl text-gray-600">
            View documents that have been ingested and processed
          </p>
        </div>

        {error && (
          <Card className="border-red-200">
            <CardHeader>
              <CardTitle className="text-red-600">Error</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-red-600">Failed to load documents: {error.message}</p>
            </CardContent>
          </Card>
        )}

        {documents && documents.length === 0 && (
          <Card>
            <CardHeader>
              <CardTitle>No Documents Found</CardTitle>
              <CardDescription>
                No processed documents found. Try running the processing pipeline first.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <a 
                href="/test/processing" 
                className="text-blue-600 hover:underline"
              >
                → Go to Processing Test
              </a>
            </CardContent>
          </Card>
        )}

        {documents && documents.length > 0 && (
          <div className="space-y-4">
            <div className="text-center">
              <p className="text-lg font-medium">
                Found {documents.length} processed documents
              </p>
            </div>

            {documents.map((doc: any) => (
              <Card key={doc.id}>
                <CardHeader>
                  <CardTitle className="text-lg">
                    {doc.source.toUpperCase()} Document
                  </CardTitle>
                  <CardDescription>
                    Processed: {new Date(doc.processed_at).toLocaleString()}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="font-medium">Source:</span> {doc.source}
                      </div>
                      <div>
                        <span className="font-medium">Hash:</span> {doc.hash.slice(0, 12)}...
                      </div>
                      <div>
                        <span className="font-medium">Ingested:</span> {new Date(doc.ingested_at).toLocaleString()}
                      </div>
                      <div>
                        <span className="font-medium">Tokens:</span> {doc.doc_text?.[0]?.token_count || 'N/A'}
                      </div>
                    </div>

                    {doc.object_key && doc.object_key.startsWith('http') && (
                      <div>
                        <a 
                          href={doc.object_key} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:underline text-sm"
                        >
                          → View Original Source
                        </a>
                      </div>
                    )}

                    {doc.doc_text?.[0]?.text && (
                      <details className="text-sm">
                        <summary className="cursor-pointer font-medium">
                          View Processed Text ({doc.doc_text[0].token_count} tokens)
                        </summary>
                        <div className="mt-2 p-3 bg-gray-50 rounded max-h-64 overflow-auto">
                          <pre className="whitespace-pre-wrap text-xs">
                            {doc.doc_text[0].text.slice(0, 1000)}
                            {doc.doc_text[0].text.length > 1000 && '...'}
                          </pre>
                        </div>
                      </details>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        <div className="text-center py-4">
          <a 
            href="/test/processing" 
            className="text-blue-600 hover:underline"
          >
            ← Back to Processing Test
          </a>
        </div>
      </div>
    </div>
  );
}