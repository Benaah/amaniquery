"use client"

import { useState, useEffect } from "react"
import Image from "next/image"
import { X, ZoomIn, Loader2, RefreshCw, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"

interface ImagePreviewProps {
  src: string
  alt: string
  className?: string
}

export function ImagePreview({ src, alt, className = "" }: ImagePreviewProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [imageError, setImageError] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [lightboxLoading, setLightboxLoading] = useState(true)
  const [lightboxError, setLightboxError] = useState(false)
  const [retryKey, setRetryKey] = useState(0)

  // Handle ESC key to close modal
  useEffect(() => {
    if (!isOpen) return

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setIsOpen(false)
      }
    }

    // Prevent body scroll when modal is open
    document.body.style.overflow = "hidden"

    window.addEventListener("keydown", handleEscape)

    return () => {
      window.removeEventListener("keydown", handleEscape)
      document.body.style.overflow = "unset"
    }
  }, [isOpen])

  const handleImageLoad = () => {
    setIsLoading(false)
  }

  const handleImageError = () => {
    setImageError(true)
    setIsLoading(false)
  }

  const handleLightboxImageLoad = () => {
    setLightboxLoading(false)
  }

  const handleLightboxImageError = () => {
    setLightboxError(true)
    setLightboxLoading(false)
  }

  const handleRetry = () => {
    setImageError(false)
    setIsLoading(true)
    setLightboxError(false)
    setLightboxLoading(true)
    // Force reload by updating retry key which will change the src
    setRetryKey(prev => prev + 1)
  }

  // Add cache-busting parameter for retry
  const imageSrc = retryKey > 0 
    ? (src.includes("?") ? `${src}&retry=${retryKey}` : `${src}?retry=${retryKey}`)
    : src

  const handleOpen = () => {
    setIsOpen(true)
    setLightboxLoading(true)
    setLightboxError(false)
  }

  const handleClose = () => {
    setIsOpen(false)
  }

  // Error state for thumbnail
  if (imageError) {
    return (
      <div className={`flex flex-col items-center justify-center w-full h-32 md:h-48 bg-muted/50 rounded-lg border border-white/10 ${className}`}>
        <AlertCircle className="w-5 h-5 md:w-6 md:h-6 text-muted-foreground mb-2" />
        <p className="text-xs md:text-sm text-muted-foreground mb-2 px-2 text-center">Failed to load image</p>
        <Button
          variant="ghost"
          size="sm"
          onClick={handleRetry}
          className="h-7 md:h-8 text-xs"
        >
          <RefreshCw className="w-3 h-3 md:w-4 md:h-4 mr-1" />
          Retry
        </Button>
      </div>
    )
  }

  return (
    <>
      {/* Thumbnail */}
      <div
        className={`relative group cursor-pointer overflow-hidden rounded-lg border border-white/10 bg-white/5 hover:border-white/20 transition-all ${className}`}
        onClick={handleOpen}
      >
        <div className="relative w-full h-32 md:h-48 min-h-[128px]">
          {isLoading && (
            <div className="absolute inset-0 flex items-center justify-center bg-muted/30">
              <Loader2 className="w-5 h-5 md:w-6 md:h-6 text-muted-foreground animate-spin" />
            </div>
          )}
          <Image
            key={retryKey}
            src={imageSrc}
            alt={alt}
            fill
            className={`object-cover transition-opacity duration-300 ${isLoading ? "opacity-0" : "opacity-100"}`}
            onLoad={handleImageLoad}
            onError={handleImageError}
            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
            unoptimized={imageSrc.startsWith("data:") || imageSrc.startsWith("blob:")}
          />
          {/* Overlay on hover */}
          <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-center justify-center">
            <ZoomIn className="w-5 h-5 md:w-6 md:h-6 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        </div>
      </div>

      {/* Lightbox Modal */}
      {isOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/95 backdrop-blur-sm"
          onClick={handleClose}
        >
          <div className="relative w-full h-full p-2 md:p-4 flex items-center justify-center">
            {/* Close button */}
            <Button
              variant="ghost"
              size="icon"
              className="absolute top-2 right-2 md:top-4 md:right-4 z-10 h-9 w-9 md:h-10 md:w-10 bg-black/70 hover:bg-black/90 text-white rounded-full"
              onClick={handleClose}
              aria-label="Close image"
            >
              <X className="w-5 h-5 md:w-6 md:h-6" />
            </Button>

            {/* Full-size image */}
            <div
              className="relative w-full h-full max-w-[95vw] max-h-[95vh] md:max-w-[90vw] md:max-h-[90vh] flex items-center justify-center"
              onClick={(e) => e.stopPropagation()}
            >
              {lightboxLoading && (
                <div className="absolute inset-0 flex items-center justify-center bg-black/50">
                  <Loader2 className="w-8 h-8 md:w-10 md:h-10 text-white animate-spin" />
                </div>
              )}
              {lightboxError ? (
                <div className="flex flex-col items-center justify-center p-8 bg-black/50 rounded-lg">
                  <AlertCircle className="w-8 h-8 md:w-10 md:h-10 text-white mb-4" />
                  <p className="text-sm md:text-base text-white mb-4 text-center">Failed to load image</p>
                  <Button
                    variant="default"
                    size="sm"
                    onClick={handleRetry}
                    className="bg-white text-black hover:bg-white/90"
                  >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Retry
                  </Button>
                </div>
              ) : (
                <Image
                  key={retryKey}
                  src={imageSrc}
                  alt={alt}
                  fill
                  className={`object-contain transition-opacity duration-300 ${lightboxLoading ? "opacity-0" : "opacity-100"}`}
                  onLoad={handleLightboxImageLoad}
                  onError={handleLightboxImageError}
                  sizes="100vw"
                  unoptimized={imageSrc.startsWith("data:") || imageSrc.startsWith("blob:")}
                  priority
                />
              )}
            </div>
          </div>
        </div>
      )}
    </>
  )
}

interface ImagePreviewGridProps {
  images: Array<{ src: string; alt: string }>
  className?: string
}

export function ImagePreviewGrid({ images, className = "" }: ImagePreviewGridProps) {
  if (images.length === 0) return null

  if (images.length === 1) {
    return <ImagePreview src={images[0].src} alt={images[0].alt} className={className} />
  }

  // Responsive grid layout
  const getGridClasses = () => {
    if (images.length === 2) {
      return "grid-cols-1 sm:grid-cols-2"
    } else if (images.length === 3) {
      return "grid-cols-1 sm:grid-cols-2"
    } else if (images.length === 4) {
      return "grid-cols-1 sm:grid-cols-2"
    } else {
      return "grid-cols-1 sm:grid-cols-2 md:grid-cols-3"
    }
  }

  return (
    <div className={`grid gap-2 ${getGridClasses()} ${className}`}>
      {images.map((image, index) => {
        // Special layout for 3 images: first image spans 2 rows on larger screens
        const rowSpanClass = index === 0 && images.length === 3 
          ? "sm:row-span-2" 
          : ""
        return (
          <ImagePreview
            key={index}
            src={image.src}
            alt={image.alt}
            className={rowSpanClass}
          />
        )
      })}
    </div>
  )
}

