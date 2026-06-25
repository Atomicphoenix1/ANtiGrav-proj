"use client"

import { useEffect, useRef, useState } from "react"
import { Play, Pause } from "lucide-react"

interface AudioPlayerProps {
  /** Audio source URL */
  src: string
  /** Initial playback position in seconds */
  startTime?: number
  /** Whether playback should be active */
  isPlaying?: boolean
}

function formatTime(seconds: number) {
  if (!Number.isFinite(seconds) || seconds < 0) seconds = 0
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, "0")}`
}

export function AudioPlayer({ src, startTime = 0, isPlaying = false }: AudioPlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null)
  const [playing, setPlaying] = useState(isPlaying)
  const [currentTime, setCurrentTime] = useState(startTime)
  const [duration, setDuration] = useState(0)
  
  // NEW: State to track if the browser has downloaded the file duration
  const [isMetadataLoaded, setIsMetadataLoaded] = useState(false)

  // Sync the incoming isPlaying prop
  useEffect(() => {
    setPlaying(isPlaying)
  }, [isPlaying])

  // Reset metadata lock if the source file changes
  useEffect(() => {
    setIsMetadataLoaded(false)
    setDuration(0)
  }, [src])

  // Apply the startTime prop ONLY after metadata is loaded
  useEffect(() => {
    const audio = audioRef.current
    if (audio && isMetadataLoaded) {
      // 2-second pre-roll cushion so the sentence beginning isn't clipped
      const cushionedTime = Math.max(0, startTime - 2)
      // Force precise seeking — fall back to currentTime if fastSeek absent
      if ('fastSeek' in audio) {
        audio.fastSeek(cushionedTime)
      } else {
        audio.currentTime = cushionedTime
      }
      setCurrentTime(cushionedTime)
    }
  }, [startTime, isMetadataLoaded])

  // Drive play/pause ONLY after metadata is loaded
  useEffect(() => {
    const audio = audioRef.current
    if (!audio || !isMetadataLoaded) return
    
    if (playing) {
      audio.play().catch(() => setPlaying(false))
    } else {
      audio.pause()
    }
  }, [playing, isMetadataLoaded])

  const togglePlay = () => setPlaying((prev) => !prev)

  const handleSeek = (event: React.ChangeEvent<HTMLInputElement>) => {
    const audio = audioRef.current
    const value = Number(event.target.value)
    if (audio) audio.currentTime = value
    setCurrentTime(value)
  }

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0

  return (
    <div
      dir="rtl"
      className="flex w-full items-center gap-4 rounded-2xl border border-border bg-card/80 px-5 py-3.5 shadow-sm backdrop-blur-sm"
    >
      <audio
        ref={audioRef}
        src={src}
        preload="metadata"
        onLoadedMetadata={(e) => {
          setDuration(e.currentTarget.duration)
          setIsMetadataLoaded(true) // UNLOCK: Now the effects can seek and play
        }}
        onTimeUpdate={(e) => setCurrentTime(e.currentTarget.currentTime)}
        onEnded={() => setPlaying(false)}
      />

      {/* Play / Pause */}
      <button
        type="button"
        onClick={togglePlay}
        aria-label={playing ? "إيقاف مؤقت" : "تشغيل"}
        className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground transition-transform duration-150 hover:scale-105 active:scale-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-card"
      >
        {playing ? (
          <Pause className="h-5 w-5 fill-current" aria-hidden="true" />
        ) : (
          <Play className="h-5 w-5 fill-current translate-x-[-1px]" aria-hidden="true" />
        )}
      </button>

      {/* Timeline + times */}
      <div className="flex min-w-0 flex-1 flex-col gap-1.5">
        <div className="relative flex h-4 items-center">
          {/* Track */}
          <div className="absolute inset-x-0 h-1.5 rounded-full bg-muted" />
          {/* Filled portion (RTL: fill from the right) */}
          <div
            className="absolute right-0 h-1.5 rounded-full bg-primary"
            style={{ width: `${progress}%` }}
          />
          <input
            type="range"
            min={0}
            max={duration || 0}
            step={0.1}
            value={currentTime}
            onChange={handleSeek}
            aria-label="شريط التقدم"
            className="absolute inset-x-0 m-0 h-4 w-full cursor-pointer appearance-none bg-transparent
              [&::-webkit-slider-thumb]:h-3.5 [&::-webkit-slider-thumb]:w-3.5 [&::-webkit-slider-thumb]:appearance-none
              [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-primary
              [&::-webkit-slider-thumb]:shadow-sm [&::-webkit-slider-thumb]:transition-transform
              [&::-webkit-slider-thumb]:hover:scale-125
              [&::-moz-range-thumb]:h-3.5 [&::-moz-range-thumb]:w-3.5 [&::-moz-range-thumb]:appearance-none
              [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:border-0 [&::-moz-range-thumb]:bg-primary"
          />
        </div>

        <div className="flex items-center justify-between font-mono text-xs tabular-nums text-muted-foreground">
          <span>{formatTime(currentTime)}</span>
          <span>{formatTime(duration)}</span>
        </div>
      </div>
    </div>
  )
}

export default AudioPlayer