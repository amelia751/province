'use client';

import { useState } from 'react';
import Sidebar from '@/components/ui/sidebar';

interface DashboardLayoutProps {
  children: React.ReactNode;
  organizationName?: string | null;
}

export default function DashboardLayout({ children, organizationName }: DashboardLayoutProps) {
  const [sidebarWidth, setSidebarWidth] = useState(64);

  const handleSidebarWidthChange = (width: number) => {
    setSidebarWidth(width);
  };

  return (
    <div className="flex flex-1 overflow-hidden">
      {/* Sidebar */}
      <Sidebar 
        organizationName={organizationName} 
        onWidthChange={handleSidebarWidthChange}
      />

      {/* Main content */}
      <div 
        className="flex-1 overflow-auto"
        style={{ marginLeft: `${sidebarWidth}px` }}
      >
        {/* Page content */}
        <main className="p-6">
          {children}
        </main>
      </div>
    </div>
  );
}