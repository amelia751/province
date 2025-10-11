"use client";

import React, { useState } from "react";
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
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import {
  Building2,
  Plus,
  ChevronDown,
  SettingsIcon,
  ArrowRight,
  Loader2,
  User,
  PanelLeft,
  PanelRight
} from "lucide-react";

interface HeaderProps {
  className?: string;
  onToggleExplorer?: () => void;
  onToggleChat?: () => void;
}

// Organization Switcher Component
interface OrgSwitcherProps {
  organization: any;
  organizationList: any[];
  setActive: any;
  onCreateOrganization: () => void;
  openOrganizationProfile: () => void;
  getUserRole: () => string;
  isLoadingOrgSwitch: boolean;
  setIsLoadingOrgSwitch: (loading: boolean) => void;
}

function OrganizationSwitcher({
  organization,
  organizationList,
  setActive,
  onCreateOrganization,
  openOrganizationProfile,
  getUserRole,
  isLoadingOrgSwitch,
  setIsLoadingOrgSwitch
}: OrgSwitcherProps) {
  const { user } = useUser();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button className="flex items-center space-x-2 px-2 py-1 rounded-md hover:bg-gray-50 transition-colors">
          <div className="h-5 w-5 flex-shrink-0 rounded overflow-hidden">
            {organization?.imageUrl ? (
              <img
                src={organization.imageUrl}
                alt={organization.name || "Organization"}
                className="w-full h-full object-cover"
              />
            ) : organization ? (
              <div className="w-full h-full bg-gray-100 flex items-center justify-center">
                <Building2 className="h-3 w-3 text-gray-600" />
              </div>
            ) : user?.imageUrl ? (
              <img
                src={user.imageUrl}
                alt={user.fullName || user.firstName || "User"}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full bg-gray-100 flex items-center justify-center">
                <User className="h-3 w-3 text-gray-600" />
              </div>
            )}
          </div>
          <div className="flex flex-col items-start min-w-0">
            <span className="text-sm font-medium text-gray-900 truncate">
              {organization?.name || user?.fullName || user?.firstName || "Personal Account"}
            </span>
          </div>
          <ChevronDown className="h-3 w-3 text-gray-400" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-56">
        <OrganizationDropdownContent 
          organization={organization}
          organizationList={organizationList}
          setActive={setActive}
          onCreateOrganization={onCreateOrganization}
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
  onCreateOrganization,
  openOrganizationProfile,
  getUserRole,
  isLoadingOrgSwitch,
  setIsLoadingOrgSwitch
}: Omit<OrgSwitcherProps, 'showText'>) {
  const { openUserProfile } = useClerk();
  const { user } = useUser();

  return (
    <>
      {/* Current Organization or Personal Account */}
      <div className="flex items-center space-x-2 p-2">
        <div className="h-6 w-6 rounded overflow-hidden bg-gray-100 flex items-center justify-center flex-shrink-0">
          {organization ? (
            organization.imageUrl ? (
              <img
                src={organization.imageUrl}
                alt={organization.name}
                className="w-full h-full object-cover"
              />
            ) : (
              <Building2 className="h-3 w-3 text-gray-500" />
            )
          ) : user?.imageUrl ? (
            <img
              src={user.imageUrl}
              alt={user.fullName || user.firstName || "User"}
              className="w-full h-full object-cover"
            />
          ) : (
            <User className="h-3 w-3 text-gray-500" />
          )}
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-xs font-medium text-black truncate">
            {organization?.name || user?.fullName || user?.firstName || "Personal Account"}
          </div>
          {organization && (
            <div className="text-[10px] text-gray-500">{getUserRole()}</div>
          )}
        </div>
        <div
          onClick={(e) => {
            e.stopPropagation();
            if (organization) {
              openOrganizationProfile();
            } else {
              openUserProfile();
            }
          }}
          className="flex items-center text-[10px] text-gray-600 hover:text-black transition-colors border border-gray-200 rounded px-1.5 py-0.5 cursor-pointer hover:bg-gray-50"
        >
          <SettingsIcon className="mr-0.5 h-2.5 w-2.5" />
          Manage
        </div>
      </div>
      {organizationList && organizationList.length > 0 && (
        <DropdownMenuSeparator />
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
                    await new Promise(resolve => setTimeout(resolve, 500));
                  } catch (error) {
                    console.error('Failed to switch organization:', error);
                  } finally {
                    setIsLoadingOrgSwitch(false);
                  }
                }}
                className="flex items-center space-x-2 p-2 cursor-pointer group"
                disabled={isLoadingOrgSwitch}
              >
                <div className="h-6 w-6 rounded bg-gray-100 flex items-center justify-center">
                  <Building2 className="h-3 w-3 text-gray-500" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-xs font-medium text-black truncate">{org.organization.name}</div>
                </div>
                {isLoadingOrgSwitch ? (
                  <Loader2 className="h-3 w-3 text-gray-400 animate-spin" />
                ) : (
                  <ArrowRight className="h-3 w-3 text-gray-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                )}
              </DropdownMenuItem>
            ))}
          <DropdownMenuSeparator />
        </>
      )}

      {/* Create Organization */}
      <DropdownMenuItem
        onClick={() => onCreateOrganization()}
        className="flex items-center space-x-2 p-2 cursor-pointer"
      >
        <div className="h-6 w-6 rounded bg-gray-50 flex items-center justify-center">
          <Plus className="h-3 w-3 text-gray-400" />
        </div>
        <div className="flex-1">
          <div className="text-xs font-medium text-black">Create Organization</div>
        </div>
      </DropdownMenuItem>
    </>
  );
}

const Header: React.FC<HeaderProps> = ({ className, onToggleExplorer, onToggleChat }) => {
  const { organization } = useOrganization();
  const { userMemberships, setActive } = useOrganizationList({
    userMemberships: {
      infinite: true,
    },
  });

  const organizationList = userMemberships?.data || [];
  const { openCreateOrganization, openOrganizationProfile } = useClerk();
  const [isLoadingOrgSwitch, setIsLoadingOrgSwitch] = useState(false);

  // Get user role in current organization
  const getUserRole = () => {
    if (!organization || !userMemberships?.data) return "Member";
    const currentMembership = userMemberships.data.find(
      (membership: any) => membership.organization.id === organization.id
    );
    const role = currentMembership?.role || "Member";
    const cleanRole = role.replace(/^org:/, "");
    return cleanRole.charAt(0).toUpperCase() + cleanRole.slice(1).toLowerCase();
  };

  return (
    <header className={cn(
      "flex items-center justify-between px-4 py-2 bg-white border-b border-gray-100",
      className
    )}>
      {/* Left side - Organization */}
      <div className="flex items-center">
        <OrganizationSwitcher
          organization={organization}
          organizationList={organizationList}
          setActive={setActive}
          onCreateOrganization={openCreateOrganization}
          openOrganizationProfile={openOrganizationProfile}
          getUserRole={getUserRole}
          isLoadingOrgSwitch={isLoadingOrgSwitch}
          setIsLoadingOrgSwitch={setIsLoadingOrgSwitch}
        />
      </div>

      {/* Right side - Panel Toggles */}
      <div className="flex items-center space-x-0.5">
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                onClick={onToggleExplorer}
                className="p-1.5 rounded-md text-gray-600 hover:text-black hover:bg-gray-50 transition-colors"
              >
                <PanelLeft className="h-4 w-4" />
              </button>
            </TooltipTrigger>
            <TooltipContent>
              <p>Toggle Explorer Panel</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>

        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <button
                onClick={onToggleChat}
                className="p-1.5 rounded-md text-gray-600 hover:text-black hover:bg-gray-50 transition-colors"
              >
                <PanelRight className="h-4 w-4" />
              </button>
            </TooltipTrigger>
            <TooltipContent>
              <p>Toggle Assistant Chat</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>
    </header>
  );
};

export default Header;