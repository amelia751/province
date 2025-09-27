import { NextResponse } from "next/server";
import { textProcessor } from "@/lib/processing/text-processor";
import { fetchCourtListener } from "@/lib/ingest/courtlistener";
import { fetchOpenFDA } from "@/lib/ingest/openfda";
import { fetchDOJADA } from "@/lib/ingest/doj";

export async function POST() {
  try {
    console.log('Starting text processing pipeline...');
    
    const since = new Date(Date.now() - 24 * 3600 * 1000); // last 24h
    
    // Fetch data from all sources
    console.log('Fetching data from sources...');
    const [clResult, fdaResult, dojResult] = await Promise.allSettled([
      fetchCourtListener({ since }),
      fetchOpenFDA({ since }),
      fetchDOJADA({ since }),
    ]);

    // Collect all items
    const allItems = [];
    
    if (clResult.status === 'fulfilled') {
      allItems.push(...clResult.value.items);
      console.log(`CourtListener: ${clResult.value.items.length} items`);
    } else {
      console.error('CourtListener failed:', clResult.reason);
    }

    if (fdaResult.status === 'fulfilled') {
      allItems.push(...fdaResult.value.items);
      console.log(`OpenFDA: ${fdaResult.value.items.length} items`);
    } else {
      console.error('OpenFDA failed:', fdaResult.reason);
    }

    if (dojResult.status === 'fulfilled') {
      allItems.push(...dojResult.value.items);
      console.log(`DOJ: ${dojResult.value.items.length} items`);
    } else {
      console.error('DOJ failed:', dojResult.reason);
    }

    console.log(`Total items to process: ${allItems.length}`);

    if (allItems.length === 0) {
      return NextResponse.json({
        success: true,
        message: 'No new items to process',
        processed: 0,
        errors: []
      });
    }

    // Process all items
    console.log('Processing items...');
    const result = await textProcessor.processItems(allItems);

    console.log(`Processing complete: ${result.processed} processed, ${result.errors.length} errors`);

    return NextResponse.json({
      success: result.success,
      message: `Processed ${result.processed} items`,
      processed: result.processed,
      total: allItems.length,
      errors: result.errors,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error("Text processing error:", error);
    return NextResponse.json(
      { 
        success: false, 
        error: error instanceof Error ? error.message : "Internal server error",
        timestamp: new Date().toISOString()
      },
      { status: 500 }
    );
  }
}