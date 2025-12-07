"use client"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import {
  Play,
  Pause,
  Volume2,
  VolumeX,
  Maximize2,
  Minimize2,
  Loader2,
  RefreshCw,
  AlertCircle,
  FileVideo,
  SkipBack,
  SkipForward,
} from "lucide-react"
import { Slider } from "@/components/ui/slider"
import { formatDuration } from "./media-api"

interface VideoPreviewProps {
  src: string
  poster?: string
  filename?: string
  transcript?: string
  frameUrls?: string[]
  className?: string
  showTranscript?: boolean
  autoPlay?: boolean
}

export function VideoPreview({
  src,
  poster,
  filename,
  transcript,
  frameUrls,
  className = "",
  showTranscript = true,
  autoPlay = false,
}: VideoPreviewProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(false)
  const [volume, setVolume] = useState(1)
  const [showControls, setShowControls] = useState(true)
  const [showFrames, setShowFrames] = useState(false)
  const controlsTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  useEffect(() => {
    const video = videoRef.current
    if (!video) return

    const handleLoadedMetadata = () => {
      setDuration(video.duration)
      setIsLoading(false)
    }

    const handleTimeUpdate = () => {
      setCurrentTime(video.currentTime)
    }

    const handleEnded = () => {
      setIsPlaying(false)
    }

    const handleError = () => {
      setError(true)
      setIsLoading(false)
    }

    const handleCanPlay = () => {
      setIsLoading(false)
    }

    const handlePlay = () => setIsPlaying(true)
    const handlePause = () => setIsPlaying(false)

    video.addEventListener("loadedmetadata", handleLoadedMetadata)
    video.addEventListener("timeupdate", handleTimeUpdate)
    video.addEventListener("ended", handleEnded)
    video.addEventListener("error", handleError)
    video.addEventListener("canplay", handleCanPlay)
    video.addEventListener("play", handlePlay)
    video.addEventListener("pause", handlePause)

    return () => {
      video.removeEventListener("loadedmetadata", handleLoadedMetadata)
      video.removeEventListener("timeupdate", handleTimeUpdate)
      video.removeEventListener("ended", handleEnded)
      video.removeEventListener("error", handleError)
      video.removeEventListener("canplay", handleCanPlay)
      video.removeEventListener("play", handlePlay)
      video.removeEventListener("pause", handlePause)
    }
  }, [src])

  // Handle fullscreen changes
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement)
    }

    document.addEventListener("fullscreenchange", handleFullscreenChange)
    return () => {
      document.removeEventListener("fullscreenchange", handleFullscreenChange)
    }
  }, [])

  // Auto-hide controls
  const resetControlsTimeout = () => {
    if (controlsTimeoutRef.current) {
      clearTimeout(controlsTimeoutRef.current)
    }
    setShowControls(true)
    if (isPlaying) {
      controlsTimeoutRef.current = setTimeout(() => {
        setShowControls(false)
      }, 3000)
    }
  }

  const togglePlay = () => {
    const video = videoRef.current
    if (!video) return

    if (isPlaying) {
      video.pause()
    } else {
      video.play()
    }
  }

  const toggleMute = () => {
    const video = videoRef.current
    if (!video) return

    video.muted = !isMuted
    setIsMuted(!isMuted)
  }

  const toggleFullscreen = async () => {
    const container = containerRef.current
    if (!container) return

    if (!document.fullscreenElement) {
      await container.requestFullscreen()
    } else {
      await document.exitFullscreen()
    }
  }

  const handleSeek = (value: number[]) => {
    const video = videoRef.current
    if (!video) return

    video.currentTime = value[0]
    setCurrentTime(value[0])
  }

  const handleVolumeChange = (value: number[]) => {
    const video = videoRef.current
    if (!video) return

    const newVolume = value[0]
    video.volume = newVolume
    setVolume(newVolume)
    setIsMuted(newVolume === 0)
  }

  const skip = (seconds: number) => {
    const video = videoRef.current
    if (!video) return

    video.currentTime = Math.max(0, Math.min(duration, video.currentTime + seconds))
  }

  const handleRetry = () => {
    setError(false)
    setIsLoading(true)
    const video = videoRef.current
    if (video) {
      video.load()
    }
  }

  if (error) {
    return (
      <div className={`flex flex-col items-center justify-center p-6 bg-muted/50 rounded-lg border border-white/10 aspect-video ${className}`}>
        <AlertCircle className="w-8 h-8 text-muted-foreground mb-2" />
        <p className="text-sm text-muted-foreground mb-2">Failed to load video</p>
        <Button variant="ghost" size="sm" onClick={handleRetry}>
          <RefreshCw className="w-4 h-4 mr-1" />
          Retry
        </Button>
      </div>
    )
  }

  return (
    <div className={`space-y-2 ${className}`}>
      {/* Header with filename */}
      {filename && (
        <div className="flex items-center gap-2">
          <FileVideo className="w-4 h-4 text-purple-400" />
          <span className="text-sm font-medium truncate">{filename}</span>
        </div>
      )}

      {/* Video container */}
      <div
        ref={containerRef}
        className="relative bg-black rounded-lg overflow-hidden group"
        onMouseMove={resetControlsTimeout}
        onMouseEnter={() => setShowControls(true)}
        onMouseLeave={() => isPlaying && setShowControls(false)}
      >
        <video
          ref={videoRef}
          src={src}
          poster={poster}
          preload="metadata"
          autoPlay={autoPlay}
          className="w-full aspect-video"
          onClick={togglePlay}
        />

        {/* Loading overlay */}
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/50">
            <Loader2 className="w-10 h-10 animate-spin text-white" />
          </div>
        )}

        {/* Play button overlay */}
        {!isPlaying && !isLoading && (
          <div 
            className="absolute inset-0 flex items-center justify-center cursor-pointer"
            onClick={togglePlay}
          >
            <div className="w-16 h-16 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center hover:bg-white/30 transition-colors">
              <Play className="w-8 h-8 text-white ml-1" />
            </div>
          </div>
        )}

        {/* Controls overlay */}
        <div
          className={`absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/80 to-transparent p-3 transition-opacity duration-200 ${
            showControls ? "opacity-100" : "opacity-0 pointer-events-none"
          }`}
        >
          {/* Progress bar */}
          <Slider
            value={[currentTime]}
            max={duration || 100}
            step={0.1}
            onValueChange={handleSeek}
            disabled={isLoading}
            className="w-full mb-2"
          />

          {/* Control buttons */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              {/* Play/Pause */}
              <Button
                variant="ghost"
                size="icon"
                onClick={togglePlay}
                className="h-8 w-8 text-white hover:bg-white/20"
              >
                {isPlaying ? (
                  <Pause className="w-4 h-4" />
                ) : (
                  <Play className="w-4 h-4 ml-0.5" />
                )}
              </Button>

              {/* Skip buttons */}
              <Button
                variant="ghost"
                size="icon"
                onClick={() => skip(-10)}
                className="h-8 w-8 text-white hover:bg-white/20"
              >
                <SkipBack className="w-4 h-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => skip(10)}
                className="h-8 w-8 text-white hover:bg-white/20"
              >
                <SkipForward className="w-4 h-4" />
              </Button>

              {/* Volume */}
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={toggleMute}
                  className="h-8 w-8 text-white hover:bg-white/20"
                >
                  {isMuted || volume === 0 ? (
                    <VolumeX className="w-4 h-4" />
                  ) : (
                    <Volume2 className="w-4 h-4" />
                  )}
                </Button>
                <Slider
                  value={[isMuted ? 0 : volume]}
                  max={1}
                  step={0.01}
                  onValueChange={handleVolumeChange}
                  className="w-16"
                />
              </div>

              {/* Time display */}
              <span className="text-xs text-white/80 ml-2">
                {formatDuration(currentTime)} / {formatDuration(duration)}
              </span>
            </div>

            {/* Fullscreen */}
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleFullscreen}
              className="h-8 w-8 text-white hover:bg-white/20"
            >
              {isFullscreen ? (
                <Minimize2 className="w-4 h-4" />
              ) : (
                <Maximize2 className="w-4 h-4" />
              )}
            </Button>
          </div>
        </div>
      </div>

      {/* Extracted frames preview */}
      {frameUrls && frameUrls.length > 0 && (
        <div className="space-y-2">
          <button
            onClick={() => setShowFrames(!showFrames)}
            className="text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            {showFrames ? "Hide" : "Show"} extracted frames ({frameUrls.length})
          </button>
          
          {showFrames && (
            <div className="flex gap-2 overflow-x-auto pb-2">
              {frameUrls.map((url, idx) => (
                <img
                  key={idx}
                  src={url}
                  alt={`Frame ${idx + 1}`}
                  className="h-16 w-auto rounded border border-white/10 flex-shrink-0"
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Transcript section */}
      {showTranscript && transcript && (
        <div className="p-3 bg-muted/50 rounded-lg border border-white/10">
          <p className="text-xs text-muted-foreground mb-1">Audio Transcript:</p>
          <p className="text-sm text-foreground/80 italic">
            &ldquo;{transcript}&rdquo;
          </p>
        </div>
      )}
    </div>
  )
}
