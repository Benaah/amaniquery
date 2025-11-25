/**
 * Agent Monitoring Component
 * 
 * Standalone component for monitoring agent performance
 *
 */

"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { ScrollArea } from "@/components/ui/scroll-area"
import ThinkingProcess from "@/components/ThinkingProcess"
import { 
  Activity, 
  AlertTriangle, 
  BarChart3, 
  Brain, 
  CheckCircle, 
  Clock, 
  RefreshCw,
  Search,
  TrendingUp,
  Users,
  XCircle,
  Zap,
  Flag
} from "lucide-react"
import { cn } from "@/lib/utils"

// Types (same as before)
interface QueryLog {
  id: string
  timestamp: string
  query: string
  persona: "wanjiku" | "wakili" | "mwanahabari"
  intent: "news" | "law" | "hybrid" | "general"
  confidence: number
  response_time_ms: number
  evidence_count: number
  reasoning_steps: number
  human_review_required: boolean
  agent_path: string[]
  quality_issues: string[]
  reasoning_path?: any  // For ThinkingProcess component
  user_feedback?: "positive" | "negative" | null
}

interface AgentMetrics {
  total_queries: number
  avg_confidence: number
  avg_response_time_ms: number
  human_review_rate: number
  persona_distribution: {
    wanjiku: number
    wakili: number
    mwanahabari: number
  }
  intent_distribution: {
    news: number
    law: number
    hybrid: number
    general: number
  }
  confidence_buckets: {
    low: number
    medium: number
    high: number
  }
}

interface ReviewQueueItem extends QueryLog {
  review_reason: string
  priority: "low" | "medium" | "high"
}

export function AgentMonitoring() {
  const [metrics, setMetrics] = useState<AgentMetrics | null>(null)
  const [queryLogs, setQueryLogs] = useState<QueryLog[]>([])
  const [reviewQueue, setReviewQueue] = useState<ReviewQueueItem[]>([])
  const [selectedLog, setSelectedLog] = useState<QueryLog | null>(null)
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState("")
  const [filterPersona, setFilterPersona] = useState<string>("all")
  const [filterConfidence, setFilterConfidence] = useState<string>("all")

  // Fetch functions
  const fetchMetrics = async () => {
    try {
      const response = await fetch("/api/admin/agent-metrics")
      const data = await response.json()
      setMetrics(data)
    } catch (error) {
      console.error("Error fetching metrics:", error)
      setMetrics(null)
    }
  }

  const fetchQueryLogs = async () => {
    setLoading(true)
    try {
      const response = await fetch("/api/admin/query-logs?limit=100")
      const data = await response.json()
      setQueryLogs(data.logs || [])
    } catch (error) {
      console.error("Error fetching query logs:", error)
      setQueryLogs([])
    } finally {
      setLoading(false)
    }
  }

  const fetchReviewQueue = async () => {
    try {
      const response = await fetch("/api/admin/review-queue")
      const data = await response.json()
      setReviewQueue(data.queue || [])
    } catch (error) {
      console.error("Error fetching review queue:", error)
      setReviewQueue([])
    }
  }

  const handleReviewApprove = async (logId: string) => {
    try {
      await fetch(`/api/admin/review-queue/${logId}/approve`, { method: "POST" })
      setReviewQueue(reviewQueue.filter(item => item.id !== logId))
    } catch (error) {
      console.error("Error approving review:", error)
    }
  }

  const handleReviewReject = async (logId: string, feedback: string) => {
    try {
      await fetch(`/api/admin/review-queue/${logId}/reject`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ feedback })
      })
      setReviewQueue(reviewQueue.filter(item => item.id !== logId))
    } catch (error) {
      console.error("Error rejecting review:", error)
    }
  }

  const handleRetrain = async () => {
    try {
      await fetch("/api/admin/retrain", { method: "POST" })
      alert("Retraining initiated. Check back in a few hours.")
    } catch (error) {
      console.error("Error initiating retrain:", error)
    }
  }

  // Fetch data on mount
  useEffect(() => {
    fetchMetrics()
    fetchQueryLogs()
    fetchReviewQueue()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Filter logs
  const filteredLogs = queryLogs.filter(log => {
    if (searchQuery && !log.query.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false
    }
    if (filterPersona !== "all" && log.persona !== filterPersona) {
      return false
    }
    if (filterConfidence === "low" && log.confidence >= 0.6) {
      return false
    }
    if (filterConfidence === "medium" && (log.confidence < 0.6 || log.confidence >= 0.8)) {
      return false
    }
    if (filterConfidence === "high" && log.confidence < 0.8) {
      return false
    }
    return true
  })

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Agent Monitoring</h1>
          <p className="text-muted-foreground">Monitor and manage AmaniQ agent performance</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={fetchMetrics} variant="outline">
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
          <Button onClick={handleRetrain}>
            <Brain className="mr-2 h-4 w-4" />
            Retrain Model
          </Button>
        </div>
      </div>

      {/* Metrics Overview */}
      {metrics && <MetricsOverview metrics={metrics} />}

      {/* Main Tabs */}
      <Tabs defaultValue="logs" className="space-y-4">
        <TabsList>
          <TabsTrigger value="logs">
            <Activity className="mr-2 h-4 w-4" />
            Query Logs
          </TabsTrigger>
          <TabsTrigger value="review">
            <Flag className="mr-2 h-4 w-4" />
            Review Queue ({reviewQueue.length})
          </TabsTrigger>
          <TabsTrigger value="analytics">
            <BarChart3 className="mr-2 h-4 w-4" />
            Analytics
          </TabsTrigger>
          <TabsTrigger value="training">
            <Brain className="mr-2 h-4 w-4" />
            Training
          </TabsTrigger>
        </TabsList>

        <TabsContent value="logs">
          <QueryLogsView 
            logs={filteredLogs}
            selectedLog={selectedLog}
            onSelectLog={setSelectedLog}
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
            filterPersona={filterPersona}
            onFilterPersonaChange={setFilterPersona}
            filterConfidence={filterConfidence}
            onFilterConfidenceChange={setFilterConfidence}
            loading={loading}
          />
        </TabsContent>

        <TabsContent value="review">
          <ReviewQueueView 
            queue={reviewQueue}
            onApprove={handleReviewApprove}
            onReject={handleReviewReject}
          />
        </TabsContent>

        <TabsContent value="analytics">
          <AnalyticsView metrics={metrics} logs={queryLogs} />
        </TabsContent>

        <TabsContent value="training">
          <TrainingView onRetrain={handleRetrain} />
        </TabsContent>
      </Tabs>
    </div>
  )
}

// Helper components (same implementations as before, but included here)
// MetricsOverview, QueryLogsView, ReviewQueueView, AnalyticsView, TrainingView

function MetricsOverview({ metrics }: { metrics: AgentMetrics }) {
  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Queries</CardTitle>
          <Activity className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{metrics.total_queries.toLocaleString()}</div>
          <p className="text-xs text-muted-foreground">Last 30 days</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Avg Confidence</CardTitle>
          <TrendingUp className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{(metrics.avg_confidence * 100).toFixed(1)}%</div>
          <div className="flex gap-1 mt-2">
            <Badge variant={metrics.avg_confidence >= 0.8 ? "default" : "secondary"} className="text-xs">
              {metrics.avg_confidence >= 0.8 ? "High" : metrics.avg_confidence >= 0.6 ? "Medium" : "Low"}
            </Badge>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Avg Response Time</CardTitle>
          <Zap className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{metrics.avg_response_time_ms.toFixed(0)}ms</div>
          <p className="text-xs text-muted-foreground">
            {metrics.avg_response_time_ms < 1000 ? "Excellent" : metrics.avg_response_time_ms < 2000 ? "Good" : "Slow"}
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Human Review Rate</CardTitle>
          <Users className="h-4 w-4 text-muted-foreground" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{(metrics.human_review_rate * 100).toFixed(1)}%</div>
          <p className="text-xs text-muted-foreground">
            {metrics.human_review_rate < 0.1 ? "Low" : metrics.human_review_rate < 0.3 ? "Moderate" : "High"}
          </p>
        </CardContent>
      </Card>
    </div>
  )
}

function QueryLogsView({ 
  logs, 
  selectedLog, 
  onSelectLog,
  searchQuery,
  onSearchChange,
  filterPersona,
  onFilterPersonaChange,
  filterConfidence,
  onFilterConfidenceChange,
  loading
}: any) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Query History</CardTitle>
          <CardDescription>Recent agent queries</CardDescription>
          
          <div className="space-y-2 pt-4">
            <div className="relative">
              <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search..."
                value={searchQuery}
                onChange={(e) => onSearchChange(e.target.value)}
                className="pl-8"
              />
            </div>
            <div className="flex gap-2">
              <Select value={filterPersona} onValueChange={onFilterPersonaChange}>
                <SelectTrigger className="w-[140px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Personas</SelectItem>
                  <SelectItem value="wanjiku">Wanjiku</SelectItem>
                  <SelectItem value="wakili">Wakili</SelectItem>
                  <SelectItem value="mwanahabari">Mwanahabari</SelectItem>
                </SelectContent>
              </Select>
              
              <Select value={filterConfidence} onValueChange={onFilterConfidenceChange}>
                <SelectTrigger className="w-[140px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Confidence</SelectItem>
                  <SelectItem value="low">Low</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[600px]">
            {loading ? (
              <div className="flex items-center justify-center h-40">
                <RefreshCw className="h-6 w-6 animate-spin" />
              </div>
            ) : (
              <div className="space-y-2">
                {logs.map((log: QueryLog) => (
                  <div
                    key={log.id}
                    onClick={() => onSelectLog(log)}
                    className={cn(
                      "p-3 rounded-lg border cursor-pointer hover:bg-accent",
                      selectedLog?.id === log.id && "bg-accent border-primary"
                    )}
                  >
                    <div className="flex justify-between mb-2">
                      <div className="flex gap-2">
                        <Badge variant={log.persona === "wakili" ? "default" : "secondary"}>
                          {log.persona}
                        </Badge>
                        <Badge variant="outline">{log.intent}</Badge>
                      </div>
                      <span className="text-xs text-muted-foreground">
                        {new Date(log.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    
                    <p className="text-sm font-medium line-clamp-2 mb-2">{log.query}</p>
                    
                    <div className="flex justify-between text-xs text-muted-foreground">
                      <div className="flex gap-3">
                        <span className="flex items-center gap-1">
                          <TrendingUp className="h-3 w-3" />
                          {(log.confidence * 100).toFixed(0)}%
                        </span>
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {log.response_time_ms}ms
                        </span>
                      </div>
                      {log.human_review_required && (
                        <Flag className="h-3 w-3 text-orange-500" />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Query Details</CardTitle>
        </CardHeader>
        <CardContent>
          {selectedLog ? (
            <ScrollArea className="h-[600px]">
              <div className="space-y-4">
                {/* Show ThinkingProcess if available */}
                {selectedLog.reasoning_path && (
                  <ThinkingProcess reasoning={selectedLog.reasoning_path} defaultExpanded />
                )}
                
                <div>
                  <Label className="text-xs font-semibold">Query</Label>
                  <p className="text-sm mt-1">{selectedLog.query}</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-xs font-semibold">Persona</Label>
                    <p className="text-sm mt-1">
                      <Badge>{selectedLog.persona}</Badge>
                    </p>
                  </div>
                  <div>
                    <Label className="text-xs font-semibold">Confidence</Label>
                    <p className="text-sm mt-1">
                      <Badge variant={
                        selectedLog.confidence >= 0.8 ? "default" :
                        selectedLog.confidence >= 0.6 ? "secondary" : "destructive"
                      }>
                        {(selectedLog.confidence * 100).toFixed(1)}%
                      </Badge>
                    </p>
                  </div>
                </div>

                <div>
                  <Label className="text-xs font-semibold">Agent Path</Label>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {selectedLog.agent_path.map((node: string, idx: number) => (
                      <span key={idx}>
                        <Badge variant="outline" className="text-xs">{node}</Badge>
                        {idx < selectedLog.agent_path.length - 1 && " → "}
                      </span>
                    ))}
                  </div>
                </div>

                {selectedLog.quality_issues?.length > 0 && (
                  <div>
                    <Label className="text-xs font-semibold">Quality Issues</Label>
                    <ul className="mt-2 space-y-1">
                      {selectedLog.quality_issues.map((issue: string, idx: number) => (
                        <li key={idx} className="text-sm text-orange-600 flex items-start gap-2">
                          <AlertTriangle className="h-4 w-4 mt-0.5" />
                          {issue}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </ScrollArea>
          ) : (
            <div className="flex items-center justify-center h-40 text-muted-foreground">
              Select a query to view details
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function ReviewQueueView({ queue, onApprove, onReject }: any) {
  const [selectedItem, setSelectedItem] = useState<ReviewQueueItem | null>(null)
  const [rejectFeedback, setRejectFeedback] = useState("")

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Pending Review ({queue.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[600px]">
            {queue.length === 0 ? (
              <div className="text-center text-muted-foreground py-8">
                <CheckCircle className="h-12 w-12 mx-auto mb-2 text-green-500" />
                <p>All caught up!</p>
              </div>
            ) : (
              <div className="space-y-2">
                {queue.map((item: ReviewQueueItem) => (
                  <div
                    key={item.id}
                    onClick={() => setSelectedItem(item)}
                    className={cn(
                      "p-3 rounded-lg border cursor-pointer hover:bg-accent",
                      selectedItem?.id === item.id && "bg-accent border-primary"
                    )}
                  >
                    <Badge variant={
                      item.priority === "high" ? "destructive" :
                      item.priority === "medium" ? "default" : "secondary"
                    }>
                      {item.priority} priority
                    </Badge>
                    <p className="text-sm font-medium mt-2">{item.query}</p>
                    <p className="text-xs text-muted-foreground mt-1">{item.review_reason}</p>
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Review Details</CardTitle>
        </CardHeader>
        <CardContent>
          {selectedItem ? (
            <div className="space-y-4">
              <div>
                <Label>Feedback</Label>
                <Textarea
                  value={rejectFeedback}
                  onChange={(e) => setRejectFeedback(e.target.value)}
                  placeholder="Explain what needs improvement..."
                  rows={4}
                />
              </div>
              <div className="flex gap-2">
                <Button
                  onClick={() => {
                    onApprove(selectedItem.id)
                    setSelectedItem(null)
                  }}
                  className="flex-1"
                >
                  <CheckCircle className="mr-2 h-4 w-4" />
                  Approve
                </Button>
                <Button
                  onClick={() => {
                    if (rejectFeedback.trim()) {
                      onReject(selectedItem.id, rejectFeedback)
                      setSelectedItem(null)
                      setRejectFeedback("")
                    }
                  }}
                  variant="destructive"
                  className="flex-1"
                >
                  <XCircle className="mr-2 h-4 w-4" />
                  Reject
                </Button>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-40 text-muted-foreground">
              Select an item to review
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function AnalyticsView({ metrics }: any) {
  if (!metrics) return <div>Loading...</div>

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Persona Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Object.entries(metrics.persona_distribution).map(([persona, count]: any) => {
              const percentage = (count / metrics.total_queries) * 100
              return (
                <div key={persona}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="capitalize">{persona}</span>
                    <span>{count} ({percentage.toFixed(1)}%)</span>
                  </div>
                  <div className="w-full bg-secondary rounded-full h-2">
                    <div 
                      className="bg-primary rounded-full h-2"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Confidence Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Object.entries(metrics.confidence_buckets).map(([bucket, count]: any) => {
              const percentage = (count / metrics.total_queries) * 100
              return (
                <div key={bucket}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="capitalize">{bucket}</span>
                    <span>{count} ({percentage.toFixed(1)}%)</span>
                  </div>
                  <div className="w-full bg-secondary rounded-full h-2">
                    <div 
                      className={cn(
                        "rounded-full h-2",
                        bucket === "low" && "bg-red-500",
                        bucket === "medium" && "bg-yellow-500",
                        bucket === "high" && "bg-green-500"
                      )}
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

function TrainingView({ onRetrain }: any) {
  const [trainingData, setTrainingData] = useState("")

  return (
    <Card>
      <CardHeader>
        <CardTitle>Model Retraining</CardTitle>
        <CardDescription>Upload training data and initiate retraining</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <Label>Training Data (JSONL)</Label>
          <Textarea
            value={trainingData}
            onChange={(e) => setTrainingData(e.target.value)}
            placeholder='{"query": "...", "response": "..."}'
            rows={10}
            className="font-mono text-xs"
          />
        </div>
        <Button onClick={onRetrain}>
          <Brain className="mr-2 h-4 w-4" />
          Start Retraining
        </Button>
      </CardContent>
    </Card>
  )
}

export default AgentMonitoring
