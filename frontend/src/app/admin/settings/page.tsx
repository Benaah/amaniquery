"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/lib/auth-context"
import { AdminSidebar } from "@/components/admin-sidebar"
import { ThemeToggle } from "@/components/theme-toggle"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { toast } from "sonner"
import {
  Settings,
  Plus,
  Trash2,
  Loader2,
  RefreshCw,
} from "lucide-react"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface ConfigEntry {
  key: string
  value: string
  description?: string
}

export default function AdminSettingsPage() {
  const { isAuthenticated, isAdmin, loading } = useAuth()
  const router = useRouter()
  const [configs, setConfigs] = useState<Record<string, ConfigEntry>>({})
  const [loadingConfigs, setLoadingConfigs] = useState(true)
  const [newConfig, setNewConfig] = useState({
    key: "",
    value: "",
    description: "",
  })
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push("/auth/signin?redirect=/admin/settings")
    } else if (!loading && isAuthenticated && !isAdmin) {
      router.push("/chat")
    }
  }, [isAuthenticated, isAdmin, loading, router])

  useEffect(() => {
    if (isAuthenticated && isAdmin) {
      fetchConfigs()
    }
  }, [isAuthenticated, isAdmin])

  const fetchConfigs = async () => {
    setLoadingConfigs(true)
    try {
      const response = await fetch(`${API_URL}/admin/config`)
      if (response.ok) {
        const data = await response.json()
        setConfigs(data.configs || {})
      } else {
        toast.error("Failed to fetch settings")
      }
    } catch (error) {
      toast.error("Failed to fetch settings")
    } finally {
      setLoadingConfigs(false)
    }
  }

  const handleSaveConfig = async (key: string, value: string) => {
    try {
      const response = await fetch(`${API_URL}/admin/config/${key}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ value }),
      })

      if (response.ok) {
        toast.success("Setting updated successfully")
        fetchConfigs()
      } else {
        toast.error("Failed to update setting")
      }
    } catch (error) {
      toast.error("Failed to update setting")
    }
  }

  const handleAddConfig = async () => {
    if (!newConfig.key || !newConfig.value) {
      toast.error("Key and value are required")
      return
    }

    setSaving(true)
    try {
      const response = await fetch(`${API_URL}/admin/config/${newConfig.key}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          value: newConfig.value,
          description: newConfig.description,
        }),
      })

      if (response.ok) {
        toast.success("Setting added successfully")
        setNewConfig({ key: "", value: "", description: "" })
        fetchConfigs()
      } else {
        toast.error("Failed to add setting")
      }
    } catch (error) {
      toast.error("Failed to add setting")
    } finally {
      setSaving(false)
    }
  }

  const handleDeleteConfig = async (key: string) => {
    if (!confirm(`Are you sure you want to delete the setting "${key}"?`)) {
      return
    }

    try {
      const response = await fetch(`${API_URL}/admin/config/${key}`, {
        method: "DELETE",
      })

      if (response.ok) {
        toast.success("Setting deleted successfully")
        fetchConfigs()
      } else {
        toast.error("Failed to delete setting")
      }
    } catch (error) {
      toast.error("Failed to delete setting")
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
        <div className="max-w-4xl mx-auto space-y-6">
          <div>
            <h1 className="text-3xl font-bold flex items-center gap-2">
              <Settings className="w-8 h-8" />
              Site Settings
            </h1>
            <p className="text-muted-foreground">Manage system configuration and settings</p>
          </div>

          {/* Add New Config */}
          <Card>
            <CardHeader>
              <CardTitle>Add New Setting</CardTitle>
              <CardDescription>Create a new configuration entry</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium">Key</label>
                  <Input
                    placeholder="setting.key"
                    value={newConfig.key}
                    onChange={(e) => setNewConfig({ ...newConfig, key: e.target.value })}
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Value</label>
                  <Input
                    placeholder="Setting value"
                    value={newConfig.value}
                    onChange={(e) => setNewConfig({ ...newConfig, value: e.target.value })}
                  />
                </div>
                <div>
                  <label className="text-sm font-medium">Description (optional)</label>
                  <Input
                    placeholder="What this setting does"
                    value={newConfig.description}
                    onChange={(e) => setNewConfig({ ...newConfig, description: e.target.value })}
                  />
                </div>
                <Button onClick={handleAddConfig} disabled={saving}>
                  {saving ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Adding...
                    </>
                  ) : (
                    <>
                      <Plus className="mr-2 h-4 w-4" />
                      Add Setting
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Existing Configs */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>System Settings</CardTitle>
                  <CardDescription>Manage existing configuration entries</CardDescription>
                </div>
                <Button variant="outline" size="sm" onClick={fetchConfigs}>
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Refresh
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {loadingConfigs ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-6 h-6 animate-spin text-primary" />
                </div>
              ) : Object.keys(configs).length === 0 ? (
                <div className="text-center py-12 text-muted-foreground">
                  No settings configured
                </div>
              ) : (
                <div className="space-y-4">
                  {Object.entries(configs).map(([key, config]) => (
                    <div
                      key={key}
                      className="flex items-start gap-4 p-4 border rounded-lg hover:bg-accent/50"
                    >
                      <div className="flex-1 space-y-2">
                        <div className="flex items-center gap-2">
                          <code className="text-sm font-mono font-semibold">{key}</code>
                          {config.description && (
                            <Badge variant="outline" className="text-xs">
                              {config.description}
                            </Badge>
                          )}
                        </div>
                        <Input
                          value={config.value}
                          onChange={(e) => {
                            setConfigs({
                              ...configs,
                              [key]: { ...config, value: e.target.value },
                            })
                          }}
                          onBlur={() => handleSaveConfig(key, config.value)}
                          className="font-mono text-sm"
                        />
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeleteConfig(key)}
                        className="text-destructive hover:text-destructive"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

