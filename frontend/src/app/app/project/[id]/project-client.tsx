"use client";

import InterfaceLayout from '@/components/interface/interface-layout';

interface ProjectClientProps {
  projectId: string;
  organizationName?: string;
}

export default function ProjectClient({ projectId, organizationName }: ProjectClientProps) {
  // TODO: Fetch project data from API using projectId
  // TODO: Pass project data to InterfaceLayout or its children

  console.log('Loading project:', projectId);

  return (
    <div className="h-full overflow-hidden">
      <InterfaceLayout organizationName={organizationName} />
    </div>
  );
}

