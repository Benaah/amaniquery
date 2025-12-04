import React, { useState } from 'react';
import { AlertTriangle, ChevronDown, ChevronRight, CheckCircle } from 'lucide-react';
import { cn } from "@/lib/utils";

interface FactCheckAlertProps {
  issues: string[];
}

export const FactCheckAlert: React.FC<FactCheckAlertProps> = ({ issues }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  if (!issues || issues.length === 0) return null;

  return (
    <div className="mb-6 rounded-xl border border-amber-200 bg-amber-50 dark:bg-amber-950/30 dark:border-amber-900/50 overflow-hidden">
      <div 
        className="p-4 flex items-start gap-3 cursor-pointer hover:bg-amber-100/50 dark:hover:bg-amber-900/20 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <AlertTriangle className="h-5 w-5 text-amber-600 dark:text-amber-500 flex-shrink-0 mt-0.5" />
        <div className="flex-1">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-semibold text-amber-900 dark:text-amber-100">
              Potential Inaccuracies Detected
            </h3>
            {isExpanded ? (
              <ChevronDown className="h-4 w-4 text-amber-700 dark:text-amber-400" />
            ) : (
              <ChevronRight className="h-4 w-4 text-amber-700 dark:text-amber-400" />
            )}
          </div>
          <p className="text-sm text-amber-800 dark:text-amber-200 mt-1">
            Our fact-checking system flagged {issues.length} potential issue{issues.length > 1 ? 's' : ''} in this response.
          </p>
        </div>
      </div>

      {isExpanded && (
        <div className="px-4 pb-4 pt-0 border-t border-amber-200/50 dark:border-amber-900/30">
          <div className="mt-3 space-y-2">
            {issues.map((issue, idx) => (
              <div key={idx} className="flex items-start gap-2 text-sm text-amber-900 dark:text-amber-100 bg-white/50 dark:bg-black/20 p-2 rounded-md">
                <span className="font-mono text-xs font-bold text-amber-600 dark:text-amber-500 mt-0.5">
                  {idx + 1}.
                </span>
                <span>{issue}</span>
              </div>
            ))}
          </div>
          <div className="mt-3 text-xs text-amber-700 dark:text-amber-400 flex items-center gap-1">
            <CheckCircle className="h-3 w-3" />
            <span>Please verify with official sources.</span>
          </div>
        </div>
      )}
    </div>
  );
};
