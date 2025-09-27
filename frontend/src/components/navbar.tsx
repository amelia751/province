"use client";

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import {
  NavigationMenu,
  NavigationMenuContent,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  NavigationMenuTrigger,
  navigationMenuTriggerStyle,
} from "@/components/ui/navigation-menu";
import { Scale, Shield, BarChart3, FileText, Users } from 'lucide-react';
import { cn } from "@/lib/utils";

const ListItem = ({ className, title, children, ...props }: any) => {
  return (
    <li>
      <NavigationMenuLink asChild>
        <a
          className={cn(
            "block select-none space-y-1 rounded-md p-3 leading-none no-underline outline-none transition-colors hover:bg-white/10 hover:text-white focus:bg-white/10 focus:text-white",
            className
          )}
          {...props}
        >
          <div className="text-sm font-medium leading-none">{title}</div>
          <p className="line-clamp-2 text-sm leading-snug text-white/60">
            {children}
          </p>
        </a>
      </NavigationMenuLink>
    </li>
  )
}

export function Navbar() {
  return (
    <nav className="relative z-50 border-b border-white/10 bg-black/50 backdrop-blur-sm">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <div className="flex items-center">
            <Link href="/" className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <Scale className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-white">Province</span>
            </Link>
          </div>

          {/* Navigation Menu */}
          <NavigationMenu className="hidden md:flex">
            <NavigationMenuList>
              <NavigationMenuItem>
                <NavigationMenuTrigger className="bg-transparent text-white/80 hover:text-white hover:bg-white/10 focus:bg-white/10 focus:text-white data-[active]:bg-white/10 data-[state=open]:bg-white/10">
                  Platform
                </NavigationMenuTrigger>
                <NavigationMenuContent>
                  <ul className="grid gap-3 p-6 md:w-[400px] lg:w-[500px] lg:grid-cols-[.75fr_1fr]">
                    <li className="row-span-3">
                      <NavigationMenuLink asChild>
                        <a
                          className="flex h-full w-full select-none flex-col justify-end rounded-md bg-gradient-to-b from-blue-500/20 to-purple-600/20 p-6 no-underline outline-none focus:shadow-md"
                          href="/"
                        >
                          <Scale className="h-6 w-6 text-white" />
                          <div className="mb-2 mt-4 text-lg font-medium text-white">
                            Province AI
                          </div>
                          <p className="text-sm leading-tight text-white/60">
                            Professional-grade AI for legal document processing and analysis.
                          </p>
                        </a>
                      </NavigationMenuLink>
                    </li>
                    <ListItem href="/docs" title="Document Analysis">
                      <div className="flex items-center space-x-2 mb-2">
                        <FileText className="w-4 h-4 text-blue-400" />
                        <span>AI-powered legal document processing</span>
                      </div>
                    </ListItem>
                    <ListItem href="/docs/installation" title="Analytics">
                      <div className="flex items-center space-x-2 mb-2">
                        <BarChart3 className="w-4 h-4 text-blue-400" />
                        <span>Comprehensive case insights and reporting</span>
                      </div>
                    </ListItem>
                    <ListItem href="/docs/primitives/typography" title="Lead Detection">
                      <div className="flex items-center space-x-2 mb-2">
                        <Shield className="w-4 h-4 text-blue-400" />
                        <span>Automated lead identification from legal sources</span>
                      </div>
                    </ListItem>
                  </ul>
                </NavigationMenuContent>
              </NavigationMenuItem>
              <NavigationMenuItem>
                <NavigationMenuTrigger className="bg-transparent text-white/80 hover:text-white hover:bg-white/10 focus:bg-white/10 focus:text-white data-[active]:bg-white/10 data-[state=open]:bg-white/10">
                  Solutions
                </NavigationMenuTrigger>
                <NavigationMenuContent>
                  <ul className="grid w-[400px] gap-3 p-4 md:w-[500px] md:grid-cols-2 lg:w-[600px]">
                    <ListItem title="Law Firms">
                      <div className="flex items-center space-x-2 mb-2">
                        <Users className="w-4 h-4 text-blue-400" />
                        <span>Streamline case management and legal research</span>
                      </div>
                    </ListItem>
                    <ListItem title="Corporate Legal">
                      <div className="flex items-center space-x-2 mb-2">
                        <Shield className="w-4 h-4 text-blue-400" />
                        <span>Enterprise compliance and risk management</span>
                      </div>
                    </ListItem>
                    <ListItem title="Government">
                      <div className="flex items-center space-x-2 mb-2">
                        <Scale className="w-4 h-4 text-blue-400" />
                        <span>Public sector legal document processing</span>
                      </div>
                    </ListItem>
                    <ListItem title="Professional Services">
                      <div className="flex items-center space-x-2 mb-2">
                        <FileText className="w-4 h-4 text-blue-400" />
                        <span>Consulting and advisory service support</span>
                      </div>
                    </ListItem>
                  </ul>
                </NavigationMenuContent>
              </NavigationMenuItem>
              <NavigationMenuItem>
                <Link href="/customers" legacyBehavior passHref>
                  <NavigationMenuLink className={cn(navigationMenuTriggerStyle(), "bg-transparent text-white/80 hover:text-white hover:bg-white/10 focus:bg-white/10 focus:text-white")}>
                    Customers
                  </NavigationMenuLink>
                </Link>
              </NavigationMenuItem>
              <NavigationMenuItem>
                <Link href="/security" legacyBehavior passHref>
                  <NavigationMenuLink className={cn(navigationMenuTriggerStyle(), "bg-transparent text-white/80 hover:text-white hover:bg-white/10 focus:bg-white/10 focus:text-white")}>
                    Security
                  </NavigationMenuLink>
                </Link>
              </NavigationMenuItem>
            </NavigationMenuList>
          </NavigationMenu>

          {/* Sign In Button */}
          <div className="flex items-center space-x-4">
            <Link href="/auth">
              <Button 
                variant="outline" 
                className="border-white/20 bg-transparent text-white hover:bg-white/10 hover:text-white hover:border-white/40 focus:bg-white/10 focus:text-white"
              >
                Sign In
              </Button>
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
}
