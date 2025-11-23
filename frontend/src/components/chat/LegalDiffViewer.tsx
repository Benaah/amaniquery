import React, { useMemo } from "react"
import ReactDiffViewer, { DiffMethod } from "react-diff-viewer-continued"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { GitCompare, ArrowRight } from "lucide-react"
import { GithubDiff } from "./types"

interface LegalDiffViewerProps {
  diff: GithubDiff
  className?: string
}

export function LegalDiffViewer({ diff, className }: LegalDiffViewerProps) {
  // Calculate percentage/number change for the badge
  const changeBadge = useMemo(() => {
    try {
      // Extract numbers from old and new text
      const oldNumbers = diff.old_text.match(/(\d+(\.\d+)?)/g)?.map(Number) || []
      const newNumbers = diff.new_text.match(/(\d+(\.\d+)?)/g)?.map(Number) || []

      // Simple heuristic: if we find one number in each that changed
      if (oldNumbers.length === 1 && newNumbers.length === 1) {
        const oldVal = oldNumbers[0]
        const newVal = newNumbers[0]
        
        if (oldVal !== newVal) {
          const percentChange = ((newVal - oldVal) / oldVal) * 100
          const isIncrease = newVal > oldVal
          
          return {
            text: `${isIncrease ? "+" : ""}${percentChange.toFixed(1)}% ${isIncrease ? "Increase" : "Decrease"}`,
            variant: isIncrease ? "destructive" : "default" as "default" | "destructive" | "outline" | "secondary",
            color: isIncrease ? "bg-red-600" : "bg-green-600" // Higher taxes (increase) usually bad/red, lower good/green? Or just standard diff colors?
            // Let's stick to standard: Green = Increase, Red = Decrease for numbers usually, 
            // BUT for taxes: Increase = Bad (Red), Decrease = Good (Green).
            // Let's just use neutral or standard diff colors to avoid bias.
            // For the badge, let's just show the change.
          }
        }
      }
      
      // Check for specific keywords like "increased from X to Y"
      // This is handled by the diff view itself visually, but a badge is nice.
      return null
    } catch (e) {
      return null
    }
  }, [diff.old_text, diff.new_text])

  // Custom styles for react-diff-viewer-2 to match Kenyan flag theme
  // Red (#B91C1C) for deleted, Green (#16A34A) for added
  const newStyles = {
    variables: {
      light: {
        diffViewerBackground: "transparent",
        diffViewerColor: "currentColor",
        addedBackground: "rgba(22, 163, 74, 0.2)", // Green #16A34A
        addedColor: "currentColor",
        removedBackground: "rgba(185, 28, 28, 0.2)", // Red #B91C1C
        removedColor: "currentColor",
        wordAddedBackground: "rgba(22, 163, 74, 0.4)",
        wordRemovedBackground: "rgba(185, 28, 28, 0.4)",
        addedGutterBackground: "rgba(22, 163, 74, 0.1)",
        removedGutterBackground: "rgba(185, 28, 28, 0.1)",
        gutterBackground: "transparent",
        gutterBackgroundDark: "transparent",
        highlightBackground: "rgba(255, 255, 255, 0.1)",
        highlightGutterBackground: "rgba(255, 255, 255, 0.1)",
        codeFoldGutterBackground: "transparent",
        codeFoldBackground: "transparent",
        emptyLineBackground: "transparent",
        gutterColor: "currentColor",
        addedGutterColor: "currentColor",
        removedGutterColor: "currentColor",
        codeFoldContentColor: "currentColor",
        diffViewerTitleBackground: "transparent",
        diffViewerTitleColor: "currentColor",
        diffViewerTitleBorderColor: "transparent",
      },
      dark: {
        diffViewerBackground: "transparent",
        diffViewerColor: "currentColor",
        addedBackground: "rgba(22, 163, 74, 0.2)", // Green
        addedColor: "currentColor",
        removedBackground: "rgba(185, 28, 28, 0.2)", // Red
        removedColor: "currentColor",
        wordAddedBackground: "rgba(22, 163, 74, 0.4)",
        wordRemovedBackground: "rgba(185, 28, 28, 0.4)",
        addedGutterBackground: "rgba(22, 163, 74, 0.1)",
        removedGutterBackground: "rgba(185, 28, 28, 0.1)",
        gutterBackground: "transparent",
        gutterBackgroundDark: "transparent",
        highlightBackground: "rgba(255, 255, 255, 0.1)",
        highlightGutterBackground: "rgba(255, 255, 255, 0.1)",
        codeFoldGutterBackground: "transparent",
        codeFoldBackground: "transparent",
        emptyLineBackground: "transparent",
        gutterColor: "currentColor",
        addedGutterColor: "currentColor",
        removedGutterColor: "currentColor",
        codeFoldContentColor: "currentColor",
        diffViewerTitleBackground: "transparent",
        diffViewerTitleColor: "currentColor",
        diffViewerTitleBorderColor: "transparent",
      }
    },
    line: {
      padding: '10px 2px',
      '&:hover': {
        background: 'rgba(255, 255, 255, 0.05)',
      },
    },
    content: {
        fontFamily: 'inherit',
        fontSize: '0.9rem',
    }
  }

  return (
    <Card className={`w-full overflow-hidden border-primary/20 bg-card/50 backdrop-blur-sm ${className}`}>
      <CardHeader className="pb-2 border-b border-border/50 bg-muted/30">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="p-2 rounded-lg bg-primary/10 text-primary">
              <GitCompare className="w-5 h-5" />
            </div>
            <div>
              <CardTitle className="text-base font-bold text-primary flex items-center gap-2">
                {diff.title}
              </CardTitle>
            </div>
          </div>
          {changeBadge && (
            <Badge variant={changeBadge.variant} className={`${changeBadge.color} text-white border-0`}>
              {changeBadge.text}
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="p-0 overflow-x-auto">
        <div className="min-w-[500px] text-sm">
            {/* We force dark mode styles if the app is in dark mode, but react-diff-viewer-2 
                uses a 'useDarkTheme' prop. We can try to detect or just pass true/false.
                For now, let's assume the app handles theme via class 'dark'. 
                Since we can't easily detect system preference here without hooks, 
                we'll rely on the parent passing a theme or default to light/dark based on CSS variables.
                Actually, react-diff-viewer-2 styles object handles both light and dark keys, 
                but we need to tell it which one to use.
            */}
            <ReactDiffViewer
              oldValue={diff.old_text}
              newValue={diff.new_text}
              splitView={diff.highlight_type === "side_by_side"}
              compareMethod={DiffMethod.WORDS}
              styles={newStyles}
              useDarkTheme={true} // Force dark theme styles for now as they look better in both modes with our transparent bg
              leftTitle="Original Text"
              rightTitle="Amended Text"
            />
        </div>
      </CardContent>
    </Card>
  )
}
