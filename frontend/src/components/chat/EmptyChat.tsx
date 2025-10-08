import React from 'react';
import { FileText, Calculator, Calendar, CheckCircle } from 'lucide-react';

const EmptyChatState: React.FC = () => {
  return (
    <div className="flex items-center justify-center h-full">
      <div className="text-center max-w-md mx-auto px-6">
        {/* Tax Icon */}
        <div className="relative mb-6">
          <div className="w-20 h-20 bg-gradient-to-br from-green-500 to-emerald-600 rounded-full flex items-center justify-center mx-auto">
            <Calculator className="h-10 w-10 text-white" />
          </div>
          {/* Floating icons */}
          <div className="absolute -top-2 -right-2">
            <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
              <FileText className="h-4 w-4 text-white" />
            </div>
          </div>
          <div className="absolute -bottom-2 -left-2">
            <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center">
              <Calendar className="h-4 w-4 text-white" />
            </div>
          </div>
        </div>

        {/* Welcome Content */}
        <div className="space-y-4">
          <div className="space-y-2">
            <h2 className="text-2xl font-bold text-slate-800">
              Welcome to Tax Assistant
            </h2>
            <p className="text-slate-600 leading-relaxed">
              I'll help you file your taxes step by step. Upload your W-2, answer a few questions, and I'll generate your tax return.
            </p>
          </div>

          {/* Features */}
          <div className="grid grid-cols-1 gap-3 mt-6">
            <div className="flex items-center space-x-3 text-sm text-slate-600">
              <CheckCircle className="h-4 w-4 text-green-500 flex-shrink-0" />
              <span>Simple W-2 employee tax returns</span>
            </div>
            <div className="flex items-center space-x-3 text-sm text-slate-600">
              <CheckCircle className="h-4 w-4 text-green-500 flex-shrink-0" />
              <span>Automatic W-2 data extraction</span>
            </div>
            <div className="flex items-center space-x-3 text-sm text-slate-600">
              <CheckCircle className="h-4 w-4 text-green-500 flex-shrink-0" />
              <span>Draft 1040 PDF generation</span>
            </div>
            <div className="flex items-center space-x-3 text-sm text-slate-600">
              <CheckCircle className="h-4 w-4 text-green-500 flex-shrink-0" />
              <span>Filing deadline reminders</span>
            </div>
          </div>

          {/* CTA */}
          <div className="mt-8 p-4 bg-slate-50 rounded-lg">
            <p className="text-sm text-slate-600">
              <strong>Ready to start?</strong> Say "I need to file my taxes" or upload your W-2 document.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default EmptyChatState;
