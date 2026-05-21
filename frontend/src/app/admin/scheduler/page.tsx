"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { toast } from "sonner"
import {
  Clock,
  Play,
  Square,
  RefreshCw,
  AlertCircle,
  CheckCircle,
  XCircle,
  Loader2,
  CalendarClock,
  Settings2,
  Activity,
  Server,
} from "lucide-react"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

const getAuthHeaders = (): Record<string, string> => {
  const token = localStorage.getItem("session_token")
  const headers: Record<string, string> = {}
  if (token) {
    headers["X-Session-Token"] = token
  }
  return headers
}

interface ScheduleEntry {
  enabled: boolean
  interval_hours: number
  timeout_minutes: number
  priority: number
  description: string
  last_run: string | null
  last_status: string | null
  consecutive_failures: number
}

interface SchedulerStatus {
  status: string
  running: boolean
  message?: string
  schedules: Record<string, ScheduleEntry>
}

interface SchedulerHealth {
  scheduler: { status: string; running_crawlers?: string[]; error?: string }
  crawler_manager: { status: string; healthy?: boolean; error?: string }
  overall: string
}

const SPIDER_NAMES: Record<string, string> = {
  news_rss: "News RSS",
  global_trends: "Global Trends",
  parliament: "Parliament",
  parliament_videos: "Parliament Videos",
  kenya_law: "Kenya Law",
  constitution: "Constitution",
  kenya_gazette: "Kenya Gazette",
  fact_check: "Fact Check",
  africa_analysis: "Africa Analysis",
}

export default function SchedulerPage() {
  const [status, setStatus] = useState<SchedulerStatus | null>(null)
  const [health, setHealth] = useState<SchedulerHealth | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [editingCrawler, setEditingCrawler] = useState<string | null>(null)
  const [editForm, setEditForm] = useState({ enabled: true, interval_hours: 24, timeout_minutes: 30 })
  const [savingSchedule, setSavingSchedule] = useState(false)

  const fetchStatus = async () => {
    try {
      const res = await fetch(`${API_URL}/api/admin/scheduler`, {
        headers: { ...getAuthHeaders() },
      })
      if (res.ok) {
        const data = await res.json()
        setStatus(data)
      }
    } catch {
      // handled below
    }
  }

  const fetchHealth = async () => {
    try {
      const res = await fetch(`${API_URL}/api/admin/scheduler/health`, {
        headers: { ...getAuthHeaders() },
      })
      if (res.ok) {
        const data = await res.json()
        setHealth(data)
      }
    } catch {
      // handled below
    }
  }

  const fetchBoth = async () => {
    setLoading(true)
    await Promise.all([fetchStatus(), fetchHealth()])
    setLoading(false)
  }

  useEffect(() => {
    fetchBoth()
    const interval = setInterval(fetchBoth, 15000)
    return () => clearInterval(interval)
  }, [])

  const startScheduler = async () => {
    setActionLoading("start")
    try {
      const res = await fetch(`${API_URL}/api/admin/scheduler/start`, {
        method: "POST",
        headers: { ...getAuthHeaders() },
      })
      if (res.ok) {
        toast.success("Scheduler started")
        fetchBoth()
      } else {
        toast.error("Failed to start scheduler")
      }
    } catch {
      toast.error("Failed to start scheduler")
    } finally {
      setActionLoading(null)
    }
  }

  const stopScheduler = async () => {
    setActionLoading("stop")
    try {
      const res = await fetch(`${API_URL}/api/admin/scheduler/stop`, {
        method: "POST",
        headers: { ...getAuthHeaders() },
      })
      if (res.ok) {
        toast.success("Scheduler stopped")
        fetchBoth()
      } else {
        toast.error("Failed to stop scheduler")
      }
    } catch {
      toast.error("Failed to stop scheduler")
    } finally {
      setActionLoading(null)
    }
  }

  const triggerCrawler = async (name: string) => {
    setActionLoading(`trigger-${name}`)
    try {
      const res = await fetch(`${API_URL}/api/admin/scheduler/trigger/${name}`, {
        method: "POST",
        headers: { ...getAuthHeaders() },
      })
      if (res.ok) {
        toast.success(`${SPIDER_NAMES[name] || name} triggered`)
        fetchBoth()
      } else {
        const err = await res.json().catch(() => ({}))
        toast.error(err.detail || "Failed to trigger crawler")
      }
    } catch {
      toast.error("Failed to trigger crawler")
    } finally {
      setActionLoading(null)
    }
  }

  const openEditDialog = (name: string, schedule: ScheduleEntry) => {
    setEditingCrawler(name)
    setEditForm({
      enabled: schedule.enabled,
      interval_hours: schedule.interval_hours,
      timeout_minutes: schedule.timeout_minutes,
    })
    setEditDialogOpen(true)
  }

  const saveSchedule = async () => {
    if (!editingCrawler) return
    setSavingSchedule(true)
    try {
      const res = await fetch(`${API_URL}/api/admin/scheduler/schedule/${editingCrawler}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", ...getAuthHeaders() },
        body: JSON.stringify(editForm),
      })
      if (res.ok) {
        toast.success("Schedule updated")
        setEditDialogOpen(false)
        fetchBoth()
      } else {
        toast.error("Failed to update schedule")
      }
    } catch {
      toast.error("Failed to update schedule")
    } finally {
      setSavingSchedule(false)
    }
  }

  const formatRelativeTime = (dateStr: string | null): string => {
    if (!dateStr) return "Never"
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMin = Math.floor(diffMs / 60000)
    if (diffMin < 1) return "Just now"
    if (diffMin < 60) return `${diffMin}m ago`
    const diffHours = Math.floor(diffMin / 60)
    if (diffHours < 24) return `${diffHours}h ago`
    const diffDays = Math.floor(diffHours / 24)
    if (diffDays === 1) return "Yesterday"
    return `${diffDays}d ago`
  }

  const getStatusBadge = (status: string | null) => {
    switch (status) {
      case "success":
        return <Badge className="bg-green-500"><CheckCircle className="w-3 h-3 mr-1" />Success</Badge>
      case "failed":
        return <Badge variant="destructive"><XCircle className="w-3 h-3 mr-1" />Failed</Badge>
      case "running":
        return <Badge variant="default"><Activity className="w-3 h-3 mr-1 animate-pulse" />Running</Badge>
      default:
        return <Badge variant="outline">—</Badge>
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold flex items-center gap-2">
            <CalendarClock className="w-8 h-8" />
            Scheduler Management
          </h1>
          <p className="text-muted-foreground">
            Manage scheduled crawler jobs and view scheduler health
          </p>
        </div>
        <div className="flex gap-2">
          {status?.running ? (
            <Button
              variant="destructive"
              onClick={stopScheduler}
              disabled={actionLoading === "stop"}
            >
              {actionLoading === "stop" ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Square className="w-4 h-4 mr-2" />
              )}
              Stop Scheduler
            </Button>
          ) : (
            <Button
              onClick={startScheduler}
              disabled={actionLoading === "start"}
            >
              {actionLoading === "start" ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Play className="w-4 h-4 mr-2" />
              )}
              Start Scheduler
            </Button>
          )}
          <Button variant="outline" onClick={fetchBoth}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Health & Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Server className="w-4 h-4" />
              Scheduler
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${
                status?.running ? "bg-green-500 animate-pulse" : "bg-gray-400"
              }`} />
              <span className="font-semibold">
                {status?.running ? "Running" : status?.status === "unavailable" ? "Unavailable" : "Stopped"}
              </span>
            </div>
            {status?.message && (
              <p className="text-xs text-muted-foreground mt-1">{status.message}</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Activity className="w-4 h-4" />
              Overall Health
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-2">
              {health?.overall === "healthy" ? (
                <CheckCircle className="w-5 h-5 text-green-500" />
              ) : health?.overall === "degraded" ? (
                <AlertCircle className="w-5 h-5 text-yellow-500" />
              ) : (
                <XCircle className="w-5 h-5 text-red-500" />
              )}
              <span className="font-semibold capitalize">{health?.overall || "Unknown"}</span>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              CM: {health?.crawler_manager?.status || "N/A"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Clock className="w-4 h-4" />
              Active Crawlers
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {health?.scheduler?.running_crawlers?.length || 0}
            </div>
            <p className="text-xs text-muted-foreground">
              Schedules: {status?.schedules ? Object.keys(status.schedules).length : 0}
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Schedule Table */}
      <Card>
        <CardHeader>
          <CardTitle>Crawler Schedules</CardTitle>
          <CardDescription>
            Configure schedules, intervals, and timeouts for each crawler
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Crawler</TableHead>
                <TableHead>Enabled</TableHead>
                <TableHead>Interval</TableHead>
                <TableHead>Timeout</TableHead>
                <TableHead>Last Run</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Failures</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {status?.schedules && Object.entries(status.schedules).length > 0 ? (
                Object.entries(status.schedules).map(([name, schedule]) => (
                  <TableRow key={name}>
                    <TableCell className="font-medium">
                      {SPIDER_NAMES[name] || name.replace(/_/g, " ")}
                      <div className="text-xs text-muted-foreground">{name}</div>
                    </TableCell>
                    <TableCell>
                      <Switch
                        checked={schedule.enabled}
                        onCheckedChange={(checked) => {
                          openEditDialog(name, schedule)
                          setEditForm((prev) => ({ ...prev, enabled: checked }))
                        }}
                      />
                    </TableCell>
                    <TableCell>{schedule.interval_hours}h</TableCell>
                    <TableCell>{schedule.timeout_minutes}m</TableCell>
                    <TableCell className="text-sm">
                      {formatRelativeTime(schedule.last_run)}
                    </TableCell>
                    <TableCell>{getStatusBadge(schedule.last_status)}</TableCell>
                    <TableCell>
                      {schedule.consecutive_failures > 0 ? (
                        <Badge variant="destructive">{schedule.consecutive_failures}</Badge>
                      ) : (
                        <span className="text-muted-foreground">0</span>
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => triggerCrawler(name)}
                          disabled={actionLoading === `trigger-${name}`}
                        >
                          {actionLoading === `trigger-${name}` ? (
                            <Loader2 className="w-3 h-3 animate-spin" />
                          ) : (
                            <Play className="w-3 h-3" />
                          )}
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => openEditDialog(name, schedule)}
                        >
                          <Settings2 className="w-3 h-3" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              ) : (
                <TableRow>
                  <TableCell colSpan={8} className="text-center py-8 text-muted-foreground">
                    {status?.status === "unavailable"
                      ? "Scheduler service is not available"
                      : "No schedule data found"}
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Edit Schedule Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              Edit Schedule — {editingCrawler ? SPIDER_NAMES[editingCrawler] || editingCrawler : ""}
            </DialogTitle>
            <DialogDescription>
              Update the schedule configuration for this crawler
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="flex items-center justify-between">
              <div>
                <Label>Enabled</Label>
                <p className="text-xs text-muted-foreground">Allow this crawler to run on schedule</p>
              </div>
              <Switch
                checked={editForm.enabled}
                onCheckedChange={(checked) => setEditForm((prev) => ({ ...prev, enabled: checked }))}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="interval">Interval (hours)</Label>
              <Input
                id="interval"
                type="number"
                min={1}
                max={168}
                value={editForm.interval_hours}
                onChange={(e) =>
                  setEditForm((prev) => ({ ...prev, interval_hours: parseInt(e.target.value) || 1 }))
                }
              />
              <p className="text-xs text-muted-foreground">
                How often the crawler should run (1-168 hours)
              </p>
            </div>
            <div className="space-y-2">
              <Label htmlFor="timeout">Timeout (minutes)</Label>
              <Input
                id="timeout"
                type="number"
                min={1}
                max={1440}
                value={editForm.timeout_minutes}
                onChange={(e) =>
                  setEditForm((prev) => ({ ...prev, timeout_minutes: parseInt(e.target.value) || 1 }))
                }
              />
              <p className="text-xs text-muted-foreground">
                Maximum runtime before the crawler is killed (1-1440 minutes)
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={saveSchedule} disabled={savingSchedule}>
              {savingSchedule ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                "Save Changes"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
