"use client";

import { useUser } from '@clerk/nextjs';
import { usePathname } from 'next/navigation';
import InterfaceLayout from '@/components/interface/interface-layout';

interface ProjectClientProps {
  projectId: string;
  organizationName?: string;
}

export default function ProjectClient({ projectId, organizationName }: ProjectClientProps) {
  const { user } = useUser();
  const pathname = usePathname();

  console.log('Loading project:', projectId);

  return (
    <div className="h-full overflow-hidden">
      <InterfaceLayout 
        organizationName={organizationName} 
        projectId={projectId}
        userId={user?.id}
        debugInfo={{
          timestamp: new Date().toISOString(),
          projectId,
          organizationName,
          user: user ? { id: user.id, exists: true } : null,
          pathname,
          currentUrl: typeof window !== 'undefined' ? window.location.href : 'SSR'
        }}
      />
    </div>
  );
}

