"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useUser, useClerk, useOrganization, useOrganizationList } from "@clerk/nextjs";
import { cn } from "@/lib/utils";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";
import {
  PanelLeftOpen, 
  PanelLeftClose, 
  Home, 
  FileText, 
  BarChart3, 
  Search, 
  Bell, 
  Settings,
  User,
  LogOut,
  Building2,
  Plus,
  ChevronDown,
  SettingsIcon,
  ArrowRight,
  Loader2
} from "lucide-react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

interface NavItem {
  title: string;
  href: string;
  icon: React.ReactNode;
  disabled?: boolean;
  external?: boolean;
}

interface SidebarNavItemsProps {
  items: NavItem[];
  pathname: string;
  isPinned: boolean;
  isHovered: boolean;
}

// Organization Switcher Component
interface OrgSwitcherProps {
  organization: any;
  organizationList: any[];
  setActive: any;
  openCreateOrganization: () => void;
  openOrganizationProfile: () => void;
  getUserRole: () => string;
  showText: boolean;
  isLoadingOrgSwitch: boolean;
  setIsLoadingOrgSwitch: (loading: boolean) => void;
}

function OrganizationSwitcher({ 
  organization, 
  organizationList, 
  setActive, 
  openCreateOrganization, 
  openOrganizationProfile, 
  getUserRole,
  showText,
  isLoadingOrgSwitch,
  setIsLoadingOrgSwitch
}: OrgSwitcherProps) {
  const itemContent = (
    <div className={cn(
      "flex items-center rounded-md transition-colors text-gray-600 hover:text-black hover:bg-gray-50",
      showText ? "px-3 py-3" : "p-3 justify-center"
    )}>
       <div className="h-4 w-4 flex-shrink-0">
         {organization?.imageUrl ? (
           <img
             src={organization.imageUrl}
             alt={organization.name || "Organization"}
             className="w-4 h-4 rounded object-cover"
           />
         ) : (
           <Building2 className="h-4 w-4" />
         )}
        </div>
       {showText && (
         <>
           <span className="ml-4 text-sm font-medium flex-1 text-left">{organization?.name || "Organizations"}</span>
           <ChevronDown className="h-4 w-4 text-gray-400" />
         </>
       )}
      </div>
  );

  if (!showText) {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <button className="w-full">
                  {itemContent}
                </button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="start" className="w-64">
                <OrganizationDropdownContent 
                  organization={organization}
                  organizationList={organizationList}
                  setActive={setActive}
                  openCreateOrganization={openCreateOrganization}
                  openOrganizationProfile={openOrganizationProfile}
                  getUserRole={getUserRole}
                  isLoadingOrgSwitch={isLoadingOrgSwitch}
                  setIsLoadingOrgSwitch={setIsLoadingOrgSwitch}
                />
              </DropdownMenuContent>
            </DropdownMenu>
          </TooltipTrigger>
          <TooltipContent side="right" className="bg-gray-50 text-black border-gray-200">
            <div className="flex items-center space-x-2">
              <div className="h-4 w-4 flex-shrink-0">
                {organization?.imageUrl ? (
                  <img
                    src={organization.imageUrl}
                    alt={organization.name || "Organization"}
                    className="w-4 h-4 rounded object-cover"
                  />
                ) : (
                  <Building2 className="h-4 w-4" />
                )}
              </div>
              <p>{organization?.name || "Organizations"}</p>
            </div>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button className="w-full">
          {itemContent}
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-64">
        <OrganizationDropdownContent 
          organization={organization}
          organizationList={organizationList}
          setActive={setActive}
          openCreateOrganization={openCreateOrganization}
          openOrganizationProfile={openOrganizationProfile}
          getUserRole={getUserRole}
          isLoadingOrgSwitch={isLoadingOrgSwitch}
          setIsLoadingOrgSwitch={setIsLoadingOrgSwitch}
        />
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

// Organization Dropdown Content Component
function OrganizationDropdownContent({ 
  organization, 
  organizationList, 
  setActive, 
  openCreateOrganization, 
  openOrganizationProfile, 
  getUserRole,
  isLoadingOrgSwitch,
  setIsLoadingOrgSwitch
}: Omit<OrgSwitcherProps, 'showText'>) {
  return (
    <>
      {/* Current Organization */}
      {organization && (
        <>
          <div className="flex items-center space-x-3 p-3">
            <div className="h-8 w-8 rounded bg-gray-100 flex items-center justify-center">
              <Building2 className="h-4 w-4 text-gray-500" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium text-black truncate">{organization.name}</div>
              <div className="text-xs text-gray-500">{getUserRole()}</div>
            </div>
            <div
              onClick={(e) => {
                e.stopPropagation();
                openOrganizationProfile();
              }}
              className="flex items-center text-xs text-gray-600 hover:text-black transition-colors border border-gray-200 rounded px-2 py-1 cursor-pointer hover:bg-gray-50"
            >
              <SettingsIcon className="mr-1 h-3 w-3" />
              Manage
            </div>
          </div>
          <DropdownMenuSeparator />
        </>
      )}

      {/* Other Organizations */}
      {organizationList && organizationList.length > 1 && (
        <>
          {organizationList
            .filter((org: any) => org.organization.id !== organization?.id)
            .map((org: any) => (
              <DropdownMenuItem 
                key={org.organization.id}
                onClick={async () => {
                  setIsLoadingOrgSwitch(true);
                  try {
                    await setActive?.({ organization: org.organization.id });
                    // Add a small delay to ensure the switch is complete
                    await new Promise(resolve => setTimeout(resolve, 500));
                  } catch (error) {
                    console.error('Failed to switch organization:', error);
                  } finally {
                    setIsLoadingOrgSwitch(false);
                  }
                }}
                className="flex items-center space-x-3 p-3 cursor-pointer group"
                disabled={isLoadingOrgSwitch}
              >
                <div className="h-8 w-8 rounded bg-gray-100 flex items-center justify-center">
                  <Building2 className="h-4 w-4 text-gray-500" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-black truncate">{org.organization.name}</div>
                </div>
                {isLoadingOrgSwitch ? (
                  <Loader2 className="h-4 w-4 text-gray-400 animate-spin" />
                ) : (
                  <ArrowRight className="h-4 w-4 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                )}
              </DropdownMenuItem>
            ))}
          <DropdownMenuSeparator />
        </>
      )}

      {/* Create Organization */}
      <DropdownMenuItem 
        onClick={() => openCreateOrganization()}
        className="flex items-center space-x-3 p-3 cursor-pointer"
      >
        <div className="h-8 w-8 rounded bg-gray-50 flex items-center justify-center">
          <Plus className="h-4 w-4 text-gray-400" />
        </div>
        <div className="flex-1">
          <div className="font-medium text-black">Create Organization</div>
        </div>
      </DropdownMenuItem>
    </>
  );
}

export function SidebarNavItems({ items, pathname, isPinned, isHovered }: SidebarNavItemsProps) {
  const showText = isPinned || isHovered;

  return items?.length ? (
    <div className="space-y-3">
      {items.map((item, index) => {
        const isActive = pathname === item.href;
        
        const itemContent = (
          <div className={cn(
            "flex items-center rounded-md transition-colors",
            showText ? "px-3 py-3" : "p-3 justify-center",
            isActive
              ? "bg-black text-white"
              : "text-gray-600 hover:text-black hover:bg-gray-50"
          )}>
            <div className="h-4 w-4 flex-shrink-0">
              {item.icon}
            </div>
            {showText && <span className="ml-4 text-sm font-medium">{item.title}</span>}
          </div>
        );

        if (!showText) {
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
                <TooltipContent side="right">
                  <p>{item.title}</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          );
        }

        return !item.disabled && item.href ? (
          <Link
            key={index}
            href={item.href}
            target={item.external ? "_blank" : ""}
            rel={item.external ? "noreferrer" : ""}
          >
            {itemContent}
          </Link>
        ) : (
          <span
            key={index}
            className="cursor-not-allowed opacity-60"
          >
            {itemContent}
          </span>
        );
      })}
    </div>
  ) : null;
}

interface ResponsiveSidebarProps {
  organizationName?: string | null;
}

const ResponsiveSidebar = ({ organizationName }: ResponsiveSidebarProps) => {
  const pathname = usePathname();
  const { user } = useUser();
  const { organization } = useOrganization();
  const { userMemberships, setActive } = useOrganizationList({
    userMemberships: {
      infinite: true,
    },
  });
  
  const organizationList = userMemberships?.data || [];
  const { openUserProfile, signOut, openCreateOrganization, openOrganizationProfile } = useClerk();
  const [isPinned, setIsPinned] = useState(true);
  const [isHovered, setIsHovered] = useState(false);
  const [isLoadingOrgSwitch, setIsLoadingOrgSwitch] = useState(false);

  useEffect(() => {
    const handleResize = () => {
      if (window.innerWidth < 1024) {
        setIsPinned(false);
      }
    };
    window.addEventListener('resize', handleResize);
    handleResize();
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const workNavItems: NavItem[] = [
    { title: "Dashboard", href: "/app", icon: <Home className="h-4 w-4" /> },
    { title: "Leads", href: "/app/leads", icon: <FileText className="h-4 w-4" /> },
    { title: "Analytics", href: "/app/analytics", icon: <BarChart3 className="h-4 w-4" /> },
    { title: "Sources", href: "/app/sources", icon: <Search className="h-4 w-4" /> },
    { title: "Alerts", href: "/app/alerts", icon: <Bell className="h-4 w-4" /> },
    { title: "Settings", href: "/app/settings", icon: <Settings className="h-4 w-4" /> },
  ];

  // Get user role in current organization
  const getUserRole = () => {
    if (!organization || !userMemberships?.data) return "Member";
    const currentMembership = userMemberships.data.find(
      (membership: any) => membership.organization.id === organization.id
    );
    const role = currentMembership?.role || "Member";
    // Remove "org:" prefix if it exists and capitalize properly
    const cleanRole = role.replace(/^org:/, "");
    return cleanRole.charAt(0).toUpperCase() + cleanRole.slice(1).toLowerCase();
  };

  const handleMouseEnter = () => {
    if (!isPinned) {
      setIsHovered(true);
    }
  };

  const handleMouseLeave = () => {
    if (!isPinned) {
      setIsHovered(false);
    }
  };

  const showText = isPinned || isHovered;

  return (
    <div
      className={cn(
        "fixed inset-y-0 left-0 z-50 flex flex-col bg-white border-r border-gray-100 transition-all duration-300",
        showText ? "w-64" : "w-16"
      )}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <div className="flex flex-col h-full">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-100">
          {showText && (
            <h2 className="text-lg font-semibold text-black">Province</h2>
          )}
          
          <button
            onClick={() => setIsPinned(!isPinned)}
            className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
          >
            {isPinned ? (
              <PanelLeftClose className="h-5 w-5" />
            ) : (
              <PanelLeftOpen className="h-5 w-5" />
            )}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4">
          <div className="space-y-6">
            {/* Organization Switcher - Main Nav Item */}
            <OrganizationSwitcher 
              organization={organization}
              organizationList={organizationList}
              setActive={setActive}
              openCreateOrganization={openCreateOrganization}
              openOrganizationProfile={openOrganizationProfile}
              getUserRole={getUserRole}
              showText={showText}
              isLoadingOrgSwitch={isLoadingOrgSwitch}
              setIsLoadingOrgSwitch={setIsLoadingOrgSwitch}
            />
            
            {/* Work Navigation Items */}
            <SidebarNavItems 
              items={workNavItems} 
              pathname={pathname || ''} 
              isPinned={isPinned} 
              isHovered={isHovered}
            />
          </div>
        </nav>

        {/* User Section */}
        <div className="p-4 border-t border-gray-100">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button className={cn(
                "flex items-center w-full rounded-md px-3 py-3 text-gray-600 hover:text-black hover:bg-gray-50 transition-colors",
                !showText && "justify-center"
              )}>
                <div className="h-5 w-5 rounded-full overflow-hidden flex-shrink-0">
                  {user?.imageUrl ? (
                    <img
                      src={user.imageUrl}
                      alt={user.fullName || user.firstName || "User"}
                      className="w-full h-full object-cover"
                    />
                  ) : (
                    <div className="w-full h-full bg-gray-200 flex items-center justify-center">
                      <User className="h-3 w-3" />
                    </div>
                  )}
                </div>
                {showText && (
                  <div className="ml-4 flex flex-col items-start min-w-0 flex-1 text-left">
                    <span className="text-sm font-medium truncate w-full">
                      {user?.fullName || user?.firstName || "User"}
                    </span>
                    <span className="text-xs text-gray-500 truncate w-full">
                      {user?.primaryEmailAddress?.emailAddress || "user@example.com"}
                    </span>
                  </div>
                )}
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuItem onClick={() => openUserProfile()}>
                <User className="mr-3 h-4 w-4" />
                Account
              </DropdownMenuItem>
              <DropdownMenuItem 
                className="text-red-600"
                onClick={() => signOut()}
              >
                <LogOut className="mr-3 h-4 w-4" />
                Sign out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </div>
  );
};

export default ResponsiveSidebar;
