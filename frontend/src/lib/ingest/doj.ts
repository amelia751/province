import { fetchAdaGovCases } from "./doj-ada-cases";
import { fetchDojOpaRssSince } from "./doj-opa-rss";

export interface DOJADAItem {
  source: "doj_ada" | "doj_ada_cases" | "doj_opa_rss";
  title: string;
  url?: string;
  published_at?: string | null;
  raw: any;
}

export interface DOJADAResult {
  items: DOJADAItem[];
  note?: string;
  sources: {
    ada_cases: { count: number; note?: string };
    opa_rss: { count: number; note?: string };
  };
}

export async function fetchDOJADA({ since }: { since: Date }): Promise<DOJADAResult> {
  try {
    console.log(`DOJ ADA: Starting parallel fetch from multiple sources`);

    // Fetch from both sources in parallel
    const [adaCasesResult, opaRssResult] = await Promise.allSettled([
      fetchAdaGovCases({ since }),
      fetchDojOpaRssSince({ since }),
    ]);

    const allItems: DOJADAItem[] = [];
    const sources = {
      ada_cases: { count: 0, note: undefined as string | undefined },
      opa_rss: { count: 0, note: undefined as string | undefined },
    };

    // Process ADA.gov cases
    if (adaCasesResult.status === "fulfilled") {
      const caseItems = adaCasesResult.value.items.map(item => ({
        ...item,
        source: "doj_ada" as const,
      }));
      allItems.push(...caseItems);
      sources.ada_cases.count = caseItems.length;
      sources.ada_cases.note = adaCasesResult.value.note;
    } else {
      sources.ada_cases.note = `Error: ${adaCasesResult.reason}`;
    }

    // Process DOJ OPA RSS
    if (opaRssResult.status === "fulfilled") {
      allItems.push(...opaRssResult.value.items);
      sources.opa_rss.count = opaRssResult.value.items.length;
      sources.opa_rss.note = opaRssResult.value.note;
    } else {
      sources.opa_rss.note = `Error: ${opaRssResult.reason}`;
    }

    // Remove duplicates based on URL
    const uniqueItems = allItems.filter((item, index, self) => 
      index === self.findIndex(t => t.url === item.url)
    );

    console.log(`DOJ ADA: Combined ${uniqueItems.length} unique items from ${allItems.length} total`);
    return { 
      items: uniqueItems,
      sources,
      note: allItems.length === 0 ? "No items found from any DOJ source" : undefined
    };

  } catch (error) {
    if (error instanceof Error) {
      console.error("DOJ ADA combined fetch error:", error.message);
      return { 
        items: [], 
        sources: { ada_cases: { count: 0 }, opa_rss: { count: 0 } },
        note: `Combined fetch error: ${error.message}` 
      };
    }
    
    console.error("DOJ ADA unknown error:", error);
    return { 
      items: [], 
      sources: { ada_cases: { count: 0 }, opa_rss: { count: 0 } },
      note: "Unknown error occurred" 
    };
  }
}