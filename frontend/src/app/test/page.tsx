"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function TestPage() {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const testIngestSources = async () => {
    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const response = await fetch("/api/ingest/run", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto py-8 px-4 max-w-4xl">
      <div className="space-y-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold tracking-tight">Data Ingestion Test</h1>
          <p className="text-muted-foreground mt-2">
            Test the CourtListener, OpenFDA, and DOJ ADA integrations and see fetched results
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Test Data Ingestion</CardTitle>
            <CardDescription>
              This will call the /api/ingest/run endpoint to fetch data from CourtListener, OpenFDA, and DOJ ADA
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button 
              onClick={testIngestSources} 
              disabled={loading}
              className="w-full"
            >
              {loading ? "Fetching..." : "Test All Sources"}
            </Button>

            {error && (
              <Card className="border-red-200 bg-red-50">
                <CardHeader>
                  <CardTitle className="text-red-800 text-lg">Error</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-red-700">{error}</p>
                </CardContent>
              </Card>
            )}

            {results && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-green-800">Results</CardTitle>
                  <CardDescription>
                    Fetched at: {results.timestamp}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="space-y-2">
                    <h3 className="font-semibold">CourtListener Results:</h3>
                    {results.results.cl.status === "fulfilled" ? (
                      <div className="space-y-2">
                        <p className="text-sm text-muted-foreground">
                          Items found: {results.results.cl.value.items.length}
                        </p>
                        {results.results.cl.value.note && (
                          <p className="text-sm text-orange-600">
                            Note: {results.results.cl.value.note}
                          </p>
                        )}
                        <div className="max-h-96 overflow-y-auto border rounded-md p-4 bg-gray-50">
                          {results.results.cl.value.items.length > 0 ? (
                            <div className="space-y-3">
                              {results.results.cl.value.items.slice(0, 5).map((item: any, idx: number) => (
                                <Card key={idx} className="bg-white">
                                  <CardContent className="pt-4">
                                    <h4 className="font-medium text-sm">{item.title}</h4>
                                    {item.court && (
                                      <p className="text-xs text-muted-foreground mt-1">
                                        Court: {item.court}
                                      </p>
                                    )}
                                    {item.published_at && (
                                      <p className="text-xs text-muted-foreground">
                                        Date: {item.published_at}
                                      </p>
                                    )}
                                    {item.url && (
                                      <a 
                                        href={item.url} 
                                        target="_blank" 
                                        rel="noopener noreferrer"
                                        className="text-xs text-blue-600 hover:underline block mt-1"
                                      >
                                        View Case →
                                      </a>
                                    )}
                                  </CardContent>
                                </Card>
                              ))}
                              {results.results.cl.value.items.length > 5 && (
                                <p className="text-xs text-muted-foreground text-center">
                                  ... and {results.results.cl.value.items.length - 5} more items
                                </p>
                              )}
                            </div>
                          ) : (
                            <p className="text-sm text-muted-foreground">No items found</p>
                          )}
                        </div>
                      </div>
                    ) : (
                      <Card className="border-red-200 bg-red-50">
                        <CardContent className="pt-4">
                          <p className="text-red-700 text-sm">
                            Error: {results.results.cl.reason}
                          </p>
                        </CardContent>
                      </Card>
                    )}
                  </div>

                  <div className="space-y-2">
                    <h3 className="font-semibold">OpenFDA Results:</h3>
                    {results.results.fda.status === "fulfilled" ? (
                      <div className="space-y-2">
                        <p className="text-sm text-muted-foreground">
                          Items found: {results.results.fda.value.items.length}
                        </p>
                        {results.results.fda.value.note && (
                          <p className="text-sm text-orange-600">
                            Note: {results.results.fda.value.note}
                          </p>
                        )}
                        <div className="max-h-96 overflow-y-auto border rounded-md p-4 bg-blue-50">
                          {results.results.fda.value.items.length > 0 ? (
                            <div className="space-y-3">
                              {results.results.fda.value.items.slice(0, 5).map((item: any, idx: number) => (
                                <Card key={idx} className="bg-white">
                                  <CardContent className="pt-4">
                                    <h4 className="font-medium text-sm">{item.title}</h4>
                                    {item.jurisdiction && (
                                      <p className="text-xs text-muted-foreground mt-1">
                                        Jurisdiction: {item.jurisdiction}
                                      </p>
                                    )}
                                    {item.published_at && (
                                      <p className="text-xs text-muted-foreground">
                                        Date: {item.published_at}
                                      </p>
                                    )}
                                    <p className="text-xs text-blue-600 mt-1">
                                      Source: FDA Drug Enforcement
                                    </p>
                                  </CardContent>
                                </Card>
                              ))}
                              {results.results.fda.value.items.length > 5 && (
                                <p className="text-xs text-muted-foreground text-center">
                                  ... and {results.results.fda.value.items.length - 5} more items
                                </p>
                              )}
                            </div>
                          ) : (
                            <p className="text-sm text-muted-foreground">No items found</p>
                          )}
                        </div>
                      </div>
                    ) : (
                      <Card className="border-red-200 bg-red-50">
                        <CardContent className="pt-4">
                          <p className="text-red-700 text-sm">
                            Error: {results.results.fda.reason}
                          </p>
                        </CardContent>
                      </Card>
                    )}
                  </div>

                  <div className="space-y-2">
                    <h3 className="font-semibold">DOJ ADA Results:</h3>
                    {results.results.doj.status === "fulfilled" ? (
                      <div className="space-y-2">
                        <p className="text-sm text-muted-foreground">
                          Items found: {results.results.doj.value.items.length}
                        </p>
                        {results.results.doj.value.sources && (
                          <div className="text-xs text-muted-foreground bg-gray-100 p-2 rounded">
                            <p>Sources: ADA Cases ({results.results.doj.value.sources.ada_cases.count}), 
                               OPA RSS ({results.results.doj.value.sources.opa_rss.count})</p>
                          </div>
                        )}
                        {results.results.doj.value.note && (
                          <p className="text-sm text-orange-600">
                            Note: {results.results.doj.value.note}
                          </p>
                        )}
                        <div className="max-h-96 overflow-y-auto border rounded-md p-4 bg-green-50">
                          {results.results.doj.value.items.length > 0 ? (
                            <div className="space-y-3">
                              {results.results.doj.value.items.slice(0, 5).map((item: any, idx: number) => (
                                <Card key={idx} className="bg-white">
                                  <CardContent className="pt-4">
                                    <h4 className="font-medium text-sm">{item.title}</h4>
                                    {item.url && (
                                      <a 
                                        href={item.url} 
                                        target="_blank" 
                                        rel="noopener noreferrer"
                                        className="text-xs text-blue-600 hover:underline block mt-1"
                                      >
                                        View ADA Case →
                                      </a>
                                    )}
                                    <div className="flex justify-between items-center mt-1">
                                      <p className="text-xs text-green-600">
                                        Source: {item.source === "doj_opa_rss" ? "DOJ Press Release" : "ADA.gov Cases"}
                                      </p>
                                      {item.published_at && (
                                        <p className="text-xs text-muted-foreground">
                                          {new Date(item.published_at).toLocaleDateString()}
                                        </p>
                                      )}
                                    </div>
                                  </CardContent>
                                </Card>
                              ))}
                              {results.results.doj.value.items.length > 5 && (
                                <p className="text-xs text-muted-foreground text-center">
                                  ... and {results.results.doj.value.items.length - 5} more items
                                </p>
                              )}
                            </div>
                          ) : (
                            <p className="text-sm text-muted-foreground">No items found</p>
                          )}
                        </div>
                      </div>
                    ) : (
                      <Card className="border-red-200 bg-red-50">
                        <CardContent className="pt-4">
                          <p className="text-red-700 text-sm">
                            Error: {results.results.doj.reason}
                          </p>
                        </CardContent>
                      </Card>
                    )}
                  </div>

                  <details className="border rounded-md p-4">
                    <summary className="cursor-pointer text-sm font-medium">
                      Raw JSON Response
                    </summary>
                    <pre className="mt-2 text-xs bg-gray-100 p-2 rounded overflow-auto max-h-48">
                      {JSON.stringify(results, null, 2)}
                    </pre>
                  </details>
                </CardContent>
              </Card>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}