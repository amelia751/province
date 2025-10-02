"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  Home,
  FileText,
  BarChart3,
  Search,
  Bell,
  Settings
} from "lucide-react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

interface NavItem {
  title: string;
  href: string;
  icon: React.ReactNode;
  disabled?: boolean;
  external?: boolean;
}

export function SidebarNavItems({ items, pathname }: { items: NavItem[]; pathname: string }) {
  return items?.length ? (
    <div className="space-y-2">
      {items.map((item, index) => {
        const isActive = pathname === item.href;

        const itemContent = (
          <div className={cn(
            "flex items-center justify-center p-3 rounded-md transition-colors mx-1",
            isActive
              ? "bg-black text-white"
              : "text-gray-600 hover:text-black hover:bg-gray-50"
          )}>
            <div className="h-5 w-5 flex-shrink-0">
              {item.icon}
            </div>
          </div>
        );

        return (
          <TooltipProvider key={index}>
            <Tooltip>
              <TooltipTrigger asChild>
                {!item.disabled && item.href ? (
                  <Link
                    href={item.href}
                    target={item.external ? "_blank" : ""}
                    rel={item.external ? "noreferrer" : ""}
                  >
                    {itemContent}
                  </Link>
                ) : (
                  <span className="cursor-not-allowed opacity-60">
                    {itemContent}
                  </span>
                )}
              </TooltipTrigger>
              <TooltipContent side="right" className="bg-gray-900 text-white border-gray-700">
                <p>{item.title}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        );
      })}
    </div>
  ) : null;
}

interface SidebarProps {
  organizationName?: string | null;
  onWidthChange?: (width: number) => void;
}

const Sidebar = ({ onWidthChange }: SidebarProps) => {
  const pathname = usePathname();
  const [sidebarWidth] = useState(64); // Fixed compact width

  const workNavItems: NavItem[] = [
    { title: "Dashboard", href: "/app", icon: <Home className="h-5 w-5" /> },
    { title: "Leads", href: "/app/leads", icon: <FileText className="h-5 w-5" /> },
    { title: "Analytics", href: "/app/analytics", icon: <BarChart3 className="h-5 w-5" /> },
    { title: "Sources", href: "/app/sources", icon: <Search className="h-5 w-5" /> },
    { title: "Alerts", href: "/app/alerts", icon: <Bell className="h-5 w-5" /> },
    { title: "Settings", href: "/app/settings", icon: <Settings className="h-5 w-5" /> },
  ];

  // Notify parent component of width changes
  useEffect(() => {
    onWidthChange?.(sidebarWidth);
  }, [sidebarWidth, onWidthChange]);

  return (
    <div
      className="flex-shrink-0 flex flex-col bg-white border-r border-gray-100"
      style={{ width: `${sidebarWidth}px` }}
    >
      {/* Navigation */}
      <nav className="flex-1 p-3">
        <div className="space-y-1">
          <SidebarNavItems
            items={workNavItems}
            pathname={pathname || ''}
          />
        </div>
      </nav>
    </div>
  );
};

export default Sidebar;