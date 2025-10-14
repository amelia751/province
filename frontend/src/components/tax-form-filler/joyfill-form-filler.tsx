"use client";

import React, { useState, useEffect } from 'react';
import { JoyDoc } from '@joyfill/components';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { CheckCircle, Download, AlertTriangle, FileText } from 'lucide-react';

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

interface JoyFillFormFillerProps {
  w2Data: W2ExtractData;
  onFormFilled?: (result: any) => void;
}

export default function JoyFillFormFiller({ w2Data, onFormFilled }: JoyFillFormFillerProps) {
  const [formDocument, setFormDocument] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filledFormUrl, setFilledFormUrl] = useState<string | null>(null);

  useEffect(() => {
    loadFormTemplate();
  }, []);

  const loadFormTemplate = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Create a JoyFill document structure for the 1040 form
      // This would normally be loaded from a JoyFill template, but we'll create it programmatically
      const formDoc = createJoyFill1040Template();
      
      // Pre-populate with W2 data
      if (w2Data?.w2_extract?.forms?.[0]) {
        populateFormWithW2Data(formDoc, w2Data);
      }
      
      setFormDocument(formDoc);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load form template');
    } finally {
      setIsLoading(false);
    }
  };

  const createJoyFill1040Template = () => {
    // Create a JoyFill document structure that matches 1040 form fields
    return {
      _id: 'form-1040-2024',
      name: 'Form 1040 - U.S. Individual Income Tax Return',
      stage: 'published',
      fields: [
        // Personal Information Section
        {
          _id: 'f1_01',
          title: 'First Name',
          type: 'text',
          required: true,
          value: '',
          position: { page: 1, x: 72, y: 720, width: 120, height: 20 }
        },
        {
          _id: 'f1_02', 
          title: 'Last Name',
          type: 'text',
          required: true,
          value: '',
          position: { page: 1, x: 200, y: 720, width: 120, height: 20 }
        },
        {
          _id: 'f1_03',
          title: 'Social Security Number',
          type: 'text',
          required: true,
          value: '',
          position: { page: 1, x: 450, y: 720, width: 100, height: 20 }
        },
        {
          _id: 'f1_04',
          title: 'Spouse First Name',
          type: 'text',
          value: '',
          position: { page: 1, x: 72, y: 705, width: 120, height: 20 }
        },
        {
          _id: 'f1_05',
          title: 'Spouse Last Name', 
          type: 'text',
          value: '',
          position: { page: 1, x: 200, y: 705, width: 120, height: 20 }
        },
        {
          _id: 'f1_06',
          title: 'Spouse SSN',
          type: 'text',
          value: '',
          position: { page: 1, x: 450, y: 705, width: 100, height: 20 }
        },
        {
          _id: 'f1_07',
          title: 'Address',
          type: 'text',
          required: true,
          value: '',
          position: { page: 1, x: 72, y: 680, width: 300, height: 20 }
        },
        {
          _id: 'f1_08',
          title: 'City',
          type: 'text',
          required: true,
          value: '',
          position: { page: 1, x: 72, y: 665, width: 150, height: 20 }
        },
        {
          _id: 'f1_09',
          title: 'State',
          type: 'text',
          required: true,
          value: '',
          position: { page: 1, x: 300, y: 665, width: 40, height: 20 }
        },
        {
          _id: 'f1_10',
          title: 'ZIP Code',
          type: 'text',
          required: true,
          value: '',
          position: { page: 1, x: 350, y: 665, width: 80, height: 20 }
        },
        
        // Filing Status Section
        {
          _id: 'filing_status',
          title: 'Filing Status',
          type: 'radio',
          required: true,
          options: [
            { value: 'single', label: 'Single' },
            { value: 'married_joint', label: 'Married filing jointly' },
            { value: 'married_separate', label: 'Married filing separately' },
            { value: 'head_household', label: 'Head of household' },
            { value: 'widow', label: 'Qualifying widow(er)' }
          ],
          value: 'single',
          position: { page: 1, x: 72, y: 630, width: 300, height: 100 }
        },
        
        // Income Section
        {
          _id: 'f1_11',
          title: 'Line 1 - Wages, salaries, tips',
          type: 'number',
          value: 0,
          position: { page: 1, x: 450, y: 580, width: 100, height: 20 }
        },
        {
          _id: 'f1_12',
          title: 'Line 2a - Tax-exempt interest',
          type: 'number',
          value: 0,
          position: { page: 1, x: 450, y: 565, width: 100, height: 20 }
        },
        {
          _id: 'f1_13',
          title: 'Line 3a - Qualified dividends',
          type: 'number',
          value: 0,
          position: { page: 1, x: 450, y: 550, width: 100, height: 20 }
        },
        {
          _id: 'total_income',
          title: 'Total Income',
          type: 'number',
          value: 0,
          calculated: true,
          position: { page: 1, x: 450, y: 520, width: 100, height: 20 }
        },
        
        // Deductions Section
        {
          _id: 'standard_deduction',
          title: 'Standard Deduction',
          type: 'number',
          value: 14600, // 2024 single filer
          position: { page: 1, x: 450, y: 480, width: 100, height: 20 }
        },
        {
          _id: 'taxable_income',
          title: 'Taxable Income',
          type: 'number',
          value: 0,
          calculated: true,
          position: { page: 1, x: 450, y: 465, width: 100, height: 20 }
        },
        
        // Tax and Payments Section
        {
          _id: 'tax_owed',
          title: 'Tax',
          type: 'number',
          value: 0,
          calculated: true,
          position: { page: 1, x: 450, y: 430, width: 100, height: 20 }
        },
        {
          _id: 'federal_withholding',
          title: 'Federal income tax withheld',
          type: 'number',
          value: 0,
          position: { page: 1, x: 450, y: 400, width: 100, height: 20 }
        },
        {
          _id: 'refund_owed',
          title: 'Refund or Amount Owed',
          type: 'number',
          value: 0,
          calculated: true,
          position: { page: 1, x: 450, y: 370, width: 100, height: 20 }
        }
      ]
    };
  };

  const populateFormWithW2Data = (formDoc: any, w2Data: W2ExtractData) => {
    const w2Form = w2Data.w2_extract.forms[0];
    
    // Extract employee name
    const employeeName = w2Form.employee.name || '';
    const nameParts = employeeName.split(' ');
    
    // Update form fields with W2 data
    const fieldUpdates: Record<string, any> = {
      'f1_01': nameParts[0] || '',
      'f1_02': nameParts.slice(1).join(' ') || '',
      'f1_03': w2Form.employee.SSN || '',
      'f1_11': w2Data.total_wages || 0,
      'federal_withholding': w2Data.total_withholding || 0
    };
    
    // Apply updates to form fields
    formDoc.fields.forEach((field: any) => {
      if (fieldUpdates.hasOwnProperty(field._id)) {
        field.value = fieldUpdates[field._id];
      }
    });
    
    // Calculate derived fields
    calculateDerivedFields(formDoc);
  };

  const calculateDerivedFields = (formDoc: any) => {
    const fields = formDoc.fields;
    const getFieldValue = (id: string) => {
      const field = fields.find((f: any) => f._id === id);
      return parseFloat(field?.value || '0') || 0;
    };
    
    const setFieldValue = (id: string, value: number) => {
      const field = fields.find((f: any) => f._id === id);
      if (field) field.value = value;
    };
    
    // Calculate total income
    const wages = getFieldValue('f1_11');
    const interest = getFieldValue('f1_12');
    const dividends = getFieldValue('f1_13');
    const totalIncome = wages + interest + dividends;
    setFieldValue('total_income', totalIncome);
    
    // Calculate taxable income
    const standardDeduction = getFieldValue('standard_deduction');
    const taxableIncome = Math.max(0, totalIncome - standardDeduction);
    setFieldValue('taxable_income', taxableIncome);
    
    // Calculate tax (simplified)
    let tax = 0;
    if (taxableIncome <= 11000) {
      tax = taxableIncome * 0.10;
    } else if (taxableIncome <= 44725) {
      tax = 1100 + (taxableIncome - 11000) * 0.12;
    } else {
      tax = 5147 + (taxableIncome - 44725) * 0.22;
    }
    setFieldValue('tax_owed', Math.round(tax));
    
    // Calculate refund or amount owed
    const federalWithholding = getFieldValue('federal_withholding');
    const refundOwed = federalWithholding - tax;
    setFieldValue('refund_owed', Math.round(refundOwed));
  };

  const handleFieldChange = (fieldId: string, value: any) => {
    if (!formDocument) return;
    
    // Update the field value
    const updatedDoc = { ...formDocument };
    const field = updatedDoc.fields.find((f: any) => f._id === fieldId);
    if (field) {
      field.value = value;
      
      // Recalculate derived fields if this is an input field
      if (['f1_11', 'f1_12', 'f1_13', 'federal_withholding', 'standard_deduction'].includes(fieldId)) {
        calculateDerivedFields(updatedDoc);
      }
      
      setFormDocument(updatedDoc);
    }
  };

  const generateFilledPDF = async () => {
    if (!formDocument) return;
    
    setIsLoading(true);
    setError(null);
    
    try {
      // Convert JoyFill document data to our backend format
      const formData: Record<string, string> = {};
      formDocument.fields.forEach((field: any) => {
        formData[`${field._id}[0]`] = String(field.value || '');
      });
      
      // Call our backend to generate the filled PDF
      const response = await fetch('/api/v1/form-filler/fill-form-joyfill', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          form_data: formData,
          form_type: '1040',
          tax_year: 2024
        })
      });
      
      if (!response.ok) {
        throw new Error(`Failed to generate PDF: ${response.statusText}`);
      }
      
      const result = await response.json();
      
      if (result.success && result.filled_form_url) {
        setFilledFormUrl(result.filled_form_url);
        onFormFilled?.(result);
      } else {
        throw new Error(result.error || 'PDF generation failed');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate PDF');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading && !formDocument) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p>Loading form template...</p>
        </div>
      </div>
    );
  }

  if (error && !formDocument) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold">JoyFill Form Filler</h1>
        <p className="text-muted-foreground">
          Interactive 1040 tax return using JoyFill components
        </p>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* W2 Data Summary */}
      <Card>
        <CardHeader>
          <CardTitle>W2 Data Summary</CardTitle>
          <CardDescription>
            Data automatically populated from your W2 extraction
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium">Total Wages</label>
              <div className="text-2xl font-bold text-green-600">
                ${w2Data.total_wages.toLocaleString()}
              </div>
            </div>
            <div>
              <label className="text-sm font-medium">Federal Withholding</label>
              <div className="text-2xl font-bold text-blue-600">
                ${w2Data.total_withholding.toLocaleString()}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* JoyFill Form Component */}
      {formDocument && (
        <Card>
          <CardHeader>
            <CardTitle>Interactive Tax Form</CardTitle>
            <CardDescription>
              Fill out your 1040 form with interactive fields
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="border rounded-lg p-4 bg-gray-50 min-h-[600px]">
              <JoyDoc
                doc={formDocument}
                onChange={(changes: any) => {
                  // Handle field changes
                  Object.entries(changes).forEach(([fieldId, value]) => {
                    handleFieldChange(fieldId, value);
                  });
                }}
                mode="fill" // Set to fill mode for form filling
                className="w-full h-full"
              />
            </div>
          </CardContent>
        </Card>
      )}

      {/* Actions */}
      <div className="flex space-x-4">
        <Button
          onClick={generateFilledPDF}
          disabled={isLoading || !formDocument}
          className="flex-1"
          size="lg"
        >
          {isLoading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Generating PDF...
            </>
          ) : (
            <>
              <FileText className="w-4 h-4 mr-2" />
              Generate Filled 1040 PDF
            </>
          )}
        </Button>
      </div>

      {/* Generated PDF */}
      {filledFormUrl && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <CheckCircle className="w-5 h-5 text-green-500 mr-2" />
              PDF Generated Successfully
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <p>Your filled 1040 form is ready for download.</p>
              <Button
                onClick={() => window.open(filledFormUrl, '_blank')}
                variant="outline"
              >
                <Download className="w-4 h-4 mr-2" />
                Download PDF
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
