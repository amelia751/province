const CL_BASE = "https://www.courtlistener.com/api/rest/v4";

export interface CourtListenerItem {
  source: "courtlistener";
  title: string;
  url?: string;
  court?: string;
  published_at?: string | null;
  raw: any;
}

export interface CourtListenerResult {
  items: CourtListenerItem[];
  note?: string;
}

export async function fetchCourtListener({ since }: { since: Date }): Promise<CourtListenerResult> {
  try {
    const params = new URLSearchParams({
      q: "ADA OR \"Title III\" OR product liability",
      page_size: "100",
      format: "json",
    });
    
    const url = `${CL_BASE}/search/?${params.toString()}`;

    const headers: Record<string, string> = {
      "User-Agent": "KC-Intel/1.0",
      "Accept": "application/json",
    };

    if (process.env.COURTLISTENER_TOKEN) {
      headers["Authorization"] = `Token ${process.env.COURTLISTENER_TOKEN}`;
    }

    const res = await fetch(url, {
      headers,
      // Add timeout to prevent hanging
      signal: AbortSignal.timeout(30000),
    });

    if (res.status === 429) {
      const retryAfter = res.headers.get("Retry-After");
      console.warn(`CourtListener rate limited. Retry after: ${retryAfter || "unknown"}`);
      return { 
        items: [], 
        note: `Rate limited. Retry after: ${retryAfter || "unknown"}` 
      };
    }

    if (!res.ok) {
      console.error(`CourtListener API error: ${res.status} ${res.statusText}`);
      return { 
        items: [], 
        note: `API error: ${res.status} ${res.statusText}` 
      };
    }

    const data = await res.json();
    
    if (!data.results || !Array.isArray(data.results)) {
      console.warn("CourtListener returned unexpected format:", data);
      return { 
        items: [], 
        note: "Unexpected API response format" 
      };
    }

    // Map to normalized shape
    const items: CourtListenerItem[] = data.results.map((r: any) => ({
      source: "courtlistener" as const,
      title: r.caseName || r.caption || r.case_name || "Case",
      url: r.absolute_url 
        ? `https://www.courtlistener.com${r.absolute_url}` 
        : r.url || undefined,
      court: r.court || r.cluster?.docket?.court || r.court_name || undefined,
      published_at: r.dateFiled || r.date_created || r.date_filed || null,
      raw: r,
    }));

    console.log(`CourtListener: fetched ${items.length} items`);
    return { items };

  } catch (error) {
    if (error instanceof Error) {
      console.error("CourtListener fetch error:", error.message);
      return { 
        items: [], 
        note: `Fetch error: ${error.message}` 
      };
    }
    
    console.error("CourtListener unknown error:", error);
    return { 
      items: [], 
      note: "Unknown error occurred" 
    };
  }
}