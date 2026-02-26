import { useState, useEffect } from "react"
import { listen } from "@tauri-apps/api/event"

export default function RecordingWidget() {
  const [recordingTime, setRecordingTime] = useState(0)

  useEffect(() => {
    const unlisten = listen("engine-stopped", () => {
      setRecordingTime(0)
    })

    return () => {
      unlisten.then(fn => fn())
    }
  }, [])

  useEffect(() => {
    const interval = window.setInterval(() => {
      setRecordingTime((prev) => prev + 1)
    }, 1000)

    return () => clearInterval(interval)
  }, [])

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`
  }

  return (
    <div className="h-screen w-screen bg-transparent flex items-center justify-center p-2">
      <div className="flex items-center space-x-3 bg-slate-900/90 border border-slate-700/50 rounded-full px-4 py-2 shadow-lg backdrop-blur-sm">
        <div className="h-3 w-3 bg-red-500 rounded-full animate-pulse" />
        <span className="text-slate-200 text-sm font-medium font-mono">
          {formatTime(recordingTime)}
        </span>
      </div>
    </div>
  )
}
