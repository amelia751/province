import { NextResponse } from "next/server";
import { fetchCourtListener } from "@/lib/ingest/courtlistener";
import { fetchOpenFDA } from "@/lib/ingest/openfda";
import { fetchDOJADA } from "@/lib/ingest/doj";

export async function POST() {
  try {
    const since = new Date(Date.now() - 24 * 3600 * 1000); // last 24h
    
    const [cl, fda, doj] = await Promise.allSettled([
      fetchCourtListener({ since }),
      fetchOpenFDA({ since }),
      fetchDOJADA({ since }),
    ]);

    return NextResponse.json({ 
      success: true,
      results: { cl, fda, doj },
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    console.error("Ingestion error:", error);
    return NextResponse.json(
      { success: false, error: "Internal server error" },
      { status: 500 }
    );
  }
}