"use client"

/**
 * Tool Result Renderer - WeKnora Integration
 * 
 * Renders tool execution results with rich formatting
 */

import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { ScrollArea } from "@/components/ui/scroll-area"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { 
  FileText, 
  Scale, 
  Search, 
  Database, 
  CheckCircle,
  XCircle,
  Clock,
  ExternalLink
} from "lucide-react"
import { cn } from "@/lib/utils"

interface ToolResult {
  tool_name: string
  status: 'success' | 'error' | 'pending'
  output: unknown
  duration_ms?: number
}

interface ToolResultRendererProps {
  result: ToolResult
  className?: string
}

export function ToolResultRenderer({ result, className }: ToolResultRendererProps) {
  const getToolIcon = (name: string) => {
    const nameLower = name.toLowerCase()
    if (nameLower.includes('search')) return <Search className="h-4 w-4" />
    if (nameLower.includes('law') || nameLower.includes('legal')) return <Scale className="h-4 w-4" />
    if (nameLower.includes('document')) return <FileText className="h-4 w-4" />
    return <Database className="h-4 w-4" />
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success': return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'error': return <XCircle className="h-4 w-4 text-red-500" />
      default: return <Clock className="h-4 w-4 text-yellow-500 animate-spin" />
    }
  }

  const renderOutput = (output: unknown) => {
    // Array of documents
    if (Array.isArray(output)) {
      return (
        <div className="space-y-2">
          {output.slice(0, 5).map((item, idx) => (
            <DocumentCard key={idx} document={item} />
          ))}
          {output.length > 5 && (
            <Badge variant="secondary">
              +{output.length - 5} more results
            </Badge>
          )}
        </div>
      )
    }

    // Object with structured data
    if (typeof output === 'object' && output !== null) {
      const obj = output as Record<string, unknown>
      
      // Table data
      if ('rows' in obj && Array.isArray(obj.rows)) {
        return <DataTable data={obj} />
      }
      
      // Generic object
      return (
        <pre className="text-xs bg-muted p-2 rounded overflow-x-auto">
          {JSON.stringify(output, null, 2)}
        </pre>
      )
    }

    // String output
    return <p className="text-sm text-muted-foreground">{String(output)}</p>
  }

  return (
    <Card className={cn("border-l-4", 
      result.status === 'success' ? "border-l-green-500" : 
      result.status === 'error' ? "border-l-red-500" : "border-l-yellow-500",
      className
    )}>
      <CardHeader className="py-2 px-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {getToolIcon(result.tool_name)}
            <CardTitle className="text-sm font-medium">{result.tool_name}</CardTitle>
          </div>
          <div className="flex items-center gap-2">
            {result.duration_ms && (
              <Badge variant="outline" className="text-xs">
                {result.duration_ms}ms
              </Badge>
            )}
            {getStatusIcon(result.status)}
          </div>
        </div>
      </CardHeader>
      <CardContent className="py-2 px-3">
        <ScrollArea className="max-h-[200px]">
          {renderOutput(result.output)}
        </ScrollArea>
      </CardContent>
    </Card>
  )
}

// Document card for search results
function DocumentCard({ document }: { document: Record<string, unknown> }) {
  return (
    <div className="p-2 bg-muted/50 rounded-md text-sm">
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1">
          <h4 className="font-medium line-clamp-1">
            {String(document.title || document.source_name || 'Document')}
          </h4>
          <p className="text-xs text-muted-foreground line-clamp-2 mt-1">
            {String(document.text || document.content || document.snippet || '')}
          </p>
        </div>
        {document.url && (
          <a href={String(document.url)} target="_blank" rel="noopener">
            <ExternalLink className="h-3 w-3 text-muted-foreground" />
          </a>
        )}
      </div>
      <div className="flex gap-1 mt-1">
        {document.category && (
          <Badge variant="secondary" className="text-xs">
            {String(document.category)}
          </Badge>
        )}
        {document.score && (
          <Badge variant="outline" className="text-xs">
            {(Number(document.score) * 100).toFixed(0)}% match
          </Badge>
        )}
      </div>
    </div>
  )
}

// Data table for structured results
function DataTable({ data }: { data: Record<string, unknown> }) {
  const rows = data.rows as Record<string, unknown>[]
  const columns = data.columns as string[] || Object.keys(rows[0] || {})

  return (
    <Table>
      <TableHeader>
        <TableRow>
          {columns.map(col => (
            <TableHead key={col} className="text-xs">{col}</TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {rows.slice(0, 5).map((row, idx) => (
          <TableRow key={idx}>
            {columns.map(col => (
              <TableCell key={col} className="text-xs">
                {String(row[col] || '')}
              </TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  )
}

export default ToolResultRenderer
