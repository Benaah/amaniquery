"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { useAuth } from "@/lib/auth-context"
import { apiClient } from "@/lib/api-client"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { OTPInput } from "@/components/ui/otp-input"
import { toast } from "sonner"
import { Loader2 } from "lucide-react"

export default function SignUpPage() {
  const [step, setStep] = useState<"form" | "otp">("form")
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    name: "",
    phone_number: "",
  })
  const [otp, setOtp] = useState("")
  const [phoneNumber, setPhoneNumber] = useState("")
  const router = useRouter()
  const { register } = useAuth()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      // Register user
      await register(
        formData.email,
        formData.password,
        formData.name,
        formData.phone_number
      )

      // Send OTP
      await apiClient.post("/api/v1/auth/phone/send-otp", {
        phone_number: formData.phone_number,
        purpose: "verification",
      })

      setPhoneNumber(formData.phone_number)
      setStep("otp")
      toast.success("OTP sent to your phone number")
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : "Registration failed"
      toast.error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleOTPVerify = async () => {
    if (otp.length !== 6) {
      toast.error("Please enter a valid 6-digit OTP")
      return
    }

    setLoading(true)

    try {
      // Verify OTP
      await apiClient.post("/api/v1/auth/phone/verify-otp", {
        phone_number: phoneNumber,
        otp: otp,
        purpose: "verification",
      })

      toast.success("Phone verified successfully! Please sign in.")
      router.push("/auth/signin")
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : "OTP verification failed"
      toast.error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handleResendOTP = async () => {
    setLoading(true)
    try {
      await apiClient.post("/api/v1/auth/phone/resend-otp", {
        phone_number: phoneNumber,
        purpose: "verification",
      })
      toast.success("OTP resent successfully")
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : "Failed to resend OTP"
      toast.error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  if (step === "otp") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-primary/5 to-accent/10 p-4">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle>Verify Phone Number</CardTitle>
            <CardDescription>
              Enter the 6-digit code sent to {phoneNumber}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <OTPInput
              value={otp}
              onChange={setOtp}
              onComplete={handleOTPVerify}
              disabled={loading}
            />
            <Button
              onClick={handleOTPVerify}
              disabled={loading || otp.length !== 6}
              className="w-full"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Verifying...
                </>
              ) : (
                "Verify OTP"
              )}
            </Button>
            <div className="text-center">
              <button
                onClick={handleResendOTP}
                disabled={loading}
                className="text-sm text-primary hover:underline"
              >
                Resend OTP
              </button>
            </div>
            <div className="text-center text-sm">
              <button
                onClick={() => setStep("form")}
                className="text-muted-foreground hover:underline"
              >
                Back to registration
              </button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-primary/5 to-accent/10 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Create Account</CardTitle>
          <CardDescription>
            Sign up to get started with AmaniQuery
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="name" className="text-sm font-medium">
                Full Name
              </label>
              <Input
                id="name"
                type="text"
                placeholder="John Doe"
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
                required
              />
            </div>
            <div>
              <label htmlFor="email" className="text-sm font-medium">
                Email
              </label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={formData.email}
                onChange={(e) =>
                  setFormData({ ...formData, email: e.target.value })
                }
                required
              />
            </div>
            <div>
              <label htmlFor="phone" className="text-sm font-medium">
                Phone Number
              </label>
              <Input
                id="phone"
                type="tel"
                placeholder="+254712345678 or 0712345678"
                value={formData.phone_number}
                onChange={(e) =>
                  setFormData({ ...formData, phone_number: e.target.value })
                }
                required
              />
              <p className="text-xs text-muted-foreground mt-1">
                Format: +254712345678, +2541XXXXXXX, 0712345678, or 01XXXXXXX
              </p>
            </div>
            <div>
              <label htmlFor="password" className="text-sm font-medium">
                Password
              </label>
              <Input
                id="password"
                type="password"
                placeholder="••••••••"
                value={formData.password}
                onChange={(e) =>
                  setFormData({ ...formData, password: e.target.value })
                }
                required
                minLength={8}
              />
              <p className="text-xs text-muted-foreground mt-1">
                Must be at least 8 characters with uppercase, lowercase, and digit
              </p>
            </div>
            <Button type="submit" disabled={loading} className="w-full">
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating Account...
                </>
              ) : (
                "Create Account"
              )}
            </Button>
          </form>
          <div className="mt-4 text-center text-sm">
            <span className="text-muted-foreground">Already have an account? </span>
            <Link href="/auth/signin" className="text-primary hover:underline">
              Sign in
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

