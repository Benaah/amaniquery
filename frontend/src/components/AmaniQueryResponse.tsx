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
}

interface AmaniQueryResponseProps {
  data: AmaniQueryResponse;
  className?: string;
}

// ============================================================================
// THEME CONFIGURATION
// ============================================================================

const PERSONA_THEMES = {
  public_interest: {
    name: 'wanjiku',
    colors: {
      primary: '#D84315',      // Kenyan flag red-orange
      secondary: '#388E3C',    // Kenyan flag green
      accent: '#FFA726',       // Warm orange
      bg: '#FFF3E0',          // Light warm background
      card: '#FFFFFF',
      text: '#212121',
      textSecondary: '#616161'
    },
    icon: '🇰🇪',
    summaryTitle: 'Kwa Ufupi',
    contextIcon: '🚌' // Matatu
  },
  legal: {
    name: 'wakili',
    colors: {
      primary: '#1A237E',      // Navy blue
      secondary: '#FFD700',    // Gold
      accent: '#3949AB',       // Indigo
      bg: '#E8EAF6',          // Light indigo
      card: '#FFFFFF',
      text: '#1A237E',
      textSecondary: '#5C6BC0'
    },
    icon: '⚖️',
    summaryTitle: 'Legal Summary',
    contextIcon: '📜'
  },
  research: {
    name: 'mwanahabari',
    colors: {
      primary: '#37474F',      // Blue grey
      secondary: '#00897B',    // Teal (data viz)
      accent: '#0288D1',       // Light blue (charts)
      bg: '#ECEFF1',          // Light grey
      card: '#FFFFFF',
      text: '#263238',
      textSecondary: '#546E7A'
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

export const AmaniQueryResponse: React.FC<AmaniQueryResponseProps> = ({ data, className = '' }) => {
  const [citationsExpanded, setCitationsExpanded] = useState(false);
  const [detailsExpanded, setDetailsExpanded] = useState(true);
  
  const theme = PERSONA_THEMES[data.query_type];
  const contextIcon = getContextIcon(data.response.kenyan_context.impact);

  return (
    <div 
      className={`amani-response ${className}`}
      style={{
        backgroundColor: theme.colors.bg,
        borderRadius: '16px',
        padding: '20px',
        maxWidth: '800px',
        margin: '0 auto',
        fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif'
      }}
    >
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
    <div
      style={{
        background: `linear-gradient(135deg, ${theme.colors.primary}, ${theme.colors.secondary})`,
        borderRadius: '20px',
        padding: '32px',
        marginBottom: '24px',
        boxShadow: '0 8px 32px rgba(0,0,0,0.12)',
        color: '#FFFFFF',
        position: 'relative',
        overflow: 'hidden'
      }}
    >
      {/* Background pattern */}
      <div 
        style={{
          position: 'absolute',
          top: 0,
          right: 0,
          fontSize: '120px',
          opacity: 0.1,
          lineHeight: 1
        }}
      >
        {theme.icon}
      </div>

      {/* Header */}
      <div style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '12px' }}>
        <span style={{ fontSize: '32px' }}>{theme.icon}</span>
        <h2 
          style={{
            fontSize: '20px',
            fontWeight: '700',
            margin: 0,
            textTransform: 'uppercase',
            letterSpacing: '0.5px'
          }}
        >
          {theme.summaryTitle}
        </h2>
      </div>

      {/* Title - HUGE */}
      <h1
        style={{
          fontSize: '28px',
          fontWeight: '800',
          lineHeight: '1.3',
          marginBottom: '16px',
          textShadow: '0 2px 4px rgba(0,0,0,0.1)'
        }}
      >
        {title}
      </h1>

      {/* Content */}
      <p
        style={{
          fontSize: '18px',
          lineHeight: '1.6',
          margin: 0,
          fontWeight: '400',
          opacity: 0.95
        }}
      >
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
    <div
      style={{
        backgroundColor: theme.colors.card,
        borderRadius: '16px',
        padding: '20px',
        marginBottom: '16px',
        border: `2px solid ${theme.colors.bg}`,
        boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
      }}
    >
      {/* Header */}
      <button
        onClick={onToggle}
        style={{
          width: '100%',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          padding: '0',
          marginBottom: isExpanded ? '16px' : '0'
        }}
      >
        <h3
          style={{
            fontSize: '18px',
            fontWeight: '700',
            color: theme.colors.primary,
            margin: 0,
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <BookOpen size={20} />
          Detailed Breakdown
        </h3>
        {isExpanded ? <ChevronUp color={theme.colors.primary} /> : <ChevronDown color={theme.colors.primary} />}
      </button>

      {/* Points */}
      {isExpanded && (
        <ul
          style={{
            listStyle: 'none',
            padding: 0,
            margin: 0
          }}
        >
          {points.map((point, idx) => (
            <li
              key={idx}
              style={{
                paddingLeft: '28px',
                marginBottom: '12px',
                position: 'relative',
                fontSize: '16px',
                lineHeight: '1.6',
                color: theme.colors.text
              }}
            >
              <span
                style={{
                  position: 'absolute',
                  left: '0',
                  top: '2px',
                  width: '20px',
                  height: '20px',
                  borderRadius: '50%',
                  backgroundColor: theme.colors.accent,
                  color: '#FFFFFF',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '12px',
                  fontWeight: '700'
                }}
              >
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
    <div
      style={{
        backgroundColor: theme.colors.card,
        borderRadius: '16px',
        padding: '20px',
        marginBottom: '16px',
        border: `2px solid ${theme.colors.secondary}`,
        borderLeft: `6px solid ${theme.colors.secondary}`,
        boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
      }}
    >
      {/* Header with icon */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '16px', marginBottom: '12px' }}>
        <div
          style={{
            fontSize: '48px',
            lineHeight: 1,
            flexShrink: 0
          }}
        >
          {icon}
        </div>
        
        <div style={{ flex: 1 }}>
          <h3
            style={{
              fontSize: '16px',
              fontWeight: '700',
              color: theme.colors.secondary,
              margin: '0 0 8px 0',
              textTransform: 'uppercase',
              letterSpacing: '0.5px'
            }}
          >
            🇰🇪 Kenyan Context
          </h3>
          
          <p
            style={{
              fontSize: '16px',
              lineHeight: '1.6',
              color: theme.colors.text,
              margin: 0
            }}
          >
            {impact}
          </p>
        </div>
      </div>

      {/* Related Topic */}
      {relatedTopic && (
        <div
          style={{
            marginTop: '12px',
            padding: '12px',
            backgroundColor: theme.colors.bg,
            borderRadius: '8px',
            fontSize: '14px',
            color: theme.colors.textSecondary,
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <TrendingUp size={16} />
          <span>
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
    <div
      style={{
        backgroundColor: theme.colors.card,
        borderRadius: '16px',
        padding: '20px',
        marginBottom: '16px',
        border: `1px solid ${theme.colors.bg}`,
        boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
      }}
    >
      {/* Header */}
      <button
        onClick={onToggle}
        style={{
          width: '100%',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: 'none',
          border: 'none',
          cursor: 'pointer',
          padding: '0',
          marginBottom: isExpanded ? '16px' : '0'
        }}
      >
        <h3
          style={{
            fontSize: '16px',
            fontWeight: '700',
            color: theme.colors.textSecondary,
            margin: 0,
            display: 'flex',
            alignItems: 'center',
            gap: '8px'
          }}
        >
          <ExternalLink size={18} />
          Sources ({citations.length})
        </h3>
        {isExpanded ? <ChevronUp color={theme.colors.textSecondary} /> : <ChevronDown color={theme.colors.textSecondary} />}
      </button>

      {/* Citation List */}
      {isExpanded && (
        <div style={{ marginTop: '8px' }}>
          {citations.map((citation, idx) => (
            <div
              key={idx}
              style={{
                padding: '12px',
                marginBottom: '8px',
                backgroundColor: theme.colors.bg,
                borderRadius: '8px',
                borderLeft: `3px solid ${theme.colors.accent}`
              }}
            >
              <div
                style={{
                  fontSize: '14px',
                  fontWeight: '600',
                  color: theme.colors.text,
                  marginBottom: '4px'
                }}
              >
                {citation.source}
              </div>
              
              {citation.quote && (
                <blockquote
                  style={{
                    margin: '8px 0 0 0',
                    padding: '8px 12px',
                    borderLeft: `3px solid ${theme.colors.textSecondary}`,
                    fontSize: '13px',
                    fontStyle: 'italic',
                    color: theme.colors.textSecondary,
                    backgroundColor: theme.colors.card
                  }}
                >
                  "{citation.quote}"
                </blockquote>
              )}
              
              {citation.url !== 'N/A' && (
                <a
                  href={citation.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    fontSize: '12px',
                    color: theme.colors.accent,
                    textDecoration: 'none',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                    marginTop: '8px'
                  }}
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
} & ThemeProps> = ({ suggestions, theme }) => {
  return (
    <div
      style={{
        backgroundColor: theme.colors.card,
        borderRadius: '16px',
        padding: '20px',
        border: `1px solid ${theme.colors.bg}`,
        boxShadow: '0 2px 8px rgba(0,0,0,0.05)'
      }}
    >
      <h3
        style={{
          fontSize: '16px',
          fontWeight: '700',
          color: theme.colors.primary,
          margin: '0 0 12px 0',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}
      >
        <Users size={18} />
        Want to know more?
      </h3>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {suggestions.map((suggestion, idx) => (
          <button
            key={idx}
            style={{
              padding: '12px 16px',
              backgroundColor: theme.colors.bg,
              border: `2px solid ${theme.colors.accent}`,
              borderRadius: '12px',
              fontSize: '14px',
              color: theme.colors.text,
              cursor: 'pointer',
              textAlign: 'left',
              transition: 'all 0.2s ease',
              fontWeight: '500'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = theme.colors.accent;
              e.currentTarget.style.color = '#FFFFFF';
              e.currentTarget.style.transform = 'translateX(4px)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = theme.colors.bg;
              e.currentTarget.style.color = theme.colors.text;
              e.currentTarget.style.transform = 'translateX(0)';
            }}
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  );
};

export default AmaniQueryResponse;
