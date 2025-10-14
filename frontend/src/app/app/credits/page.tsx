"use client";

import React, { useState } from "react";
import { HandCoins, Plus, Check, Info, Calculator, TrendingUp, DollarSign } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";

interface Credit {
  id: string;
  name: string;
  description: string;
  maxAmount: number;
  estimatedAmount: number;
  qualified: boolean;
  category: "tax-credit" | "deduction";
  requirements: string[];
}

const mockCredits: Credit[] = [
  {
    id: "1",
    name: "Child Tax Credit",
    description: "Credit for qualifying children under 17",
    maxAmount: 2000,
    estimatedAmount: 2000,
    qualified: true,
    category: "tax-credit",
    requirements: ["Child must be under 17", "Child must be claimed as dependent", "Income limits apply"]
  },
  {
    id: "2",
    name: "Earned Income Tax Credit",
    description: "Credit for low to moderate income workers",
    maxAmount: 6935,
    estimatedAmount: 4500,
    qualified: true,
    category: "tax-credit",
    requirements: ["Must have earned income", "Meet income limits", "Must file tax return"]
  },
  {
    id: "3",
    name: "Standard Deduction",
    description: "Standard deduction for single filers",
    maxAmount: 13850,
    estimatedAmount: 13850,
    qualified: true,
    category: "deduction",
    requirements: ["Cannot itemize deductions", "Filing status: Single"]
  },
  {
    id: "4",
    name: "Student Loan Interest",
    description: "Deduction for student loan interest paid",
    maxAmount: 2500,
    estimatedAmount: 1200,
    qualified: true,
    category: "deduction",
    requirements: ["Paid interest on qualified student loan", "Income limits apply"]
  },
  {
    id: "5",
    name: "Retirement Savings Credit",
    description: "Credit for contributions to retirement accounts",
    maxAmount: 1000,
    estimatedAmount: 0,
    qualified: false,
    category: "tax-credit",
    requirements: ["Contribute to IRA or 401(k)", "Meet income requirements", "Age 18 or older"]
  },
];

export default function CreditsPage() {
  const [selectedTab, setSelectedTab] = useState("all");

  const filteredCredits = mockCredits.filter(credit => {
    if (selectedTab === "all") return true;
    if (selectedTab === "qualified") return credit.qualified;
    if (selectedTab === "available") return !credit.qualified;
    return credit.category === selectedTab;
  });

  const totalCredits = mockCredits
    .filter(c => c.category === "tax-credit" && c.qualified)
    .reduce((sum, c) => sum + c.estimatedAmount, 0);

  const totalDeductions = mockCredits
    .filter(c => c.category === "deduction" && c.qualified)
    .reduce((sum, c) => sum + c.estimatedAmount, 0);

  const qualifiedCount = mockCredits.filter(c => c.qualified).length;
  const availableCount = mockCredits.filter(c => !c.qualified).length;

  return (
    <div className="flex-1 overflow-auto">
      <div className="container max-w-7xl mx-auto p-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <HandCoins className="h-8 w-8" />
            <h1 className="text-3xl font-bold">Credits & Deductions</h1>
          </div>
          <p className="text-muted-foreground">Maximize your tax savings with available credits and deductions</p>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <Card>
            <CardHeader className="pb-3">
              <CardDescription className="flex items-center gap-2">
                <DollarSign className="h-4 w-4" />
                Total Tax Credits
              </CardDescription>
              <CardTitle className="text-3xl">${totalCredits.toLocaleString()}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-sm text-muted-foreground">
                Direct reduction in tax owed
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardDescription className="flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                Total Deductions
              </CardDescription>
              <CardTitle className="text-3xl">${totalDeductions.toLocaleString()}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-sm text-muted-foreground">
                Reduces taxable income
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardDescription className="flex items-center gap-2">
                <Calculator className="h-4 w-4" />
                Qualified Benefits
              </CardDescription>
              <CardTitle className="text-3xl">{qualifiedCount}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-sm text-muted-foreground">
                {availableCount} more available to explore
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Estimated Tax Impact */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Estimated Tax Impact</CardTitle>
            <CardDescription>Based on your current credits and deductions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span>Estimated Tax Liability Before Credits</span>
                  <span className="font-medium">$12,500</span>
                </div>
                <Progress value={100} className="h-2 bg-red-100" />
              </div>
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span>After Credits & Deductions</span>
                  <span className="font-medium text-green-600">$5,650</span>
                </div>
                <Progress value={45} className="h-2" />
              </div>
              <Separator />
              <div className="flex justify-between items-center">
                <span className="text-lg font-semibold">Estimated Savings</span>
                <span className="text-2xl font-bold text-green-600">$6,850</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Credits & Deductions List */}
        <Card>
          <CardHeader>
            <CardTitle>Available Benefits</CardTitle>
            <CardDescription>Review and manage your tax credits and deductions</CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs value={selectedTab} onValueChange={setSelectedTab}>
              <TabsList className="grid w-full grid-cols-5">
                <TabsTrigger value="all">All</TabsTrigger>
                <TabsTrigger value="qualified">Qualified</TabsTrigger>
                <TabsTrigger value="available">Available</TabsTrigger>
                <TabsTrigger value="tax-credit">Credits</TabsTrigger>
                <TabsTrigger value="deduction">Deductions</TabsTrigger>
              </TabsList>

              <TabsContent value={selectedTab} className="mt-6">
                <div className="space-y-4">
                  {filteredCredits.map((credit) => (
                    <div
                      key={credit.id}
                      className="flex items-start justify-between p-4 rounded-lg border hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="font-semibold">{credit.name}</h3>
                          {credit.qualified ? (
                            <Badge className="bg-green-100 text-green-800 border-green-200">
                              <Check className="h-3 w-3 mr-1" />
                              Qualified
                            </Badge>
                          ) : (
                            <Badge variant="outline" className="text-gray-600">
                              Available
                            </Badge>
                          )}
                          <Badge variant="outline" className="text-xs">
                            {credit.category === "tax-credit" ? "Tax Credit" : "Deduction"}
                          </Badge>
                        </div>
                        <p className="text-sm text-muted-foreground mb-3">{credit.description}</p>

                        {credit.qualified && (
                          <div className="flex items-center gap-4 text-sm">
                            <div>
                              <span className="text-muted-foreground">Estimated Amount: </span>
                              <span className="font-semibold">${credit.estimatedAmount.toLocaleString()}</span>
                            </div>
                            <div>
                              <span className="text-muted-foreground">Max Amount: </span>
                              <span className="font-medium">${credit.maxAmount.toLocaleString()}</span>
                            </div>
                          </div>
                        )}

                        {!credit.qualified && (
                          <div className="text-sm text-muted-foreground">
                            <span className="font-medium">Potential: </span>
                            Up to ${credit.maxAmount.toLocaleString()}
                          </div>
                        )}
                      </div>

                      <Dialog>
                        <DialogTrigger asChild>
                          <Button variant="outline" size="sm">
                            <Info className="h-4 w-4 mr-2" />
                            Details
                          </Button>
                        </DialogTrigger>
                        <DialogContent>
                          <DialogHeader>
                            <DialogTitle>{credit.name}</DialogTitle>
                            <DialogDescription>{credit.description}</DialogDescription>
                          </DialogHeader>
                          <div className="space-y-4">
                            <div>
                              <h4 className="font-semibold mb-2">Requirements</h4>
                              <ul className="space-y-2">
                                {credit.requirements.map((req, idx) => (
                                  <li key={idx} className="flex items-start gap-2 text-sm">
                                    <Check className="h-4 w-4 mt-0.5 text-green-600 flex-shrink-0" />
                                    <span>{req}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                            <Separator />
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <Label className="text-muted-foreground">Maximum Amount</Label>
                                <p className="text-lg font-semibold">${credit.maxAmount.toLocaleString()}</p>
                              </div>
                              {credit.qualified && (
                                <div>
                                  <Label className="text-muted-foreground">Your Estimated Amount</Label>
                                  <p className="text-lg font-semibold text-green-600">
                                    ${credit.estimatedAmount.toLocaleString()}
                                  </p>
                                </div>
                              )}
                            </div>
                            {!credit.qualified && (
                              <Button className="w-full bg-black hover:bg-gray-800">
                                <Plus className="h-4 w-4 mr-2" />
                                Apply for This Credit
                              </Button>
                            )}
                          </div>
                        </DialogContent>
                      </Dialog>
                    </div>
                  ))}

                  {filteredCredits.length === 0 && (
                    <div className="text-center py-12 text-muted-foreground">
                      <HandCoins className="h-12 w-12 mx-auto mb-4 opacity-20" />
                      <p>No credits or deductions found in this category</p>
                    </div>
                  )}
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
