"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/lib/auth-context"
import { AdminSidebar } from "@/components/admin-sidebar"
import { ThemeToggle } from "@/components/theme-toggle"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { toast } from "sonner"
import {
  Activity,
  Users,
  BarChart3,
  Loader2,
  Globe,
  Key,
} from "lucide-react"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface AnalyticsData {
  total_users: number
  total_integrations: number
  total_api_keys: number
  total_requests_today: number
  total_requests_this_week: number
  total_requests_this_month: number
  total_cost_today: number
  total_cost_this_week: number
  total_cost_this_month: number
  top_users: Array<{ user_id: string; email: string; request_count: number }>
  top_integrations: Array<{ integration_id: string; name: string; request_count: number }>
  top_endpoints: Array<{ endpoint: string; request_count: number }>
  requests_over_time: Array<{ date: string; count: number }>
}

function FeedbackTrainingMetrics() {
  const [metrics, setMetrics] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const [feedbackRes, trainingRes, clusterRes] = await Promise.all([
          fetch("/api/v1/feedback/analytics"),
          fetch("/api/v1/finetuning/stats"),
          fetch("/api/v1/clusters/stats")
        ])

        const data = {
          feedback: feedbackRes.ok ? await feedbackRes.json() : null,
          training: trainingRes.ok ? await trainingRes.json() : null,
          clusters: clusterRes.ok ? await clusterRes.json() : null
        }

        setMetrics(data)
      } catch (error) {
        console.error("Failed to fetch continuous learning metrics:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchMetrics()
  }, [])

  if (loading) {
    return (
      <div className="flex justify-center py-6">
        <Loader2 className="w-6 h-6 animate-spin" />
      </div>
    )
  }

  if (!metrics) return null

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <Card className="border-l-4 border-l-blue-500">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Total Feedback</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {metrics.feedback?.feedback_distribution?.total || 0}
          </div>
          <p className="text-xs text-muted-foreground">
            {metrics.feedback?.feedback_distribution?.positive_rate?.toFixed(1)}% positive
          </p>
        </CardContent>
      </Card>

      <Card className="border-l-4 border-l-green-500">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Training Ready</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {metrics.training?.kept_for_training || 0}
          </div>
          <p className="text-xs text-muted-foreground">
            Avg: {metrics.training?.average_score?.toFixed(2) || "N/A"}
          </p>
        </CardContent>
      </Card>

      <Card className="border-l-4 border-l-orange-500">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Pending Export</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {metrics.training?.awaiting_export || 0}
          </div>
          <p className="text-xs text-muted-foreground">Ready for fine-tuning</p>
        </CardContent>
      </Card>

      <Card className="border-l-4 border-l-purple-500">
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Task Clusters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {metrics.clusters?.active_clusters || 0}
          </div>
          <p className="text-xs text-muted-foreground">
            {metrics.clusters?.total_queries_classified || 0} queries classified
          </p>
        </CardContent>
      </Card>
    </div>
  )
}


export default function AdminAnalyticsPage() {
  const { isAuthenticated, isAdmin, loading } = useAuth()
  const router = useRouter()
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null)
  const [loadingAnalytics, setLoadingAnalytics] = useState(true)

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push("/auth/signin?redirect=/admin/analytics")
    } else if (!loading && isAuthenticated && !isAdmin) {
      router.push("/chat")
    }
  }, [isAuthenticated, isAdmin, loading, router])

  useEffect(() => {
    if (isAuthenticated && isAdmin) {
      fetchAnalytics()
    }
  }, [isAuthenticated, isAdmin])

  const fetchAnalytics = async () => {
    setLoadingAnalytics(true)
    try {
      const sessionToken = localStorage.getItem("session_token")
      const response = await fetch(`/api/cache/admin/analytics`, {
        headers: {
          "X-Session-Token": sessionToken || "",
        },
      })

      if (response.ok) {
        const data = await response.json()
        setAnalytics(data)
        const cacheStatus = response.headers.get("X-Cache")
        if (cacheStatus) console.log(`Analytics cache: ${cacheStatus}`)
      } else {
        toast.error("Failed to fetch analytics")
      }
    } catch {
      toast.error("Failed to fetch analytics")
    } finally {
      setLoadingAnalytics(false)
    }
  }

  if (loading || !isAuthenticated || !isAdmin) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background flex">
      <AdminSidebar />
      <div className="flex-1 ml-0 md:ml-[20px] p-4 md:p-6">
        <div className="absolute top-4 right-4 z-10">
          <ThemeToggle />
        </div>
        <div className="max-w-7xl mx-auto space-y-6">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <BarChart3 className="w-8 h-8" />
              Analytics Dashboard
            </h1>
            <p className="text-muted-foreground">System usage and performance metrics</p>
          </div>

          {loadingAnalytics ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-6 h-6 animate-spin text-primary" />
            </div>
          ) : analytics ? (
            <>
              {/* AmaniQ Continuous Learning Metrics */}
              <div className="mb-6">
                <h2 className="text-xl font-semibold mb-4">AmaniQ Continuous Learning</h2>
                <FeedbackTrainingMetrics />
              </div>

              {/* Original System Analytics */}
              {/* Overview Stats */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Total Users</CardTitle>
                    <Users className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{analytics.total_users}</div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Integrations</CardTitle>
                    <Globe className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{analytics.total_integrations}</div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">API Keys</CardTitle>
                    <Key className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{analytics.total_api_keys}</div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <CardTitle className="text-sm font-medium">Requests Today</CardTitle>
                    <Activity className="h-4 w-4 text-muted-foreground" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{analytics.total_requests_today}</div>
                  </CardContent>
                </Card>
              </div>

              {/* Request Stats */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm font-medium">This Week</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{analytics.total_requests_this_week}</div>
                    <p className="text-xs text-muted-foreground">Requests</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm font-medium">This Month</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{analytics.total_requests_this_month}</div>
                    <p className="text-xs text-muted-foreground">Requests</p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm font-medium">Cost This Month</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">
                      ${analytics.total_cost_this_month.toFixed(2)}
                    </div>
                    <p className="text-xs text-muted-foreground">Total cost</p>
                  </CardContent>
                </Card>
              </div>

              {/* Top Users */}
              {analytics.top_users && analytics.top_users.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Top Users</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {analytics.top_users.slice(0, 10).map((user, index) => (
                        <div
                          key={user.user_id}
                          className="flex items-center justify-between p-2 rounded-lg hover:bg-accent"
                        >
                          <div className="flex items-center gap-3">
                            <Badge variant="outline">{index + 1}</Badge>
                            <span className="font-medium">{user.email}</span>
                          </div>
                          <span className="text-sm text-muted-foreground">
                            {user.request_count} requests
                          </span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Top Endpoints */}
              {analytics.top_endpoints && analytics.top_endpoints.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Top Endpoints</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {analytics.top_endpoints.slice(0, 10).map((endpoint, index) => (
                        <div
                          key={endpoint.endpoint}
                          className="flex items-center justify-between p-2 rounded-lg hover:bg-accent"
                        >
                          <div className="flex items-center gap-3">
                            <Badge variant="outline">{index + 1}</Badge>
                            <code className="text-sm font-mono">{endpoint.endpoint}</code>
                          </div>
                          <span className="text-sm text-muted-foreground">
                            {endpoint.request_count} requests
                          </span>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </>
          ) : (
            <Card>
              <CardContent className="py-12 text-center text-muted-foreground">
                No analytics data available
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}

