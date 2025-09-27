'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function ProcessingTestPage() {
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState<any>(null);

  const runProcessing = async () => {
    setIsRunning(true);
    setResult(null);

    try {
      const response = await fetch('/api/processing/run', {
        method: 'POST',
      });

      const data = await response.json();
      setResult(data);
    } catch (error) {
      setResult({
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-4">
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="text-center py-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Text Processing Test
          </h1>
          <p className="text-xl text-gray-600">
            Test the document ingestion and text processing pipeline
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Run Text Processing Pipeline</CardTitle>
            <CardDescription>
              This will fetch data from CourtListener, OpenFDA, and DOJ APIs, then process and store the text in the database.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button 
              onClick={runProcessing} 
              disabled={isRunning}
              className="w-full"
            >
              {isRunning ? 'Processing...' : 'Run Processing Pipeline'}
            </Button>
          </CardContent>
        </Card>

        {result && (
          <Card>
            <CardHeader>
              <CardTitle className={result.success ? 'text-green-600' : 'text-red-600'}>
                {result.success ? '✅ Success' : '❌ Error'}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {result.message && (
                  <p className="text-lg font-medium">{result.message}</p>
                )}
                
                {result.processed !== undefined && (
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="font-medium">Processed:</span> {result.processed}
                    </div>
                    <div>
                      <span className="font-medium">Total:</span> {result.total || 'N/A'}
                    </div>
                  </div>
                )}

                {result.errors && result.errors.length > 0 && (
                  <div>
                    <h4 className="font-medium text-red-600 mb-2">Errors:</h4>
                    <ul className="list-disc list-inside space-y-1 text-sm text-red-600">
                      {result.errors.map((error: string, index: number) => (
                        <li key={index}>{error}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {result.error && (
                  <div className="text-red-600 text-sm">
                    <span className="font-medium">Error:</span> {result.error}
                  </div>
                )}

                <div className="text-xs text-gray-500">
                  <span className="font-medium">Timestamp:</span> {result.timestamp}
                </div>

                <details className="text-xs">
                  <summary className="cursor-pointer font-medium">Raw Response</summary>
                  <pre className="mt-2 p-2 bg-gray-100 rounded overflow-auto">
                    {JSON.stringify(result, null, 2)}
                  </pre>
                </details>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}