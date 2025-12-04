"use client"

import React, { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { X, Bell, Clock, CheckCircle, AlertCircle } from "lucide-react"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

interface NotificationSubscriptionDialogProps {
  isOpen: boolean
  onClose: () => void
  phoneNumber?: string
}

interface Source {
  name: string
  article_count: number
}

interface Subscription {
  id: number
  phone_number: string
  notification_type: "whatsapp" | "sms" | "both"
  schedule_type: "immediate" | "daily_digest"
  digest_time: string | null
  categories: string[] | null
  sources: string[] | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export default function NotificationSubscriptionDialog({
  isOpen,
  onClose,
  phoneNumber: initialPhoneNumber = ""
}: NotificationSubscriptionDialogProps) {
  const [phoneNumber, setPhoneNumber] = useState(initialPhoneNumber)
  const [notificationType, setNotificationType] = useState<"whatsapp" | "sms" | "both">("whatsapp")
  const [scheduleType, setScheduleType] = useState<"immediate" | "daily_digest">("immediate")
  const [digestTime, setDigestTime] = useState("08:00")
  const [selectedCategories, setSelectedCategories] = useState<string[]>([])
  const [selectedSources, setSelectedSources] = useState<string[]>([])
  const [categories, setCategories] = useState<string[]>([])
  const [sources, setSources] = useState<Source[]>([])
  const [loading, setLoading] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null)
  const [existingSubscription, setExistingSubscription] = useState<Subscription | null>(null)

  useEffect(() => {
    if (isOpen) {
      fetchCategories()
      fetchSources()
      if (phoneNumber) {
        checkSubscription()
      }
    }
  }, [isOpen])

  // Debounced check for subscription when phone number changes
  useEffect(() => {
    if (!isOpen || !phoneNumber || phoneNumber.length < 10) return

    const timeoutId = setTimeout(() => {
      checkSubscription()
    }, 500)

    return () => clearTimeout(timeoutId)
  }, [phoneNumber, isOpen])

  const fetchCategories = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/notifications/categories`)
      if (response.ok) {
        const data = await response.json()
        setCategories(data.categories || [])
      }
    } catch (error) {
      console.error("Failed to fetch categories:", error)
    }
  }

  const fetchSources = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/notifications/sources`)
      if (response.ok) {
        const data = await response.json()
        setSources(data.sources || [])
      }
    } catch (error) {
      console.error("Failed to fetch sources:", error)
    }
  }

  const checkSubscription = async () => {
    if (!phoneNumber) return
    setLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/notifications/subscription/${encodeURIComponent(phoneNumber)}`)
      if (response.ok) {
        const data = await response.json()
        setExistingSubscription(data)
        setNotificationType(data.notification_type || "whatsapp")
        setScheduleType(data.schedule_type || "immediate")
        setDigestTime(data.digest_time || "08:00")
        setSelectedCategories(data.categories || [])
        setSelectedSources(data.sources || [])
      } else if (response.status === 404) {
        setExistingSubscription(null)
      }
    } catch (error) {
      console.error("Failed to check subscription:", error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!phoneNumber.trim()) {
      setMessage({ type: "error", text: "Please enter a phone number" })
      return
    }

    setSubmitting(true)
    setMessage(null)

    try {
      const payload = {
        phone_number: phoneNumber.trim(),
        notification_type: notificationType,
        schedule_type: scheduleType,
        digest_time: scheduleType === "daily_digest" ? digestTime : null,
        categories: selectedCategories.length > 0 ? selectedCategories : null,
        sources: selectedSources.length > 0 ? selectedSources : null,
      }

      const response = await fetch(`${API_BASE_URL}/api/v1/notifications/subscribe`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      })

      if (response.ok) {
        setMessage({ type: "success", text: "Successfully subscribed to news notifications!" })
        setTimeout(() => {
          onClose()
          setMessage(null)
        }, 2000)
      } else {
        const error = await response.json()
        setMessage({ type: "error", text: error.detail || "Failed to subscribe" })
      }
    } catch (error) {
      setMessage({ type: "error", text: "Failed to subscribe. Please try again." })
    } finally {
      setSubmitting(false)
    }
  }

  const handleUnsubscribe = async () => {
    if (!phoneNumber.trim()) return

    setSubmitting(true)
    setMessage(null)

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/notifications/unsubscribe?phone_number=${encodeURIComponent(phoneNumber.trim())}`, {
        method: "POST",
      })

      if (response.ok) {
        setMessage({ type: "success", text: "Successfully unsubscribed" })
        setExistingSubscription(null)
        setTimeout(() => {
          onClose()
          setMessage(null)
        }, 2000)
      } else {
        const error = await response.json()
        setMessage({ type: "error", text: error.detail || "Failed to unsubscribe" })
      }
    } catch (error) {
      setMessage({ type: "error", text: "Failed to unsubscribe. Please try again." })
    } finally {
      setSubmitting(false)
    }
  }

  const toggleCategory = (category: string) => {
    setSelectedCategories((prev) =>
      prev.includes(category) ? prev.filter((c) => c !== category) : [...prev, category]
    )
  }

  const toggleSource = (source: string) => {
    setSelectedSources((prev) =>
      prev.includes(source) ? prev.filter((s) => s !== source) : [...prev, source]
    )
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <Card className="w-full max-w-2xl max-h-[90vh] overflow-y-auto m-4">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
          <CardTitle className="flex items-center text-xl">
            <Bell className="w-5 h-5 mr-2" />
            News Notifications
          </CardTitle>
          <Button variant="ghost" size="sm" onClick={onClose}>
            <X className="w-4 h-4" />
          </Button>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Phone Number */}
            <div>
              <label className="text-sm font-medium mb-2 block">Phone Number</label>
              <Input
                type="tel"
                placeholder="e.g., 0712345678 or +254712345678"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                disabled={submitting || loading}
                required
              />
              {phoneNumber && (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="mt-2"
                  onClick={checkSubscription}
                  disabled={loading}
                >
                  {loading ? "Checking..." : "Check Subscription"}
                </Button>
              )}
            </div>

            {/* Notification Type */}
            <div>
              <label className="text-sm font-medium mb-2 block">Notification Type</label>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant={notificationType === "whatsapp" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setNotificationType("whatsapp")}
                  disabled={submitting}
                >
                  WhatsApp
                </Button>
                <Button
                  type="button"
                  variant={notificationType === "sms" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setNotificationType("sms")}
                  disabled={submitting}
                >
                  SMS
                </Button>
                <Button
                  type="button"
                  variant={notificationType === "both" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setNotificationType("both")}
                  disabled={submitting}
                >
                  Both
                </Button>
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                WhatsApp is default, SMS will be used as fallback
              </p>
            </div>

            {/* Schedule Type */}
            <div>
              <label className="text-sm font-medium mb-2 block">Schedule</label>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant={scheduleType === "immediate" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setScheduleType("immediate")}
                  disabled={submitting}
                >
                  <Clock className="w-4 h-4 mr-1" />
                  Immediate
                </Button>
                <Button
                  type="button"
                  variant={scheduleType === "daily_digest" ? "default" : "outline"}
                  size="sm"
                  onClick={() => setScheduleType("daily_digest")}
                  disabled={submitting}
                >
                  Daily Digest
                </Button>
              </div>
              {scheduleType === "daily_digest" && (
                <div className="mt-2">
                  <Input
                    type="time"
                    value={digestTime}
                    onChange={(e) => setDigestTime(e.target.value)}
                    disabled={submitting}
                    className="w-32"
                  />
                </div>
              )}
            </div>

            {/* Categories Filter */}
            <div>
              <label className="text-sm font-medium mb-2 block">
                Categories (Optional - leave empty for all)
              </label>
              <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto p-2 border rounded">
                {categories.length > 0 ? (
                  categories.map((category) => (
                    <Badge
                      key={category}
                      variant={selectedCategories.includes(category) ? "default" : "outline"}
                      className="cursor-pointer"
                      onClick={() => toggleCategory(category)}
                    >
                      {category}
                    </Badge>
                  ))
                ) : (
                  <span className="text-sm text-muted-foreground">Loading categories...</span>
                )}
              </div>
            </div>

            {/* Sources Filter */}
            <div>
              <label className="text-sm font-medium mb-2 block">
                Sources (Optional - leave empty for all)
              </label>
              <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto p-2 border rounded">
                {sources.length > 0 ? (
                  sources.map((source) => (
                    <Badge
                      key={source.name}
                      variant={selectedSources.includes(source.name) ? "default" : "outline"}
                      className="cursor-pointer"
                      onClick={() => toggleSource(source.name)}
                    >
                      {source.name}
                    </Badge>
                  ))
                ) : (
                  <span className="text-sm text-muted-foreground">Loading sources...</span>
                )}
              </div>
            </div>

            {/* Message */}
            {message && (
              <div
                className={`flex items-center gap-2 p-3 rounded ${
                  message.type === "success" ? "bg-green-50 text-green-800" : "bg-red-50 text-red-800"
                }`}
              >
                {message.type === "success" ? (
                  <CheckCircle className="w-4 h-4" />
                ) : (
                  <AlertCircle className="w-4 h-4" />
                )}
                <span className="text-sm">{message.text}</span>
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-2 justify-end">
              {existingSubscription && (
                <Button
                  type="button"
                  variant="destructive"
                  onClick={handleUnsubscribe}
                  disabled={submitting}
                >
                  Unsubscribe
                </Button>
              )}
              <Button type="button" variant="outline" onClick={onClose} disabled={submitting}>
                Cancel
              </Button>
              <Button type="submit" disabled={submitting}>
                {existingSubscription ? "Update Subscription" : "Subscribe"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

