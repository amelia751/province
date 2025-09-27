export interface DOJOPAItem {
  source: "doj_opa_rss";
  title: string;
  url?: string;
  published_at?: string | null;
  raw: any;
}

export interface DOJOPAResult {
  items: DOJOPAItem[];
  note?: string;
}

const OPA_RSS = "https://www.justice.gov/rss/rss.opa.hp.xml";

// ADA-related keywords to filter press releases
const ADA_KEYWORDS = [
  /americans with disabilities act/i,
  /\bADA\b/,
  /title\s*(ii|iii)/i,
  /olmstead/i,
  /accessibility/i,
  /disability.*rights/i,
  /civil.*rights.*division/i,
  /reasonable.*accommodation/i,
  /web.*accessibility/i,
  /physical.*accessibility/i
];

export async function fetchDojOpaRssSince({ since }: { since: Date }): Promise<DOJOPAResult> {
  try {
    console.log(`DOJ OPA RSS: Fetching from ${OPA_RSS}`);
    
    // Dynamic import for rss-parser to work with Next.js
    const Parser = (await import("rss-parser")).default;
    const parser = new Parser();
    
    const feed = await parser.parseURL(OPA_RSS);
    
    if (!feed.items || feed.items.length === 0) {
      return { 
        items: [], 
        note: "No items found in RSS feed" 
      };
    }

    const filteredItems = feed.items
      .filter(item => {
        // Date filter
        const dateOk = item.pubDate ? new Date(item.pubDate) >= since : true;
        
        // Keyword filter - check title and content
        const text = `${item.title || ""} ${item.contentSnippet || ""} ${item.content || ""}`.toLowerCase();
        const hasADAKeyword = ADA_KEYWORDS.some(keyword => keyword.test(text));
        
        return dateOk && hasADAKeyword;
      })
      .map(item => ({
        source: "doj_opa_rss" as const,
        title: item.title || "DOJ Press Release",
        url: item.link || undefined,
        published_at: item.pubDate || null,
        raw: {
          guid: item.guid,
          content: item.content,
          contentSnippet: item.contentSnippet,
          categories: item.categories,
          pubDate: item.pubDate,
        },
      }));

    console.log(`DOJ OPA RSS: found ${filteredItems.length} ADA-related items since ${since.toISOString()}`);
    return { items: filteredItems };

  } catch (error) {
    if (error instanceof Error) {
      console.error("DOJ OPA RSS fetch error:", error.message);
      return { 
        items: [], 
        note: `RSS fetch error: ${error.message}` 
      };
    }
    
    console.error("DOJ OPA RSS unknown error:", error);
    return { 
      items: [], 
      note: "Unknown RSS error occurred" 
    };
  }
}