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
  Building2,
  Plus,
  ChevronDown,
  SettingsIcon,
  ArrowRight,
  Loader2,
  User,
  LogOut
} from "lucide-react";

interface HeaderProps {
  className?: string;
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
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button className="flex items-center space-x-2 px-2 py-1 rounded-md hover:bg-gray-50 transition-colors">
          <div className="h-5 w-5 flex-shrink-0">
            {organization?.imageUrl ? (
              <img
                src={organization.imageUrl}
                alt={organization.name || "Organization"}
                className="w-5 h-5 rounded object-cover"
              />
            ) : (
              <Building2 className="h-5 w-5 text-gray-600" />
            )}
          </div>
          <div className="flex flex-col items-start min-w-0">
            <span className="text-sm font-medium text-gray-900 truncate">
              {organization?.name || "Organizations"}
            </span>
          </div>
          <ChevronDown className="h-3 w-3 text-gray-400" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-64">
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
        onClick={() => onCreateOrganization()}
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

const Header: React.FC<HeaderProps> = ({ className }) => {
  const { user } = useUser();
  const { organization } = useOrganization();
  const { userMemberships, setActive } = useOrganizationList({
    userMemberships: {
      infinite: true,
    },
  });
  
  const organizationList = userMemberships?.data || [];
  const { openUserProfile, signOut, openCreateOrganization, openOrganizationProfile } = useClerk();
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

      {/* Right side - User */}
      <div className="flex items-center">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button className="flex items-center space-x-2 px-2 py-1 rounded-md hover:bg-gray-50 transition-colors">
              <div className="h-5 w-5 rounded-full overflow-hidden flex-shrink-0">
                {user?.imageUrl ? (
                  <img
                    src={user.imageUrl}
                    alt={user.fullName || user.firstName || "User"}
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full bg-gray-200 flex items-center justify-center">
                    <User className="h-3 w-3 text-gray-500" />
                  </div>
                )}
              </div>
              <span className="text-sm font-medium text-gray-900 truncate">
                {user?.fullName || user?.firstName || "User"}
              </span>
              <ChevronDown className="h-3 w-3 text-gray-400" />
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
    </header>
  );
};

export default Header;