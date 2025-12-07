"use client"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { 
  Play, 
  Pause, 
  Volume2, 
  VolumeX, 
  Loader2, 
  RefreshCw, 
  AlertCircle,
  FileAudio
} from "lucide-react"
import { Slider } from "@/components/ui/slider"
import { formatDuration } from "./media-api"

interface AudioPreviewProps {
  src: string
  filename?: string
  transcript?: string
  className?: string
  showTranscript?: boolean
}

export function AudioPreview({ 
  src, 
  filename,
  transcript,
  className = "",
  showTranscript = true
}: AudioPreviewProps) {
  const audioRef = useRef<HTMLAudioElement>(null)
  const [isPlaying, setIsPlaying] = useState(false)
  const [isMuted, setIsMuted] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(false)
  const [volume, setVolume] = useState(1)
  const [showVolumeSlider, setShowVolumeSlider] = useState(false)

  useEffect(() => {
    const audio = audioRef.current
    if (!audio) return

    const handleLoadedMetadata = () => {
      setDuration(audio.duration)
      setIsLoading(false)
    }

    const handleTimeUpdate = () => {
      setCurrentTime(audio.currentTime)
    }

    const handleEnded = () => {
      setIsPlaying(false)
      setCurrentTime(0)
    }

    const handleError = () => {
      setError(true)
      setIsLoading(false)
    }

    const handleCanPlay = () => {
      setIsLoading(false)
    }

    audio.addEventListener("loadedmetadata", handleLoadedMetadata)
    audio.addEventListener("timeupdate", handleTimeUpdate)
    audio.addEventListener("ended", handleEnded)
    audio.addEventListener("error", handleError)
    audio.addEventListener("canplay", handleCanPlay)

    return () => {
      audio.removeEventListener("loadedmetadata", handleLoadedMetadata)
      audio.removeEventListener("timeupdate", handleTimeUpdate)
      audio.removeEventListener("ended", handleEnded)
      audio.removeEventListener("error", handleError)
      audio.removeEventListener("canplay", handleCanPlay)
    }
  }, [src])

  const togglePlay = () => {
    const audio = audioRef.current
    if (!audio) return

    if (isPlaying) {
      audio.pause()
    } else {
      audio.play()
    }
    setIsPlaying(!isPlaying)
  }

  const toggleMute = () => {
    const audio = audioRef.current
    if (!audio) return

    audio.muted = !isMuted
    setIsMuted(!isMuted)
  }

  const handleSeek = (value: number[]) => {
    const audio = audioRef.current
    if (!audio) return

    audio.currentTime = value[0]
    setCurrentTime(value[0])
  }

  const handleVolumeChange = (value: number[]) => {
    const audio = audioRef.current
    if (!audio) return

    const newVolume = value[0]
    audio.volume = newVolume
    setVolume(newVolume)
    setIsMuted(newVolume === 0)
  }

  const handleRetry = () => {
    setError(false)
    setIsLoading(true)
    const audio = audioRef.current
    if (audio) {
      audio.load()
    }
  }

  if (error) {
    return (
      <div className={`flex flex-col items-center justify-center p-4 bg-muted/50 rounded-lg border border-white/10 ${className}`}>
        <AlertCircle className="w-6 h-6 text-muted-foreground mb-2" />
        <p className="text-sm text-muted-foreground mb-2">Failed to load audio</p>
        <Button variant="ghost" size="sm" onClick={handleRetry}>
          <RefreshCw className="w-4 h-4 mr-1" />
          Retry
        </Button>
      </div>
    )
  }

  return (
    <div className={`bg-muted/50 rounded-lg border border-white/10 p-3 ${className}`}>
      <audio ref={audioRef} src={src} preload="metadata" />
      
      {/* Header with filename */}
      {filename && (
        <div className="flex items-center gap-2 mb-3">
          <FileAudio className="w-4 h-4 text-blue-400" />
          <span className="text-sm font-medium truncate">{filename}</span>
        </div>
      )}

      {/* Player controls */}
      <div className="flex items-center gap-3">
        {/* Play/Pause button */}
        <Button
          variant="ghost"
          size="icon"
          onClick={togglePlay}
          disabled={isLoading}
          className="h-10 w-10 rounded-full bg-primary/10 hover:bg-primary/20"
        >
          {isLoading ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : isPlaying ? (
            <Pause className="w-5 h-5" />
          ) : (
            <Play className="w-5 h-5 ml-0.5" />
          )}
        </Button>

        {/* Progress bar */}
        <div className="flex-1 space-y-1">
          <Slider
            value={[currentTime]}
            max={duration || 100}
            step={0.1}
            onValueChange={handleSeek}
            disabled={isLoading}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>{formatDuration(currentTime)}</span>
            <span>{formatDuration(duration)}</span>
          </div>
        </div>

        {/* Volume control */}
        <div 
          className="relative"
          onMouseEnter={() => setShowVolumeSlider(true)}
          onMouseLeave={() => setShowVolumeSlider(false)}
        >
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleMute}
            className="h-8 w-8"
          >
            {isMuted || volume === 0 ? (
              <VolumeX className="w-4 h-4" />
            ) : (
              <Volume2 className="w-4 h-4" />
            )}
          </Button>
          
          {showVolumeSlider && (
            <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 p-2 bg-background border border-white/10 rounded-lg shadow-lg">
              <Slider
                value={[isMuted ? 0 : volume]}
                max={1}
                step={0.01}
                orientation="vertical"
                onValueChange={handleVolumeChange}
                className="h-20"
              />
            </div>
          )}
        </div>
      </div>

      {/* Transcript section */}
      {showTranscript && transcript && (
        <div className="mt-3 pt-3 border-t border-white/10">
          <p className="text-xs text-muted-foreground mb-1">Transcript:</p>
          <p className="text-sm text-foreground/80 italic line-clamp-3">
            &ldquo;{transcript}&rdquo;
          </p>
        </div>
      )}
    </div>
  )
}
