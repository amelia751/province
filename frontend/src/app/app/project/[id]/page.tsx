import { auth } from '@clerk/nextjs/server';
import { redirect } from 'next/navigation';
import { getOrganizationName } from '@/lib/organization';
import ProjectClient from './project-client';

interface ProjectPageProps {
  params: {
    id: string;
  };
}

export default async function ProjectPage({ params }: ProjectPageProps) {
  const { userId, orgId } = await auth();
  
  if (!userId || !orgId) {
    redirect('/');
  }

  const organizationName = await getOrganizationName();
  
  // TODO: Fetch project data from database using params.id
  // For now, we'll pass the id to the client component
  
  return (
    <ProjectClient 
      projectId={params.id} 
      organizationName={organizationName || undefined}
    />
  );
}

