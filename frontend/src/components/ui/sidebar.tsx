"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useClerk } from "@clerk/nextjs";
import { cn } from "@/lib/utils";
import {
  Home,
  FolderDot,
  UserPen,
  HandCoins,
  SlidersHorizontal,
  LogOut
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
    <div className="space-y-1">
      {items.map((item, index) => {
        const isActive = pathname === item.href;

        const itemContent = (
          <div className={cn(
            "flex items-center justify-center p-3 rounded-md transition-all duration-200 group",
            isActive
              ? "bg-black text-white"
              : "text-gray-600 hover:text-black hover:bg-gray-50"
          )}>
            <div className="h-5 w-5 flex-shrink-0 transition-transform duration-200 group-hover:scale-110">
              {item.icon}
            </div>
          </div>
        );

        return (
          <div key={index}>
            <TooltipProvider>
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
          </div>
        );
      })}
    </div>
  ) : null;
}

interface SidebarProps {
  organizationName?: string | null;
  isPersonalAccount?: boolean;
  onWidthChange?: (width: number) => void;
}

const Sidebar = ({ organizationName, isPersonalAccount, onWidthChange }: SidebarProps) => {
  const pathname = usePathname();
  const [sidebarWidth] = useState(64); // Fixed compact width
  const { signOut } = useClerk();

  const workNavItems: NavItem[] = [
    { title: "Home", href: "/app", icon: <Home className="h-5 w-5" /> },
    { title: "Vault", href: "/app/vault", icon: <FolderDot className="h-5 w-5" /> },
    { title: "Profile", href: "/app/profile", icon: <UserPen className="h-5 w-5" /> },
    { title: "Credits", href: "/app/credits", icon: <HandCoins className="h-5 w-5" /> },
    { title: "Preferences", href: "/app/preferences", icon: <SlidersHorizontal className="h-5 w-5" /> },
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
      <nav className="flex-1 px-2 py-3">
        <div className="space-y-1">
          <SidebarNavItems
            items={workNavItems}
            pathname={pathname || ''}
          />
        </div>
      </nav>

      {/* Sign Out Button at Bottom */}
      <div className="px-2 pb-3">
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                onClick={() => signOut()}
                className="flex items-center justify-center p-3 rounded-md transition-all duration-200 w-full text-gray-600 hover:text-black hover:bg-gray-50 group"
              >
                <LogOut className="h-5 w-5 transition-transform duration-200 group-hover:scale-110" />
              </button>
            </TooltipTrigger>
            <TooltipContent side="right" className="bg-gray-900 text-white border-gray-700">
              <p>Sign out</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>
    </div>
  );
};

export default Sidebar;