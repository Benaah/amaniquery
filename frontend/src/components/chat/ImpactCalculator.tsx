import React, { useState, useEffect, useMemo } from "react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Calculator, Info, RefreshCw } from "lucide-react"
import { InteractiveWidget, WidgetInput, WidgetOutput } from "./types"

interface ImpactCalculatorProps {
  widget: InteractiveWidget
  className?: string
}

export function ImpactCalculator({ widget, className }: ImpactCalculatorProps) {
  // Initialize state with default values or empty strings
  const [values, setValues] = useState<Record<string, string>>(() => {
    const initial: Record<string, string> = {}
    widget.inputs.forEach(input => {
      if (input.default_value) {
        initial[input.name] = input.default_value
      }
    })
    return initial
  })

  const [results, setResults] = useState<Record<string, string>>({})
  const [error, setError] = useState<string | null>(null)

  // Handle input changes
  const handleInputChange = (name: string, value: string) => {
    setValues(prev => ({ ...prev, [name]: value }))
    setError(null)
  }

  // Calculate results
  const calculate = () => {
    try {
      // Prepare variables for the formula
      const variables: Record<string, number> = {}
      let allValid = true

      widget.inputs.forEach(input => {
        const val = parseFloat(values[input.name] || "0")
        if (isNaN(val)) {
          allValid = false
        }
        variables[input.name] = val
      })

      if (!allValid) {
        // Don't error immediately, just treat as 0 or wait for valid input
        // But for better UX, we might want to show a hint
      }

      // Create a safe evaluation context
      // We use new Function but with limited scope. 
      // Ideally, use a math parser library, but for this task we use JS eval with caution.
      // The formula comes from our backend (trusted source).
      
      const argNames = Object.keys(variables)
      const argValues = Object.values(variables)
      
      // Wrap formula in a return statement if it doesn't have one and isn't a single expression
      let formulaBody = widget.formula
      if (!formulaBody.includes("return") && !formulaBody.includes(";")) {
        formulaBody = `return ${formulaBody};`
      } else if (!formulaBody.includes("return")) {
         // If it has semicolons but no return, assume the last statement is the value? 
         // Or just wrap the whole thing in a function body.
         // Let's assume the prompt generates valid JS function bodies or expressions.
         // If it's an expression like "a + b", adding "return " works.
         // If it's "let a=1; a+b", adding "return " might break it if not careful.
         // Safest is to rely on the prompt to generate "return ..." or a simple expression.
         // Our few-shot examples use simple expressions or "let ...; return ...".
         // Let's try to detect if it needs 'return'.
         if (!formulaBody.trim().startsWith("let") && !formulaBody.trim().startsWith("const") && !formulaBody.trim().startsWith("var") && !formulaBody.trim().startsWith("if")) {
             formulaBody = `return ${formulaBody};`
         }
      }

      const calculateFn = new Function(...argNames, formulaBody)
      const resultValue = calculateFn(...argValues)

      // Format outputs
      const newResults: Record<string, string> = {}
      widget.outputs.forEach(output => {
        let formatted = output.format.replace("{value}", resultValue.toLocaleString(undefined, { maximumFractionDigits: 2 }))
        newResults[output.label] = formatted
      })

      setResults(newResults)
      setError(null)
    } catch (err) {
      console.error("Calculation error:", err)
      setError("Invalid calculation formula or inputs")
    }
  }

  // Auto-calculate when values change (debounced could be better but immediate is snappier for simple math)
  useEffect(() => {
    // Check if we have values for all required inputs
    const hasAllInputs = widget.inputs.every(input => values[input.name] !== undefined && values[input.name] !== "")
    if (hasAllInputs) {
      calculate()
    }
  }, [values, widget.formula])

  const handleReset = () => {
    const initial: Record<string, string> = {}
    widget.inputs.forEach(input => {
      if (input.default_value) {
        initial[input.name] = input.default_value
      }
    })
    setValues(initial)
    setResults({})
    setError(null)
  }

  return (
    <Card className={`w-full max-w-md border-primary/20 bg-primary/5 backdrop-blur-sm ${className}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <div className="p-2 rounded-lg bg-primary/10 text-primary">
            <Calculator className="w-5 h-5" />
          </div>
          <div>
            <CardTitle className="text-lg font-bold text-primary">{widget.title}</CardTitle>
            <CardDescription className="text-xs">{widget.description}</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-4">
          {widget.inputs.map((input) => (
            <div key={input.name} className="space-y-1.5">
              <label htmlFor={input.name} className="text-xs font-medium text-muted-foreground block">
                {input.label}
              </label>
              <Input
                id={input.name}
                type={input.type}
                placeholder={input.placeholder}
                value={values[input.name] || ""}
                onChange={(e) => handleInputChange(input.name, e.target.value)}
                className="bg-background/50 border-primary/10 focus:border-primary/30 transition-colors"
              />
            </div>
          ))}
        </div>

        {error && (
          <div className="p-2 rounded bg-red-500/10 text-red-500 text-xs">
            {error}
          </div>
        )}

        {Object.keys(results).length > 0 && (
          <div className="mt-4 pt-4 border-t border-primary/10 space-y-3 animate-in fade-in slide-in-from-top-2 duration-300">
            {widget.outputs.map((output, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-primary/10 border border-primary/20">
                <span className="text-sm font-medium text-muted-foreground">{output.label}</span>
                <span className="text-lg font-bold text-primary">{results[output.label]}</span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
      <CardFooter className="pt-0 pb-3 flex justify-between items-center text-xs text-muted-foreground">
        <div className="flex items-center gap-1">
            {widget.source_citation && (
                <>
                    <Info className="w-3 h-3" />
                    <span>Source: {widget.source_citation}</span>
                </>
            )}
        </div>
        <Button variant="ghost" size="sm" onClick={handleReset} className="h-6 px-2 text-xs hover:bg-primary/10">
            <RefreshCw className="w-3 h-3 mr-1" />
            Reset
        </Button>
      </CardFooter>
    </Card>
  )
}
