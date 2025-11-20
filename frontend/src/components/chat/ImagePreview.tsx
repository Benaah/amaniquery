"use client"

import { useState } from "react"
import Image from "next/image"
import { X, ZoomIn } from "lucide-react"
import { Button } from "@/components/ui/button"

interface ImagePreviewProps {
  src: string
  alt: string
  className?: string
}

export function ImagePreview({ src, alt, className = "" }: ImagePreviewProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [imageError, setImageError] = useState(false)

  if (imageError) {
    return (
      <div className={`flex items-center justify-center w-full h-48 bg-muted rounded-lg ${className}`}>
        <p className="text-sm text-muted-foreground">Failed to load image</p>
      </div>
    )
  }

  return (
    <>
      {/* Thumbnail */}
      <div
        className={`relative group cursor-pointer overflow-hidden rounded-lg border border-white/10 bg-white/5 hover:border-white/20 transition-all ${className}`}
        onClick={() => setIsOpen(true)}
      >
        <div className="relative w-full h-48">
          <Image
            src={src}
            alt={alt}
            fill
            className="object-cover"
            onError={() => setImageError(true)}
            sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
          />
          {/* Overlay on hover */}
          <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-center justify-center">
            <ZoomIn className="w-6 h-6 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        </div>
      </div>

      {/* Lightbox Modal */}
      {isOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-sm"
          onClick={() => setIsOpen(false)}
        >
          <div className="relative max-w-7xl max-h-[90vh] w-full h-full p-4 flex items-center justify-center">
            {/* Close button */}
            <Button
              variant="ghost"
              size="icon"
              className="absolute top-4 right-4 z-10 bg-black/50 hover:bg-black/70 text-white"
              onClick={() => setIsOpen(false)}
            >
              <X className="w-5 h-5" />
            </Button>

            {/* Full-size image */}
            <div
              className="relative w-full h-full max-w-full max-h-full"
              onClick={(e) => e.stopPropagation()}
            >
              <Image
                src={src}
                alt={alt}
                fill
                className="object-contain"
                onError={() => setImageError(true)}
                sizes="100vw"
              />
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

  return (
    <div className={`grid gap-2 ${images.length === 2 ? "grid-cols-2" : "grid-cols-2"} ${className}`}>
      {images.map((image, index) => (
        <ImagePreview
          key={index}
          src={image.src}
          alt={image.alt}
          className={index === 0 && images.length === 3 ? "row-span-2" : ""}
        />
      ))}
    </div>
  )
}

