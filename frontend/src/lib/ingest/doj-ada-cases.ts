import * as cheerio from "cheerio";

export interface DOJADACaseItem {
  source: "doj_ada_cases";
  title: string;
  url?: string;
  published_at?: string | null;
  raw: any;
}

export interface DOJADACaseResult {
  items: DOJADACaseItem[];
  note?: string;
}

const BASE = "https://www.ada.gov/cases/";

export async function fetchAdaGovCases({ since }: { since: Date }): Promise<DOJADACaseResult> {
  try {
    console.log(`DOJ ADA Cases: Fetching from ${BASE}`);

    const headers: Record<string, string> = {
      "User-Agent": "KC-Intel/1.0 (Legal Intelligence Bot)",
      "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
      "Accept-Language": "en-US,en;q=0.5",
      "Connection": "keep-alive",
    };

    const res = await fetch(BASE, {
      headers,
      signal: AbortSignal.timeout(30000),
    });

    if (!res.ok) {
      console.error(`ADA.gov cases error: ${res.status} ${res.statusText}`);
      return { 
        items: [], 
        note: `HTTP error: ${res.status} ${res.statusText}` 
      };
    }

    const html = await res.text();
    const $ = cheerio.load(html);
    
    const items: DOJADACaseItem[] = [];

    // Strategy: Target links that go to /crt/ paths (Civil Rights Division cases)
    // and exclude obvious navigation/category pages
    
    // Look for links that go to actual case pages (/crt/ paths)
    $("a[href*='/crt/']").each((i, element) => {
      const $link = $(element);
      const href = $link.attr("href");
      const text = $link.text().trim();
      
      if (!href || !text) return;
      
      // Skip if it's clearly navigation/category (short text, category names)
      const navigationTerms = [
        "accessible technology",
        "web access", 
        "criminal justice",
        "law enforcement",
        "education",
        "healthcare",
        "housing",
        "employment",
        "voting",
        "state and local",
        "places of public accommodation",
        "featured topics",
        "additional topics",
        "most viewed",
        "press releases"
      ];
      
      const isNavigation = navigationTerms.some(term => 
        text.toLowerCase().includes(term.toLowerCase())
      );
      
      // Only include if it's not navigation and has substantial text
      if (!isNavigation && text.length > 20) {
        const absoluteUrl = href.startsWith("http") 
          ? href 
          : new URL(href, BASE).toString();
        
        items.push({
          source: "doj_ada_cases",
          title: text,
          url: absoluteUrl,
          published_at: null,
          raw: {
            href,
            text,
            method: "crt_path_case"
          },
        });
      }
    });

    // Look for PDF links (often case documents/settlements)
    $("a[href$='.pdf']").each((i, element) => {
      const $link = $(element);
      const href = $link.attr("href");
      const text = $link.text().trim();
      
      if (!href || !text) return;
      
      // Look for case-like PDF names
      if (text.length > 15 && (
          text.includes("Settlement") ||
          text.includes("Agreement") ||
          text.includes("Consent Decree") ||
          text.includes("v.") ||
          text.includes("United States")
      )) {
        const absoluteUrl = href.startsWith("http") 
          ? href 
          : new URL(href, BASE).toString();
        
        items.push({
          source: "doj_ada_cases",
          title: text,
          url: absoluteUrl,
          published_at: null,
          raw: {
            href,
            text,
            method: "pdf_document"
          },
        });
      }
    });

    // Look for links in specific case listing sections
    // Target content under headings like "Cases", "Settlements", etc.
    $("h2, h3, h4").each((i, heading) => {
      const $heading = $(heading);
      const headingText = $heading.text().toLowerCase();
      
      if (headingText.includes("case") || 
          headingText.includes("settlement") || 
          headingText.includes("enforcement") ||
          headingText.includes("agreement")) {
        
        // Find links in the content following this heading
        $heading.nextAll().find("a").each((j, element) => {
          const $link = $(element);
          const href = $link.attr("href");
          const text = $link.text().trim();
          
          if (!href || !text || text.length < 20) return;
          
          // Skip if it looks like navigation
          if (text.toLowerCase().includes("learn more") || 
              text.toLowerCase().includes("read more")) return;
          
          const absoluteUrl = href.startsWith("http") 
            ? href 
            : new URL(href, BASE).toString();
          
          items.push({
            source: "doj_ada_cases",
            title: text,
            url: absoluteUrl,
            published_at: null,
            raw: {
              href,
              text,
              method: "section_content",
              section: headingText
            },
          });
        });
      }
    });

    // Remove duplicates based on URL
    const uniqueItems = items.filter((item, index, self) => 
      index === self.findIndex(t => t.url === item.url)
    );

    console.log(`DOJ ADA Cases: found ${uniqueItems.length} unique case items`);
    return { items: uniqueItems };

  } catch (error) {
    if (error instanceof Error) {
      console.error("DOJ ADA Cases fetch error:", error.message);
      return { 
        items: [], 
        note: `Fetch error: ${error.message}` 
      };
    }
    
    console.error("DOJ ADA Cases unknown error:", error);
    return { 
      items: [], 
      note: "Unknown error occurred" 
    };
  }
}