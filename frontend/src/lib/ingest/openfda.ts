const FDA_BASE = "https://api.fda.gov/drug/enforcement.json"; // swap to device/food if needed

export interface OpenFDAItem {
  source: "openfda";
  title: string;
  url?: string;
  jurisdiction?: string;
  published_at?: string | null;
  raw: any;
}

export interface OpenFDAResult {
  items: OpenFDAItem[];
  note?: string;
}

export async function fetchOpenFDA({ since }: { since: Date }): Promise<OpenFDAResult> {
  try {
    // For now, let's fetch recent data without date filtering to test the connection
    // OpenFDA's date range syntax can be tricky, so we'll start simple
    const params = new URLSearchParams({
      limit: "100",
    });
    
    const url = `${FDA_BASE}?${params.toString()}${
      process.env.OPENFDA_KEY ? `&api_key=${process.env.OPENFDA_KEY}` : ""
    }`;

    console.log(`OpenFDA: Fetching recent enforcement data from: ${url}`);

    const headers: Record<string, string> = {
      "User-Agent": "KC-Intel/1.0",
      "Accept": "application/json",
    };

    const res = await fetch(url, {
      headers,
      // Add timeout to prevent hanging
      signal: AbortSignal.timeout(30000),
    });

    if (res.status === 429) {
      const retryAfter = res.headers.get("Retry-After");
      console.warn(`OpenFDA rate limited. Retry after: ${retryAfter || "unknown"}`);
      return { 
        items: [], 
        note: `Rate limited. Retry after: ${retryAfter || "unknown"}` 
      };
    }

    if (!res.ok) {
      const errorText = await res.text().catch(() => "Unknown error");
      console.error(`OpenFDA API error: ${res.status} ${res.statusText}`, errorText);
      return { 
        items: [], 
        note: `API error: ${res.status} ${res.statusText} - ${errorText}` 
      };
    }

    const data = await res.json();

    if (!data.results || !Array.isArray(data.results)) {
      console.warn("OpenFDA returned unexpected format:", data);
      return { 
        items: [], 
        note: data.error?.message || "Unexpected API response format" 
      };
    }

    // Map to normalized shape
    const items: OpenFDAItem[] = data.results.map((r: any) => ({
      source: "openfda" as const,
      title: `${r.product_description || "Product"} — ${r.reason_for_recall || "Recall"}`,
      url: r.more_code_info || r.classification || undefined,
      jurisdiction: r.state || r.country || undefined,
      published_at: parseFDAReportDate(r.report_date),
      raw: r,
    }));

    console.log(`OpenFDA: fetched ${items.length} items`);
    return { items };

  } catch (error) {
    if (error instanceof Error) {
      console.error("OpenFDA fetch error:", error.message);
      return { 
        items: [], 
        note: `Fetch error: ${error.message}` 
      };
    }
    
    console.error("OpenFDA unknown error:", error);
    return { 
      items: [], 
      note: "Unknown error occurred" 
    };
  }
}

function fmtDate(d: Date): string {
  return d.toISOString().slice(0,10).replace(/-/g,""); // YYYYMMDD
}

function parseFDAReportDate(s?: string): string | null {
  if (!s) return null;
  if (s.length !== 8) return s; // Return as-is if not YYYYMMDD format
  const y = s.slice(0,4), m = s.slice(4,6), d = s.slice(6,8);
  return `${y}-${m}-${d}`;
}