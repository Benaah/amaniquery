"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { 
  Database, 
  Activity, 
  Clock, 
  CheckCircle, 
  XCircle, 
  Play, 
  Search,
  BarChart3,
  FileText,
  Globe
} from "lucide-react"
import Link from "next/link"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface Stats {
  total_chunks: number
  categories: Record<string, number>
  sources: string[]
}

interface Health {
  status: string
  database_chunks: number
  embedding_model: string
  llm_provider: string
}

interface Crawler {
  status: "idle" | "running" | "failed"
  last_run: string
  logs: string[]
}

interface Document {
  id: string
  content: string
  metadata: {
    title: string
    url: string
    source: string
    category: string
    date: string
    author?: string
    sentiment_polarity?: number
    sentiment_label?: string
  }
  score: number
}

interface CommandResult {
  command: string
  exit_code: number
  stdout: string
  stderr: string
  cwd: string
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [health, setHealth] = useState<Health | null>(null)
  const [crawlers, setCrawlers] = useState<Record<string, Crawler>>({})
  const [documents, setDocuments] = useState<Document[]>([])
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedCrawler, setSelectedCrawler] = useState<string | null>(null)
  const [command, setCommand] = useState("")
  const [commandHistory, setCommandHistory] = useState<CommandResult[]>([])
  const [isExecuting, setIsExecuting] = useState(false)

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/stats`)
      if (response.ok) {
        const data = await response.json()
        setStats(data)
      }
    } catch (error) {
      console.error("Failed to fetch stats:", error)
    }
  }

  const fetchHealth = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/health`)
      if (response.ok) {
        const data = await response.json()
        setHealth(data)
      }
    } catch (error) {
      console.error("Failed to fetch health:", error)
    }
  }

  const fetchCrawlers = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/crawlers`)
      if (response.ok) {
        const data = await response.json()
        setCrawlers(data.crawlers || {})
      } else {
        console.error("Failed to fetch crawlers:", response.status)
        setCrawlers({})
      }
    } catch (error) {
      console.error("Failed to fetch crawlers:", error)
      setCrawlers({})
    }
  }

  const searchDocuments = async () => {
    try {
      const params = new URLSearchParams()
      if (searchQuery) params.append("query", searchQuery)
      params.append("limit", "100")

      const response = await fetch(`${API_BASE_URL}/admin/documents?${params}`)
      if (response.ok) {
        const data = await response.json()
        setDocuments(data.documents)
      }
    } catch (error) {
      console.error("Failed to search documents:", error)
    }
  }

  const executeCommand = async () => {
    if (!command.trim()) return

    setIsExecuting(true)
    try {
      const response = await fetch(`${API_BASE_URL}/admin/execute`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ command }),
      })

      if (response.ok) {
        const result: CommandResult = await response.json()
        setCommandHistory(prev => [result, ...prev.slice(0, 9)]) // Keep last 10
        setCommand("")
      }
    } catch (error) {
      console.error("Failed to execute command:", error)
    } finally {
      setIsExecuting(false)
    }
  }

  useEffect(() => {
    fetchStats()
    fetchHealth()
    fetchCrawlers()
  }, [])

  const runCrawler = async (crawlerName: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/crawlers/${crawlerName}/start`, {
        method: "POST",
      })
      if (response.ok) {
        // Refresh crawler status
        fetchCrawlers()
      }
    } catch (error) {
      console.error("Failed to start crawler:", error)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "healthy": return "text-green-600"
      case "running": return "text-blue-600"
      case "failed": return "text-red-600"
      default: return "text-gray-600"
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "healthy": return <CheckCircle className="w-4 h-4" />
      case "running": return <Activity className="w-4 h-4" />
      case "failed": return <XCircle className="w-4 h-4" />
      default: return <Clock className="w-4 h-4" />
    }
  }

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Admin Dashboard</h1>
            <p className="text-muted-foreground">Control Panel for AmaniQuery System</p>
          </div>
          <Link href="/">
            <Button variant="outline">
              <Globe className="w-4 h-4 mr-2" />
              Back to Home
            </Button>
          </Link>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Documents</CardTitle>
              <FileText className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {stats?.total_chunks || health?.database_chunks || 0}
              </div>
              <p className="text-xs text-muted-foreground">
                Vector database chunks
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Vector DB Status</CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="flex items-center space-x-2">
                {getStatusIcon(health?.status || "unknown")}
                <span className={`text-sm font-medium ${getStatusColor(health?.status || "unknown")}`}>
                  {health?.status || "Unknown"}
                </span>
              </div>
              <p className="text-xs text-muted-foreground">
                {health?.embedding_model || "Loading..."}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">System Status</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                Active
              </div>
              <p className="text-xs text-muted-foreground">
                System operational
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">API Health</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="flex items-center space-x-2">
                {health ? (
                  <>
                    <CheckCircle className="w-4 h-4 text-green-600" />
                    <span className="text-sm font-medium text-green-600">Online</span>
                  </>
                ) : (
                  <>
                    <XCircle className="w-4 h-4 text-red-600" />
                    <span className="text-sm font-medium text-red-600">Offline</span>
                  </>
                )}
              </div>
              <p className="text-xs text-muted-foreground">
                {health?.llm_provider || "Checking..."}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Crawler Management */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <BarChart3 className="w-5 h-5 mr-2" />
              Crawler Management
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Crawler</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Last Run</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {crawlers && Object.keys(crawlers).length > 0 ? (
                  Object.entries(crawlers).map(([name, crawler]) => (
                    <TableRow key={name}>
                      <TableCell className="font-medium capitalize">{name.replace('_', ' ')}</TableCell>
                      <TableCell>
                        <Badge variant={
                          crawler.status === "running" ? "default" :
                          crawler.status === "failed" ? "destructive" : "secondary"
                        }>
                          {crawler.status}
                        </Badge>
                      </TableCell>
                      <TableCell>{new Date(crawler.last_run).toLocaleString()}</TableCell>
                      <TableCell>
                        <div className="flex space-x-2">
                          <Button
                            size="sm"
                            onClick={() => runCrawler(name)}
                            disabled={crawler.status === "running"}
                          >
                            <Play className="w-3 h-3 mr-1" />
                            Run
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => setSelectedCrawler(name)}
                          >
                            Logs
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center text-muted-foreground py-8">
                      No crawlers available or loading...
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* Log Viewer */}
        {selectedCrawler && crawlers && crawlers[selectedCrawler] && (
          <Card>
            <CardHeader>
              <CardTitle>Logs - {selectedCrawler.replace('_', ' ')}</CardTitle>
            </CardHeader>
            <CardContent>
              <Textarea
                value={crawlers[selectedCrawler].logs?.join('\n') || "No logs available"}
                readOnly
                className="min-h-[200px] font-mono text-sm"
              />
            </CardContent>
          </Card>
        )}

        {/* Command Shell */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Activity className="w-5 h-5 mr-2" />
              Command Shell
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex space-x-2">
                <Input
                  placeholder="Enter command to execute..."
                  value={command}
                  onChange={(e) => setCommand(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && executeCommand()}
                  className="flex-1 font-mono"
                  disabled={isExecuting}
                />
                <Button onClick={executeCommand} disabled={isExecuting || !command.trim()}>
                  {isExecuting ? "Running..." : "Execute"}
                </Button>
              </div>
              
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {commandHistory.map((result, index) => (
                  <Card key={index} className="bg-muted">
                    <CardContent className="p-3">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="font-mono text-sm text-muted-foreground">$</span>
                        <code className="font-mono text-sm">{result.command}</code>
                        <Badge variant={result.exit_code === 0 ? "secondary" : "destructive"}>
                          Exit: {result.exit_code}
                        </Badge>
                      </div>
                      {result.stdout && (
                        <pre className="text-xs font-mono bg-background p-2 rounded border overflow-x-auto whitespace-pre-wrap">
                          {result.stdout}
                        </pre>
                      )}
                      {result.stderr && (
                        <pre className="text-xs font-mono bg-destructive/10 text-destructive p-2 rounded border overflow-x-auto whitespace-pre-wrap">
                          {result.stderr}
                        </pre>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Data Explorer */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Search className="w-5 h-5 mr-2" />
              Data Explorer
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex space-x-2">
                <Input
                  placeholder="Search documents by keyword, source, or date..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && searchDocuments()}
                  className="flex-1"
                />
                <Button onClick={searchDocuments}>
                  <Search className="w-4 h-4 mr-2" />
                  Search
                </Button>
              </div>
              
              {documents.length > 0 && (
                <div className="space-y-2">
                  <p className="text-sm text-muted-foreground">
                    Found {documents.length} documents
                  </p>
                  <div className="max-h-96 overflow-y-auto space-y-2">
                    {documents.slice(0, 20).map((doc) => (
                      <Card key={doc.id} className="cursor-pointer hover:bg-muted/50">
                        <CardContent className="p-3">
                          <div className="flex justify-between items-start mb-2">
                            <h4 className="font-medium text-sm">{doc.metadata.title || "Untitled"}</h4>
                            <Badge variant="outline">{doc.metadata.category}</Badge>
                          </div>
                          <p className="text-xs text-muted-foreground mb-2 line-clamp-2">
                            {doc.content.substring(0, 200)}...
                          </p>
                          <div className="flex justify-between text-xs text-muted-foreground">
                            <span>{doc.metadata.source}</span>
                            <span>{doc.metadata.date}</span>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              )}
              
              <div className="text-sm text-muted-foreground">
                <p>Categories: {stats ? Object.keys(stats.categories).join(", ") : "Loading..."}</p>
                <p>Sources: {stats ? stats.sources.join(", ") : "Loading..."}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}