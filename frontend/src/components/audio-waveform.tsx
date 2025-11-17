"use client"

import { useEffect, useRef } from "react"
import { cn } from "@/lib/utils"

interface AudioWaveformProps {
  audioStream: MediaStream | null
  isActive: boolean
  className?: string
  barCount?: number
  barColor?: string
  activeBarColor?: string
}

// Helper function to get CSS color value from CSS custom properties
function getColorValue(colorInput: string, fallback: string): string {
  // If it's already a valid color (hex, rgb, hsl, named color), return it
  if (/^#([0-9A-F]{3}){1,2}$/i.test(colorInput) || 
      /^rgb\(|^rgba\(|^hsl\(|^hsla\(/.test(colorInput) ||
      /^(red|blue|green|yellow|orange|purple|pink|black|white|gray|grey)$/i.test(colorInput)) {
    return colorInput
  }
  
  // Get color from CSS custom properties using a test element (most reliable method)
  if (typeof window !== "undefined" && typeof document !== "undefined") {
    try {
      if (colorInput.includes("primary")) {
        const opacity = colorInput.includes("/30") ? "0.3" : "1"
        
        // Create a test element with the Tailwind class to get computed color
        const testEl = document.createElement("div")
        testEl.className = "bg-primary"
        testEl.style.position = "absolute"
        testEl.style.visibility = "hidden"
        testEl.style.pointerEvents = "none"
        testEl.style.width = "1px"
        testEl.style.height = "1px"
        document.body.appendChild(testEl)
        
        const computed = getComputedStyle(testEl)
        const bgColor = computed.backgroundColor
        document.body.removeChild(testEl)
        
        // If we got a valid color, apply opacity if needed
        if (bgColor && bgColor !== "rgba(0, 0, 0, 0)" && bgColor !== "transparent") {
          // Handle RGB colors
          if (bgColor.startsWith("rgb(")) {
            const rgbMatch = bgColor.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/)
            if (rgbMatch) {
              return `rgba(${rgbMatch[1]}, ${rgbMatch[2]}, ${rgbMatch[3]}, ${opacity})`
            }
          }
          // Handle RGBA colors - replace existing alpha
          if (bgColor.startsWith("rgba(")) {
            const rgbaMatch = bgColor.match(/rgba\((\d+),\s*(\d+),\s*(\d+),\s*[\d.]+\)/)
            if (rgbaMatch) {
              return `rgba(${rgbaMatch[1]}, ${rgbaMatch[2]}, ${rgbaMatch[3]}, ${opacity})`
            }
          }
          // Handle HSL colors
          if (bgColor.startsWith("hsl(")) {
            const hslMatch = bgColor.match(/hsl\((\d+),\s*([\d.]+)%,\s*([\d.]+)%\)/)
            if (hslMatch) {
              return `hsla(${hslMatch[1]}, ${hslMatch[2]}%, ${hslMatch[3]}%, ${opacity})`
            }
          }
          // Handle HSLA colors - replace existing alpha
          if (bgColor.startsWith("hsla(")) {
            const hslaMatch = bgColor.match(/hsla\((\d+),\s*([\d.]+)%,\s*([\d.]+)%,\s*[\d.]+\)/)
            if (hslaMatch) {
              return `hsla(${hslaMatch[1]}, ${hslaMatch[2]}%, ${hslaMatch[3]}%, ${opacity})`
            }
          }
          // For other formats, return as-is if opacity is 1, otherwise try to convert
          if (opacity === "1") {
            return bgColor
          }
        }
      }
    } catch (e) {
      // Fall through to fallback
    }
  }
  
  return fallback
}

export function AudioWaveform({
  audioStream,
  isActive,
  className,
  barCount = 40,
  barColor = "bg-primary/30",
  activeBarColor = "bg-primary",
}: AudioWaveformProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const animationFrameRef = useRef<number | null>(null)
  const analyserRef = useRef<AnalyserNode | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const isAnalyzingRef = useRef(false)

  useEffect(() => {
    if (!audioStream || !canvasRef.current) {
      isAnalyzingRef.current = false
      return
    }

    const canvas = canvasRef.current
    const ctx = canvas.getContext("2d")
    if (!ctx) return

    // Set canvas size
    const rect = canvas.getBoundingClientRect()
    canvas.width = rect.width * window.devicePixelRatio
    canvas.height = rect.height * window.devicePixelRatio
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio)

    // Create audio context and analyser
    try {
      const AudioContextClass = (window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext) as typeof AudioContext
      const audioContext = new AudioContextClass()
      const analyser = audioContext.createAnalyser()
      const source = audioContext.createMediaStreamSource(audioStream)

      analyser.fftSize = 256
      analyser.smoothingTimeConstant = 0.8
      source.connect(analyser)

      analyserRef.current = analyser
      audioContextRef.current = audioContext
      isAnalyzingRef.current = true

      const bufferLength = analyser.frequencyBinCount
      const dataArray = new Uint8Array(bufferLength)

      // Get actual color values from CSS
      const resolvedBarColor = getColorValue(barColor, "rgba(59, 130, 246, 0.3)") // blue-500 with 30% opacity
      const resolvedActiveColor = getColorValue(activeBarColor, "rgb(59, 130, 246)") // blue-500

      const draw = () => {
        if (!isActive || !isAnalyzingRef.current) {
          // Draw flat line when not active
          ctx.clearRect(0, 0, canvas.width / window.devicePixelRatio, canvas.height / window.devicePixelRatio)
          ctx.fillStyle = resolvedBarColor
          const barWidth = (canvas.width / window.devicePixelRatio) / barCount
          const barHeight = 4
          const centerY = (canvas.height / window.devicePixelRatio) / 2

          for (let i = 0; i < barCount; i++) {
            const x = i * barWidth
            ctx.fillRect(x, centerY - barHeight / 2, barWidth - 2, barHeight)
          }
          animationFrameRef.current = requestAnimationFrame(draw)
          return
        }

        analyser.getByteFrequencyData(dataArray)

        ctx.clearRect(0, 0, canvas.width / window.devicePixelRatio, canvas.height / window.devicePixelRatio)

        const barWidth = (canvas.width / window.devicePixelRatio) / barCount
        const centerY = (canvas.height / window.devicePixelRatio) / 2
        const maxBarHeight = (canvas.height / window.devicePixelRatio) * 0.8

        // Sample data points for visualization
        const step = Math.floor(bufferLength / barCount)

        for (let i = 0; i < barCount; i++) {
          const dataIndex = i * step
          const barHeight = (dataArray[dataIndex] / 255) * maxBarHeight
          const x = i * barWidth

          // Draw bar
          const gradient = ctx.createLinearGradient(
            x,
            centerY - barHeight / 2,
            x,
            centerY + barHeight / 2
          )
          gradient.addColorStop(0, resolvedActiveColor)
          gradient.addColorStop(1, resolvedBarColor)

          ctx.fillStyle = gradient
          ctx.fillRect(x, centerY - barHeight / 2, barWidth - 2, barHeight || 2)
        }

        animationFrameRef.current = requestAnimationFrame(draw)
      }

      draw()
    } catch (error) {
      console.error("Error setting up audio visualization:", error)
      isAnalyzingRef.current = false
    }

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current)
      }
      if (audioContextRef.current) {
        audioContextRef.current.close().catch(console.error)
      }
      isAnalyzingRef.current = false
    }
  }, [audioStream, isActive, barCount, barColor, activeBarColor])

  return (
    <div className={cn("w-full h-16 bg-muted/30 rounded-lg overflow-hidden", className)}>
      <canvas
        ref={canvasRef}
        className="w-full h-full block"
      />
    </div>
  )
}

