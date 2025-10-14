"use client";

import React, { useState } from "react";
import { FolderDot, Search, Upload, File, FileText, Filter, Calendar, Download, Trash2, MoreHorizontal } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

interface Document {
  id: string;
  name: string;
  type: string;
  category: string;
  uploadDate: string;
  size: string;
  taxYear: number;
}

const mockDocuments: Document[] = [
  { id: "1", name: "W2_2024_Company_A.pdf", type: "W-2", category: "Income", uploadDate: "2024-01-15", size: "234 KB", taxYear: 2024 },
  { id: "2", name: "1099_MISC_2024.pdf", type: "1099-MISC", category: "Income", uploadDate: "2024-01-20", size: "156 KB", taxYear: 2024 },
  { id: "3", name: "Mortgage_Interest_Statement.pdf", type: "1098", category: "Deductions", uploadDate: "2024-01-25", size: "189 KB", taxYear: 2024 },
  { id: "4", name: "Medical_Expenses_Receipt.pdf", type: "Receipt", category: "Deductions", uploadDate: "2024-02-10", size: "98 KB", taxYear: 2024 },
  { id: "5", name: "2023_Tax_Return.pdf", type: "1040", category: "Returns", uploadDate: "2023-04-15", size: "567 KB", taxYear: 2023 },
];

export default function VaultPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [selectedYear, setSelectedYear] = useState<string>("all");

  const filteredDocuments = mockDocuments.filter(doc => {
    const matchesSearch = doc.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         doc.type.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === "all" || doc.category === selectedCategory;
    const matchesYear = selectedYear === "all" || doc.taxYear.toString() === selectedYear;
    return matchesSearch && matchesCategory && matchesYear;
  });

  const categories = ["Income", "Deductions", "Returns", "Other"];
  const years = ["2024", "2023", "2022", "2021"];

  const getCategoryBadgeColor = (category: string) => {
    switch (category) {
      case "Income": return "bg-green-100 text-green-800 border-green-200";
      case "Deductions": return "bg-blue-100 text-blue-800 border-blue-200";
      case "Returns": return "bg-purple-100 text-purple-800 border-purple-200";
      default: return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  return (
    <div className="flex-1 overflow-auto">
      <div className="container max-w-7xl mx-auto p-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-2">
            <FolderDot className="h-8 w-8" />
            <h1 className="text-3xl font-bold">Vault</h1>
          </div>
          <p className="text-muted-foreground">Manage and organize your tax documents</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Total Documents</CardDescription>
              <CardTitle className="text-3xl">{mockDocuments.length}</CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Income Documents</CardDescription>
              <CardTitle className="text-3xl">
                {mockDocuments.filter(d => d.category === "Income").length}
              </CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Deduction Documents</CardDescription>
              <CardTitle className="text-3xl">
                {mockDocuments.filter(d => d.category === "Deductions").length}
              </CardTitle>
            </CardHeader>
          </Card>
          <Card>
            <CardHeader className="pb-3">
              <CardDescription>Current Year (2024)</CardDescription>
              <CardTitle className="text-3xl">
                {mockDocuments.filter(d => d.taxYear === 2024).length}
              </CardTitle>
            </CardHeader>
          </Card>
        </div>

        {/* Actions & Filters */}
        <Card className="mb-6">
          <CardContent className="pt-6">
            <div className="flex flex-col md:flex-row gap-4">
              {/* Search */}
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search documents..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9"
                />
              </div>

              {/* Category Filter */}
              <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                <SelectTrigger className="w-full md:w-[180px]">
                  <SelectValue placeholder="Category" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories</SelectItem>
                  {categories.map(cat => (
                    <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {/* Year Filter */}
              <Select value={selectedYear} onValueChange={setSelectedYear}>
                <SelectTrigger className="w-full md:w-[180px]">
                  <SelectValue placeholder="Tax Year" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Years</SelectItem>
                  {years.map(year => (
                    <SelectItem key={year} value={year}>{year}</SelectItem>
                  ))}
                </SelectContent>
              </Select>

              {/* Upload Button */}
              <Button className="bg-black hover:bg-gray-800">
                <Upload className="h-4 w-4 mr-2" />
                Upload
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Documents List */}
        <Card>
          <CardHeader>
            <CardTitle>Documents</CardTitle>
            <CardDescription>
              {filteredDocuments.length} document{filteredDocuments.length !== 1 ? 's' : ''} found
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {filteredDocuments.map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center justify-between p-4 rounded-lg border hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center gap-4 flex-1 min-w-0">
                    <div className="h-10 w-10 rounded-lg bg-gray-100 flex items-center justify-center flex-shrink-0">
                      <FileText className="h-5 w-5 text-gray-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <p className="font-medium truncate">{doc.name}</p>
                        <Badge variant="outline" className={getCategoryBadgeColor(doc.category)}>
                          {doc.category}
                        </Badge>
                      </div>
                      <div className="flex items-center gap-3 text-sm text-muted-foreground">
                        <span>{doc.type}</span>
                        <span>•</span>
                        <span>{doc.size}</span>
                        <span>•</span>
                        <span>{new Date(doc.uploadDate).toLocaleDateString()}</span>
                        <span>•</span>
                        <span>Tax Year {doc.taxYear}</span>
                      </div>
                    </div>
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem>
                        <Download className="h-4 w-4 mr-2" />
                        Download
                      </DropdownMenuItem>
                      <DropdownMenuItem className="text-red-600">
                        <Trash2 className="h-4 w-4 mr-2" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              ))}
              {filteredDocuments.length === 0 && (
                <div className="text-center py-12 text-muted-foreground">
                  <FileText className="h-12 w-12 mx-auto mb-4 opacity-20" />
                  <p>No documents found</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
