'use client';

import ResponsiveSidebar from '@/components/ui/sidebar';

interface DashboardLayoutProps {
  children: React.ReactNode;
  organizationName?: string | null;
}

export default function DashboardLayout({ children, organizationName }: DashboardLayoutProps) {
  return (
    <div className="min-h-screen bg-white">
      {/* Responsive Sidebar */}
      <ResponsiveSidebar organizationName={organizationName} />

      {/* Main content */}
      <div className="ml-16 transition-all duration-300">
        {/* Page content */}
        <main className="p-6">
          {children}
        </main>
      </div>
    </div>
  );
}