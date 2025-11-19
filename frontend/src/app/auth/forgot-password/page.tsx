"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { apiClient } from "@/lib/api-client"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { OTPInput } from "@/components/ui/otp-input"
import { toast } from "sonner"
import { Loader2 } from "lucide-react"

export default function ForgotPasswordPage() {
  const [step, setStep] = useState<"email" | "otp" | "reset">("email")
  const [loading, setLoading] = useState(false)
  const [email, setEmail] = useState("")
  const [phoneNumber, setPhoneNumber] = useState("")
  const [otp, setOtp] = useState("")
  const [resetToken, setResetToken] = useState("")
  const [newPassword, setNewPassword] = useState("")
  const router = useRouter()

  const handleEmailSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      // Request password reset (this will send OTP to user's phone)
      await apiClient.post("/api/v1/auth/password/reset-request", {
        email: email,
      })

      // Get user's phone number (we'll need to fetch it or it should be in response)
      // For now, we'll ask user to enter phone number
      setStep("otp")
      toast.success("Please enter your phone number to receive OTP")
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : "Failed to request password reset"
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
        purpose: "password_reset",
      })

      // Get password reset token (in real implementation, this would come from the backend)
      // For now, we'll use a placeholder
      await apiClient.post("/api/v1/auth/password/reset-request", {
        email: email,
      })

      setResetToken("verified") // In production, get actual token
      setStep("reset")
      toast.success("OTP verified. Please set your new password.")
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : "OTP verification failed"
      toast.error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const handlePasswordReset = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      // Reset password with token and OTP verification
      await apiClient.post("/api/v1/auth/password/reset", {
        token: resetToken,
        new_password: newPassword,
      })

      toast.success("Password reset successfully! Please sign in.")
      router.push("/auth/signin")
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : "Password reset failed"
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
        purpose: "password_reset",
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
            <CardTitle>Verify OTP</CardTitle>
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
                onClick={() => setStep("email")}
                className="text-muted-foreground hover:underline"
              >
                Back
              </button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (step === "reset") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-primary/5 to-accent/10 p-4">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle>Reset Password</CardTitle>
            <CardDescription>Enter your new password</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handlePasswordReset} className="space-y-4">
              <div>
                <label htmlFor="newPassword" className="text-sm font-medium">
                  New Password
                </label>
                <Input
                  id="newPassword"
                  type="password"
                  placeholder="••••••••"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
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
                    Resetting...
                  </>
                ) : (
                  "Reset Password"
                )}
              </Button>
            </form>
            <div className="mt-4 text-center text-sm">
              <Link href="/auth/signin" className="text-primary hover:underline">
                Back to sign in
              </Link>
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
          <CardTitle>Forgot Password</CardTitle>
          <CardDescription>
            Enter your email and phone number to reset your password
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleEmailSubmit} className="space-y-4">
            <div>
              <label htmlFor="email" className="text-sm font-medium">
                Email
              </label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
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
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                required
              />
              <p className="text-xs text-muted-foreground mt-1">
                Format: +254712345678, +2541XXXXXXX, 0712345678, or 01XXXXXXX
              </p>
            </div>
            <Button type="submit" disabled={loading} className="w-full">
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Sending OTP...
                </>
              ) : (
                "Send OTP"
              )}
            </Button>
          </form>
          <div className="mt-4 text-center text-sm">
            <Link href="/auth/signin" className="text-primary hover:underline">
              Back to sign in
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

