"use client"

import * as React from "react"

import { cn } from "@/lib/utils"

interface SliderProps {
  value?: number[]
  defaultValue?: number[]
  max?: number
  min?: number
  step?: number
  disabled?: boolean
  orientation?: "horizontal" | "vertical"
  onValueChange?: (value: number[]) => void
  className?: string
}

const Slider = React.forwardRef<HTMLDivElement, SliderProps>(
  (
    {
      value,
      defaultValue = [0],
      max = 100,
      min = 0,
      step = 1,
      disabled = false,
      orientation = "horizontal",
      onValueChange,
      className,
      ...props
    },
    ref
  ) => {
    const [internalValue, setInternalValue] = React.useState(defaultValue)
    const currentValue = value ?? internalValue
    const trackRef = React.useRef<HTMLDivElement>(null)
    const isDragging = React.useRef(false)

    const isVertical = orientation === "vertical"

    const getPercentage = (val: number) => {
      return ((val - min) / (max - min)) * 100
    }

    const getValueFromPosition = (clientX: number, clientY: number) => {
      if (!trackRef.current) return currentValue[0]

      const rect = trackRef.current.getBoundingClientRect()
      let percentage: number

      if (isVertical) {
        percentage = 1 - (clientY - rect.top) / rect.height
      } else {
        percentage = (clientX - rect.left) / rect.width
      }

      percentage = Math.max(0, Math.min(1, percentage))
      let newValue = min + percentage * (max - min)

      // Snap to step
      newValue = Math.round(newValue / step) * step
      newValue = Math.max(min, Math.min(max, newValue))

      return newValue
    }

    const handlePointerDown = (e: React.PointerEvent) => {
      if (disabled) return
      isDragging.current = true
      e.currentTarget.setPointerCapture(e.pointerId)
      
      const newValue = getValueFromPosition(e.clientX, e.clientY)
      const newValues = [newValue]
      setInternalValue(newValues)
      onValueChange?.(newValues)
    }

    const handlePointerMove = (e: React.PointerEvent) => {
      if (!isDragging.current || disabled) return
      
      const newValue = getValueFromPosition(e.clientX, e.clientY)
      const newValues = [newValue]
      setInternalValue(newValues)
      onValueChange?.(newValues)
    }

    const handlePointerUp = () => {
      isDragging.current = false
    }

    const percentage = getPercentage(currentValue[0])

    return (
      <div
        ref={ref}
        className={cn(
          "relative flex touch-none select-none",
          isVertical ? "h-full w-2 flex-col" : "w-full h-2",
          disabled && "opacity-50 cursor-not-allowed",
          className
        )}
        {...props}
      >
        <div
          ref={trackRef}
          className={cn(
            "relative grow overflow-hidden rounded-full bg-primary/20 cursor-pointer",
            isVertical ? "w-full" : "h-full"
          )}
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerLeave={handlePointerUp}
        >
          {/* Filled track */}
          <div
            className="absolute bg-primary"
            style={
              isVertical
                ? {
                    width: "100%",
                    height: `${percentage}%`,
                    bottom: 0,
                  }
                : {
                    height: "100%",
                    width: `${percentage}%`,
                    left: 0,
                  }
            }
          />
        </div>
        
        {/* Thumb */}
        <div
          className={cn(
            "absolute block h-4 w-4 rounded-full border border-primary/50 bg-background shadow transition-colors",
            "focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring",
            disabled ? "cursor-not-allowed" : "cursor-grab active:cursor-grabbing",
            !disabled && "hover:bg-accent"
          )}
          style={
            isVertical
              ? {
                  bottom: `calc(${percentage}% - 8px)`,
                  left: "50%",
                  transform: "translateX(-50%)",
                }
              : {
                  left: `calc(${percentage}% - 8px)`,
                  top: "50%",
                  transform: "translateY(-50%)",
                }
          }
        />
      </div>
    )
  }
)

Slider.displayName = "Slider"

export { Slider }
