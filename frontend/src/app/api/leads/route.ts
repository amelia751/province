import { NextResponse } from "next/server";
import { auth } from '@clerk/nextjs/server';
import { getUserOrganization } from '@/lib/organization';
import { leadDetector } from '@/lib/leads/lead-detector';

export async function GET() {
  try {
    const { userId, orgId } = await auth();
    
    if (!userId || !orgId) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    // Get organization settings
    const organization = await getUserOrganization();
    
    if (!organization) {
      return NextResponse.json(
        { error: 'Organization not found' },
        { status: 404 }
      );
    }

    console.log('Fetching leads for organization:', orgId);
    console.log('Practice areas:', organization.practice_areas);
    console.log('Jurisdictions:', organization.jurisdictions);

    // Detect leads based on organization preferences
    const leads = await leadDetector.detectLeads({
      practiceAreas: organization.practice_areas || [],
      jurisdictions: organization.jurisdictions || [],
      keywordsInclude: organization.keywords_include || [],
      keywordsExclude: organization.keywords_exclude || []
    });

    console.log(`Found ${leads.length} leads for organization`);

    return NextResponse.json({
      success: true,
      leads,
      count: leads.length,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error("Error fetching leads:", error);
    return NextResponse.json(
      { 
        success: false, 
        error: error instanceof Error ? error.message : "Internal server error" 
      },
      { status: 500 }
    );
  }
}