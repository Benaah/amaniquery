/**
 * AmaniQuery v2 Response Display Component
 * 
 * Displays structured JSON responses with persona-specific theming:
 * - wanjiku: Warm orange/green (Kenyan flag vibes)
 * - wakili: Navy blue + gold (legal professional)
 * - mwanahabari: Neutral grey + data visualization
 */

import React, { useState } from 'react';
import { ChevronDown, ChevronUp, ExternalLink, BookOpen, TrendingUp, Users } from 'lucide-react';
import { cn } from "@/lib/utils";
import { ThinkingProcess } from './ThinkingProcess';
import { FactCheckAlert } from './FactCheckAlert';

// ============================================================================
// TYPES
// ============================================================================

export type QueryType = 'public_interest' | 'legal' | 'research';

export interface AmaniQueryResponse {
  query_type: QueryType;
  language_detected: string;
  response: {
    summary_card: {
      title: string;
      content: string;
    };
    detailed_breakdown: {
      points: string[];
    };
    kenyan_context: {
      impact: string;
      related_topic: string | null;
    };
    citations: Array<{
      source: string;
      url: string;
      quote: string | null;
    }>;
  };
  follow_up_suggestions: string[];
  metadata?: {
    reasoning_path?: {
      query: string;
      thoughts: Array<{
        step: number;
        action: string;
        observation: string;
        reasoning: string;
        duration_ms?: number;
        confidence?: number;
      }>;
      total_duration_ms: number;
      final_conclusion: string;
    };
    quality_issues?: string[];
    [key: string]: unknown;
  };
}

interface AmaniQueryResponseProps {
  data: AmaniQueryResponse;
  className?: string;
  onFollowUpClick?: (suggestion: string) => void;
}

// ============================================================================
// THEME CONFIGURATION
// ============================================================================

const PERSONA_THEMES = {
  public_interest: {
    name: 'wanjiku',
    classes: {
      container: 'bg-orange-50/50 dark:bg-orange-950/20',
      card: 'bg-white dark:bg-gray-900 border-orange-100 dark:border-orange-900/50',
      summaryGradient: 'from-orange-600 to-green-600',
      primaryText: 'text-orange-900 dark:text-orange-100',
      secondaryText: 'text-orange-700 dark:text-orange-300',
      accentBg: 'bg-orange-500',
      accentText: 'text-orange-600 dark:text-orange-400',
      border: 'border-orange-200 dark:border-orange-800',
      contextBorder: 'border-green-600 dark:border-green-500',
      iconColor: 'text-green-600 dark:text-green-500',
      buttonHover: 'hover:bg-orange-100 dark:hover:bg-orange-900/50'
    },
    icon: '🇰🇪',
    summaryTitle: 'Kwa Ufupi',
    contextIcon: '🚌' // Matatu
  },
  legal: {
    name: 'wakili',
    classes: {
      container: 'bg-indigo-50/50 dark:bg-indigo-950/20',
      card: 'bg-white dark:bg-gray-900 border-indigo-100 dark:border-indigo-900/50',
      summaryGradient: 'from-indigo-700 to-blue-900',
      primaryText: 'text-indigo-900 dark:text-indigo-100',
      secondaryText: 'text-indigo-700 dark:text-indigo-300',
      accentBg: 'bg-indigo-500',
      accentText: 'text-indigo-600 dark:text-indigo-400',
      border: 'border-indigo-200 dark:border-indigo-800',
      contextBorder: 'border-amber-400 dark:border-amber-500',
      iconColor: 'text-amber-500 dark:text-amber-400',
      buttonHover: 'hover:bg-indigo-100 dark:hover:bg-indigo-900/50'
    },
    icon: '⚖️',
    summaryTitle: 'Legal Summary',
    contextIcon: '📜'
  },
  research: {
    name: 'mwanahabari',
    classes: {
      container: 'bg-slate-50/50 dark:bg-slate-950/20',
      card: 'bg-white dark:bg-gray-900 border-slate-100 dark:border-slate-800',
      summaryGradient: 'from-slate-700 to-teal-700',
      primaryText: 'text-slate-900 dark:text-slate-100',
      secondaryText: 'text-slate-700 dark:text-slate-300',
      accentBg: 'bg-teal-500',
      accentText: 'text-teal-600 dark:text-teal-400',
      border: 'border-slate-200 dark:border-slate-700',
      contextBorder: 'border-teal-500 dark:border-teal-400',
      iconColor: 'text-teal-600 dark:text-teal-500',
      buttonHover: 'hover:bg-slate-100 dark:hover:bg-slate-800'
    },
    icon: '📊',
    summaryTitle: 'The Bottom Line',
    contextIcon: '📈'
  }
};

// ============================================================================
// KENYAN CONTEXT ICONS
// ============================================================================

const KENYAN_CONTEXT_ICONS: Record<string, string> = {
  'transport': '🚌', // Matatu
  'money': '💰',
  'government': '🏛️',
  'food': '🌽', // Maize/ugali
  'housing': '🏘️',
  'health': '🏥',
  'education': '📚',
  'default': '🇰🇪'
};

const getContextIcon = (impact: string): string => {
  const lowercaseImpact = impact.toLowerCase();
  
  if (lowercaseImpact.includes('transport') || lowercaseImpact.includes('matatu') || lowercaseImpact.includes('parking')) {
    return KENYAN_CONTEXT_ICONS.transport;
  }
  if (lowercaseImpact.includes('money') || lowercaseImpact.includes('fee') || lowercaseImpact.includes('cost')) {
    return KENYAN_CONTEXT_ICONS.money;
  }
  if (lowercaseImpact.includes('food') || lowercaseImpact.includes('mama mboga')) {
    return KENYAN_CONTEXT_ICONS.food;
  }
  if (lowercaseImpact.includes('housing') || lowercaseImpact.includes('rent')) {
    return KENYAN_CONTEXT_ICONS.housing;
  }
  
  return KENYAN_CONTEXT_ICONS.default;
};

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export const AmaniQueryResponse: React.FC<AmaniQueryResponseProps> = ({ data, className = '', onFollowUpClick }) => {
  const [citationsExpanded, setCitationsExpanded] = useState(false);
  const [detailsExpanded, setDetailsExpanded] = useState(true);
  
  const theme = PERSONA_THEMES[data.query_type];
  const contextIcon = getContextIcon(data.response.kenyan_context.impact);

  return (
    <div className={cn(
      "rounded-2xl p-5 max-w-3xl mx-auto font-sans transition-colors duration-200",
      theme.classes.container,
      className
    )}>
      {/* THINKING PROCESS - Display if available */}
      {data.metadata?.reasoning_path && (
        <div className="mb-6">
          <ThinkingProcess 
            reasoning={data.metadata.reasoning_path} 
            className="bg-white/50 dark:bg-black/20 backdrop-blur-sm"
          />
        </div>
      )}

      {/* FACT CHECK ALERT - Display if issues found */}
      {data.metadata?.quality_issues && Array.isArray(data.metadata.quality_issues) && data.metadata.quality_issues.length > 0 && (
        <FactCheckAlert issues={data.metadata.quality_issues as string[]} />
      )}

      {/* SUMMARY CARD - HUGE AND PROMINENT */}
      <SummaryCard 
        title={data.response.summary_card.title}
        content={data.response.summary_card.content}
        theme={theme}
      />

      {/* DETAILED BREAKDOWN */}
      <DetailedBreakdown
        points={data.response.detailed_breakdown.points}
        theme={theme}
        isExpanded={detailsExpanded}
        onToggle={() => setDetailsExpanded(!detailsExpanded)}
      />

      {/* KENYAN CONTEXT */}
      <KenyanContext
        impact={data.response.kenyan_context.impact}
        relatedTopic={data.response.kenyan_context.related_topic}
        icon={contextIcon}
        theme={theme}
      />

      {/* CITATIONS */}
      <Citations
        citations={data.response.citations}
        theme={theme}
        isExpanded={citationsExpanded}
        onToggle={() => setCitationsExpanded(!citationsExpanded)}
      />

      {/* FOLLOW-UP SUGGESTIONS */}
      <FollowUpSuggestions
        suggestions={data.follow_up_suggestions}
        theme={theme}
        onFollowUpClick={onFollowUpClick}
      />
    </div>
  );
};

// ============================================================================
// SUB-COMPONENTS
// ============================================================================

interface ThemeProps {
  theme: typeof PERSONA_THEMES[keyof typeof PERSONA_THEMES];
}

// SUMMARY CARD - TikTok-style prominence
const SummaryCard: React.FC<{ title: string; content: string } & ThemeProps> = ({ 
  title, 
  content, 
  theme 
}) => {
  return (
    <div className={cn(
      "relative overflow-hidden rounded-2xl p-8 mb-6 shadow-lg text-white",
      `bg-gradient-to-br ${theme.classes.summaryGradient}`
    )}>
      {/* Background pattern */}
      <div className="absolute top-0 right-0 text-[120px] opacity-10 leading-none pointer-events-none select-none">
        {theme.icon}
      </div>

      {/* Header */}
      <div className="flex items-center gap-3 mb-4 relative z-10">
        <span className="text-3xl">{theme.icon}</span>
        <h2 className="text-lg font-bold uppercase tracking-wide m-0">
          {theme.summaryTitle}
        </h2>
      </div>

      {/* Title - HUGE */}
      <h1 className="text-2xl md:text-3xl font-extrabold leading-tight mb-4 drop-shadow-sm relative z-10">
        {title}
      </h1>

      {/* Content */}
      <p className="text-lg leading-relaxed font-normal opacity-95 m-0 relative z-10">
        {content}
      </p>
    </div>
  );
};

// DETAILED BREAKDOWN
const DetailedBreakdown: React.FC<{
  points: string[];
  isExpanded: boolean;
  onToggle: () => void;
} & ThemeProps> = ({ points, theme, isExpanded, onToggle }) => {
  return (
    <div className={cn(
      "rounded-2xl p-5 mb-4 border shadow-sm transition-all duration-200",
      theme.classes.card
    )}>
      {/* Header */}
      <button
        onClick={onToggle}
        className="w-full flex justify-between items-center bg-transparent border-none cursor-pointer p-0"
      >
        <h3 className={cn(
          "text-lg font-bold flex items-center gap-2 m-0",
          theme.classes.secondaryText
        )}>
          <BookOpen size={20} />
          Detailed Breakdown
        </h3>
        {isExpanded ? (
          <ChevronUp className={theme.classes.secondaryText} />
        ) : (
          <ChevronDown className={theme.classes.secondaryText} />
        )}
      </button>

      {/* Points */}
      {isExpanded && (
        <ul className="list-none p-0 m-0 mt-4 space-y-3">
          {points.map((point, idx) => (
            <li key={idx} className={cn(
              "pl-8 relative text-base leading-relaxed",
              theme.classes.primaryText
            )}>
              <span className={cn(
                "absolute left-0 top-0.5 w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold text-white",
                theme.classes.accentBg
              )}>
                {idx + 1}
              </span>
              {point}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

// KENYAN CONTEXT
const KenyanContext: React.FC<{
  impact: string;
  relatedTopic: string | null;
  icon: string;
} & ThemeProps> = ({ impact, relatedTopic, icon, theme }) => {
  return (
    <div className={cn(
      "rounded-2xl p-5 mb-4 border-2 border-l-[6px] shadow-sm",
      theme.classes.card,
      theme.classes.contextBorder
    )}>
      {/* Header with icon */}
      <div className="flex items-start gap-4 mb-3">
        <div className="text-5xl leading-none flex-shrink-0">
          {icon}
        </div>
        
        <div className="flex-1">
          <h3 className={cn(
            "text-base font-bold uppercase tracking-wide mb-2",
            theme.classes.iconColor
          )}>
            🇰🇪 Kenyan Context
          </h3>
          
          <p className={cn(
            "text-base leading-relaxed m-0",
            theme.classes.primaryText
          )}>
            {impact}
          </p>
        </div>
      </div>

      {/* Related Topic */}
      {relatedTopic && (
        <div className={cn(
          "mt-3 p-3 rounded-lg text-sm flex items-center gap-2",
          theme.classes.container
        )}>
          <TrendingUp size={16} className={theme.classes.secondaryText} />
          <span className={theme.classes.secondaryText}>
            <strong>Related:</strong> {relatedTopic}
          </span>
        </div>
      )}
    </div>
  );
};

// CITATIONS (Collapsible)
const Citations: React.FC<{
  citations: AmaniQueryResponse['response']['citations'];
  isExpanded: boolean;
  onToggle: () => void;
} & ThemeProps> = ({ citations, theme, isExpanded, onToggle }) => {
  return (
    <div className={cn(
      "rounded-2xl p-5 mb-4 border shadow-sm",
      theme.classes.card
    )}>
      {/* Header */}
      <button
        onClick={onToggle}
        className="w-full flex justify-between items-center bg-transparent border-none cursor-pointer p-0"
      >
        <h3 className="text-base font-bold text-muted-foreground flex items-center gap-2 m-0">
          <ExternalLink size={18} />
          Sources ({citations.length})
        </h3>
        {isExpanded ? (
          <ChevronUp className="text-muted-foreground" />
        ) : (
          <ChevronDown className="text-muted-foreground" />
        )}
      </button>

      {/* Citation List */}
      {isExpanded && (
        <div className="mt-4 space-y-2">
          {citations.map((citation, idx) => (
            <div
              key={idx}
              className={cn(
                "p-3 rounded-lg border-l-4 [border-left-color:currentColor]",
                theme.classes.container,
                theme.classes.border
              )}
            >
              <div className={cn(
                "text-sm font-semibold mb-1",
                theme.classes.primaryText
              )}>
                {citation.source}
              </div>
              
              {citation.quote && (
                <blockquote className={cn(
                  "mt-2 mb-0 pl-3 border-l-2 text-sm italic",
                  "border-muted-foreground/30 text-muted-foreground"
                )}>
                  &quot;{citation.quote}&quot;
                </blockquote>
              )}
              
              {citation.url !== 'N/A' && (
                <a
                  href={citation.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={cn(
                    "text-sm underline decoration-2 underline-offset-2 inline-flex items-center gap-1 mt-2",
                    "text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300",
                    "transition-colors duration-200 font-medium"
                  )}
                >
                  View source <ExternalLink size={12} />
                </a>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// FOLLOW-UP SUGGESTIONS
const FollowUpSuggestions: React.FC<{
  suggestions: string[];
  onFollowUpClick?: (suggestion: string) => void;
} & ThemeProps> = ({ suggestions, theme, onFollowUpClick }) => {
  return (
    <div className={cn(
      "rounded-2xl p-5 border shadow-sm",
      theme.classes.card
    )}>
      <h3 className={cn(
        "text-base font-bold mb-3 flex items-center gap-2",
        theme.classes.secondaryText
      )}>
        <Users size={18} />
        Want to know more?
      </h3>

      <div className="flex flex-col gap-2">
        {suggestions.map((suggestion, idx) => (
          <button
            key={idx}
            onClick={() => onFollowUpClick?.(suggestion)}
            className={cn(
              "p-3 md:px-4 rounded-xl text-sm text-left transition-all duration-200 font-medium border-2",
              "bg-transparent cursor-pointer",
              theme.classes.border,
              theme.classes.primaryText,
              theme.classes.buttonHover,
              "hover:translate-x-1 hover:shadow-md active:scale-[0.98]"
            )}
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  );
};

export default AmaniQueryResponse;
