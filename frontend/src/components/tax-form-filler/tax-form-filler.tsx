"use client";

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { CheckCircle, FileText, Calculator, Download, AlertTriangle } from 'lucide-react';
import { PdfViewer } from '@/components/pdf-viewer';

interface W2ExtractData {
  success: boolean;
  w2_extract: {
    year: number;
    forms: Array<{
      employer: { name: string; EIN: string };
      employee: { name: string; SSN: string };
      boxes: Record<string, number | string>;
    }>;
    total_wages: number;
    total_withholding: number;
  };
  forms_count: number;
  total_wages: number;
  total_withholding: number;
  processing_method: string;
}

interface TaxpayerInfo {
  first_name: string;
  last_name: string;
  ssn: string;
  address: string;
  city: string;
  state: string;
  zip_code: string;
  filing_status: string;
  phone?: string;
  email?: string;
}

interface FormFillResponse {
  success: boolean;
  filled_form_url?: string;
  form_summary?: {
    total_w2_forms: number;
    total_wages: number;
    total_withholding: number;
    fields_filled: number;
    employers: string[];
  };
  error?: string;
}

interface TaxCalculations {
  total_wages: number;
  adjusted_gross_income: number;
  standard_deduction: number;
  taxable_income: number;
  tax_owed: number;
  total_withholding: number;
  refund_amount: number;
  amount_owed: number;
  filing_status: string;
}

interface TaxFormFillerProps {
  w2Data: W2ExtractData;
  onFormFilled?: (result: FormFillResponse) => void;
}

const FILING_STATUS_OPTIONS = [
  { value: 'single', label: 'Single' },
  { value: 'married_filing_jointly', label: 'Married Filing Jointly' },
  { value: 'married_filing_separately', label: 'Married Filing Separately' },
  { value: 'head_of_household', label: 'Head of Household' },
];

const US_STATES = [
  'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
  'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
  'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
  'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
  'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY'
];

export default function TaxFormFiller({ w2Data, onFormFilled }: TaxFormFillerProps) {
  const [currentStep, setCurrentStep] = useState(1);
  const [taxpayerInfo, setTaxpayerInfo] = useState<TaxpayerInfo>({
    first_name: '',
    last_name: '',
    ssn: '',
    address: '',
    city: '',
    state: '',
    zip_code: '',
    filing_status: 'single',
  });
  const [calculations, setCalculations] = useState<TaxCalculations | null>(null);
  const [filledFormUrl, setFilledFormUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Pre-populate from W2 data if available
  useEffect(() => {
    if (w2Data?.w2_extract?.forms?.[0]?.employee) {
      const employee = w2Data.w2_extract.forms[0].employee;
      const nameParts = employee.name?.split(' ') || [];
      
      setTaxpayerInfo(prev => ({
        ...prev,
        first_name: nameParts[0] || '',
        last_name: nameParts.slice(1).join(' ') || '',
        ssn: employee.SSN || '',
      }));
    }
  }, [w2Data]);

  const handleInputChange = (field: keyof TaxpayerInfo, value: string) => {
    setTaxpayerInfo(prev => ({ ...prev, [field]: value }));
  };

  const validateStep1 = () => {
    const required = ['first_name', 'last_name', 'ssn', 'address', 'city', 'state', 'zip_code'];
    return required.every(field => taxpayerInfo[field as keyof TaxpayerInfo]?.trim());
  };

  const previewCalculations = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/form-filler/preview-calculations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          w2_extract_data: w2Data,
          taxpayer_info: taxpayerInfo,
          form_type: '1040',
          form_year: 2024,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setCalculations(data.calculations);
      setCurrentStep(2);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to calculate taxes');
    } finally {
      setIsLoading(false);
    }
  };

  const generateFilledForm = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/form-filler/fill-form', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          w2_extract_data: w2Data,
          taxpayer_info: taxpayerInfo,
          form_type: '1040',
          form_year: 2024,
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result: FormFillResponse = await response.json();
      
      if (result.success && result.filled_form_url) {
        setFilledFormUrl(result.filled_form_url);
        setCurrentStep(3);
        onFormFilled?.(result);
      } else {
        throw new Error(result.error || 'Form generation failed');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate form');
    } finally {
      setIsLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold">Tax Form Filler</h1>
        <p className="text-muted-foreground">
          Generate your 1040 tax return using extracted W-2 data
        </p>
      </div>

      {/* Progress Steps */}
      <div className="flex items-center justify-center space-x-4 mb-8">
        {[1, 2, 3].map((step) => (
          <div key={step} className="flex items-center">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                currentStep >= step
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-muted text-muted-foreground'
              }`}
            >
              {currentStep > step ? <CheckCircle className="w-4 h-4" /> : step}
            </div>
            {step < 3 && (
              <div
                className={`w-12 h-0.5 ${
                  currentStep > step ? 'bg-primary' : 'bg-muted'
                }`}
              />
            )}
          </div>
        ))}
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Tabs value={currentStep.toString()} className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="1" disabled={currentStep < 1}>
            <FileText className="w-4 h-4 mr-2" />
            Personal Info
          </TabsTrigger>
          <TabsTrigger value="2" disabled={currentStep < 2}>
            <Calculator className="w-4 h-4 mr-2" />
            Review & Calculate
          </TabsTrigger>
          <TabsTrigger value="3" disabled={currentStep < 3}>
            <Download className="w-4 h-4 mr-2" />
            Generate Form
          </TabsTrigger>
        </TabsList>

        {/* Step 1: Personal Information */}
        <TabsContent value="1" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Personal Information</CardTitle>
              <CardDescription>
                Enter your personal details for the tax return
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="first_name">First Name *</Label>
                  <Input
                    id="first_name"
                    value={taxpayerInfo.first_name}
                    onChange={(e) => handleInputChange('first_name', e.target.value)}
                    placeholder="John"
                  />
                </div>
                <div>
                  <Label htmlFor="last_name">Last Name *</Label>
                  <Input
                    id="last_name"
                    value={taxpayerInfo.last_name}
                    onChange={(e) => handleInputChange('last_name', e.target.value)}
                    placeholder="Doe"
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="ssn">Social Security Number *</Label>
                <Input
                  id="ssn"
                  value={taxpayerInfo.ssn}
                  onChange={(e) => handleInputChange('ssn', e.target.value)}
                  placeholder="123-45-6789"
                />
              </div>

              <div>
                <Label htmlFor="address">Address *</Label>
                <Input
                  id="address"
                  value={taxpayerInfo.address}
                  onChange={(e) => handleInputChange('address', e.target.value)}
                  placeholder="123 Main St"
                />
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label htmlFor="city">City *</Label>
                  <Input
                    id="city"
                    value={taxpayerInfo.city}
                    onChange={(e) => handleInputChange('city', e.target.value)}
                    placeholder="Anytown"
                  />
                </div>
                <div>
                  <Label htmlFor="state">State *</Label>
                  <Select
                    value={taxpayerInfo.state}
                    onValueChange={(value) => handleInputChange('state', value)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select state" />
                    </SelectTrigger>
                    <SelectContent>
                      {US_STATES.map((state) => (
                        <SelectItem key={state} value={state}>
                          {state}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="zip_code">ZIP Code *</Label>
                  <Input
                    id="zip_code"
                    value={taxpayerInfo.zip_code}
                    onChange={(e) => handleInputChange('zip_code', e.target.value)}
                    placeholder="12345"
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="filing_status">Filing Status *</Label>
                <Select
                  value={taxpayerInfo.filing_status}
                  onValueChange={(value) => handleInputChange('filing_status', value)}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {FILING_STATUS_OPTIONS.map((option) => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="phone">Phone (Optional)</Label>
                  <Input
                    id="phone"
                    value={taxpayerInfo.phone || ''}
                    onChange={(e) => handleInputChange('phone', e.target.value)}
                    placeholder="(555) 123-4567"
                  />
                </div>
                <div>
                  <Label htmlFor="email">Email (Optional)</Label>
                  <Input
                    id="email"
                    type="email"
                    value={taxpayerInfo.email || ''}
                    onChange={(e) => handleInputChange('email', e.target.value)}
                    placeholder="john@example.com"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* W-2 Summary */}
          <Card>
            <CardHeader>
              <CardTitle>W-2 Summary</CardTitle>
              <CardDescription>
                Data from your extracted W-2 forms
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Total Wages</Label>
                  <div className="text-2xl font-bold text-green-600">
                    {formatCurrency(w2Data.total_wages)}
                  </div>
                </div>
                <div>
                  <Label>Federal Tax Withheld</Label>
                  <div className="text-2xl font-bold text-blue-600">
                    {formatCurrency(w2Data.total_withholding)}
                  </div>
                </div>
              </div>
              <Separator className="my-4" />
              <div className="space-y-2">
                <Label>Employers ({w2Data.forms_count} W-2 forms)</Label>
                {w2Data.w2_extract.forms.map((form, index) => (
                  <Badge key={index} variant="secondary">
                    {form.employer.name}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>

          <Button
            onClick={previewCalculations}
            disabled={!validateStep1() || isLoading}
            className="w-full"
            size="lg"
          >
            {isLoading ? 'Calculating...' : 'Continue to Review'}
          </Button>
        </TabsContent>

        {/* Step 2: Review & Calculate */}
        <TabsContent value="2" className="space-y-6">
          {calculations && (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>Tax Calculation Summary</CardTitle>
                  <CardDescription>
                    Review your calculated tax return
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-6">
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span>Total Wages:</span>
                        <span className="font-medium">
                          {formatCurrency(calculations.total_wages)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Adjusted Gross Income:</span>
                        <span className="font-medium">
                          {formatCurrency(calculations.adjusted_gross_income)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Standard Deduction:</span>
                        <span className="font-medium">
                          {formatCurrency(calculations.standard_deduction)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Taxable Income:</span>
                        <span className="font-medium">
                          {formatCurrency(calculations.taxable_income)}
                        </span>
                      </div>
                    </div>
                    
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span>Tax Owed:</span>
                        <span className="font-medium">
                          {formatCurrency(calculations.tax_owed)}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span>Federal Tax Withheld:</span>
                        <span className="font-medium">
                          {formatCurrency(calculations.total_withholding)}
                        </span>
                      </div>
                      <Separator />
                      {calculations.refund_amount > 0 ? (
                        <div className="flex justify-between text-green-600 font-bold text-lg">
                          <span>Refund:</span>
                          <span>{formatCurrency(calculations.refund_amount)}</span>
                        </div>
                      ) : (
                        <div className="flex justify-between text-red-600 font-bold text-lg">
                          <span>Amount Owed:</span>
                          <span>{formatCurrency(calculations.amount_owed)}</span>
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>

              <div className="flex space-x-4">
                <Button
                  variant="outline"
                  onClick={() => setCurrentStep(1)}
                  className="flex-1"
                >
                  Back to Edit
                </Button>
                <Button
                  onClick={generateFilledForm}
                  disabled={isLoading}
                  className="flex-1"
                  size="lg"
                >
                  {isLoading ? 'Generating Form...' : 'Generate 1040 Form'}
                </Button>
              </div>
            </>
          )}
        </TabsContent>

        {/* Step 3: Generated Form */}
        <TabsContent value="3" className="space-y-6">
          {filledFormUrl && (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>Your Completed 1040 Form</CardTitle>
                  <CardDescription>
                    Review and download your filled tax return
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span>Form Type:</span>
                      <Badge>Form 1040 (2024)</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Filing Status:</span>
                      <span className="capitalize">
                        {taxpayerInfo.filing_status.replace('_', ' ')}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>Generated:</span>
                      <span>{new Date().toLocaleDateString()}</span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <div className="h-[600px] border rounded-lg overflow-hidden">
                <PdfViewer
                  url={filledFormUrl}
                  className="w-full h-full"
                />
              </div>

              <div className="flex space-x-4">
                <Button
                  variant="outline"
                  onClick={() => setCurrentStep(2)}
                  className="flex-1"
                >
                  Back to Review
                </Button>
                <Button
                  onClick={() => window.open(filledFormUrl, '_blank')}
                  className="flex-1"
                  size="lg"
                >
                  <Download className="w-4 h-4 mr-2" />
                  Download Form
                </Button>
              </div>
            </>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
