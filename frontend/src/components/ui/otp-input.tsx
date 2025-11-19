"use client"

import { useState, useRef, useEffect } from "react"
import { Input } from "./input"

interface OTPInputProps {
  length?: number
  value: string
  onChange: (value: string) => void
  onComplete?: (value: string) => void
  disabled?: boolean
  className?: string
}

export function OTPInput({
  length = 6,
  value,
  onChange,
  onComplete,
  disabled = false,
  className = ""
}: OTPInputProps) {
  const [otp, setOtp] = useState<string[]>(new Array(length).fill(""))
  const inputRefs = useRef<(HTMLInputElement | null)[]>([])
  const prevValueRef = useRef<string>(value)

  useEffect(() => {
    // Only update if value actually changed to avoid cascading renders
    if (prevValueRef.current !== value) {
      prevValueRef.current = value
      
      // Defer state update to next tick to avoid synchronous setState in effect
      queueMicrotask(() => {
        if (value && value.length === length) {
          setOtp(value.split(""))
        } else if (!value) {
          setOtp(new Array(length).fill(""))
        }
      })
    }
  }, [value, length])

  const handleChange = (index: number, val: string) => {
    if (disabled) return

    // Only allow digits
    const digit = val.replace(/\D/g, "")
    if (digit.length > 1) return

    const newOtp = [...otp]
    newOtp[index] = digit
    setOtp(newOtp)

    const otpString = newOtp.join("")
    onChange(otpString)

    // Auto-focus next input
    if (digit && index < length - 1) {
      inputRefs.current[index + 1]?.focus()
    }

    // Call onComplete when all digits are filled
    if (otpString.length === length && onComplete) {
      onComplete(otpString)
    }
  }

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Backspace" && !otp[index] && index > 0) {
      inputRefs.current[index - 1]?.focus()
    } else if (e.key === "ArrowLeft" && index > 0) {
      inputRefs.current[index - 1]?.focus()
    } else if (e.key === "ArrowRight" && index < length - 1) {
      inputRefs.current[index + 1]?.focus()
    }
  }

  const handlePaste = (e: React.ClipboardEvent) => {
    e.preventDefault()
    const pastedData = e.clipboardData.getData("text").replace(/\D/g, "").slice(0, length)
    
    if (pastedData.length > 0) {
      const newOtp = [...otp]
      for (let i = 0; i < pastedData.length && i < length; i++) {
        newOtp[i] = pastedData[i]
      }
      setOtp(newOtp)
      
      const otpString = newOtp.join("")
      onChange(otpString)
      
      // Focus the next empty input or the last one
      const nextIndex = Math.min(pastedData.length, length - 1)
      inputRefs.current[nextIndex]?.focus()
      
      if (otpString.length === length && onComplete) {
        onComplete(otpString)
      }
    }
  }

  return (
    <div className={`flex gap-2 justify-center ${className}`}>
      {otp.map((digit, index) => (
        <Input
          key={index}
          ref={(el) => {
            inputRefs.current[index] = el
          }}
          type="text"
          inputMode="numeric"
          maxLength={1}
          value={digit}
          onChange={(e) => handleChange(index, e.target.value)}
          onKeyDown={(e) => handleKeyDown(index, e)}
          onPaste={handlePaste}
          disabled={disabled}
          className="w-12 h-12 text-center text-lg font-semibold"
          autoFocus={index === 0}
        />
      ))}
    </div>
  )
}

