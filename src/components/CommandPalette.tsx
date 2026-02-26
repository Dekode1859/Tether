import { useState, useEffect } from "react"
import { invoke } from "@tauri-apps/api/core"
import { listen } from "@tauri-apps/api/event"
import { Mic, Network, Search, Loader2, Copy, Check } from "lucide-react"
import {
  Command,
  CommandInput,
  CommandList,
  CommandEmpty,
  CommandGroup,
  CommandItem,
  CommandSeparator,
} from "@/components/ui/command"

type RunningState = "idle" | "recording" | "thinking" | "weaving"

export default function CommandPalette() {
  const [inputValue, setInputValue] = useState("")
  const [runningState, setRunningState] = useState<RunningState>("idle")
  const [result, setResult] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)

  useEffect(() => {
    const unlistenRecordingToggle = listen("hotkey-recording-toggle", () => {
      if (runningState === "recording") {
        handleStopRecording()
      } else if (runningState === "idle") {
        handleStartRecording()
      }
    })

    const unlistenEngineStarted = listen("engine-started", () => {
      setRunningState("recording")
    })

    const unlistenEngineStopped = listen("engine-stopped", () => {
      setRunningState("idle")
      setRecordingTime(0)
    })

    return () => {
      unlistenRecordingToggle.then(fn => fn())
      unlistenEngineStarted.then(fn => fn())
      unlistenEngineStopped.then(fn => fn())
    }
  }, [runningState])

  useEffect(() => {
    let interval: number | undefined
    if (runningState === "recording") {
      interval = window.setInterval(() => {
        setRecordingTime((prev) => prev + 1)
      }, 1000)
    }
    return () => {
      if (interval) clearInterval(interval)
    }
  }, [runningState])

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`
  }

  const handleStartRecording = async () => {
    try {
      await invoke("start_spool")
      setRunningState("recording")
    } catch (error) {
      console.error("Failed to start recording:", error)
    }
  }

  const handleStopRecording = async () => {
    try {
      await invoke("stop_spool")
      setRunningState("idle")
      setRecordingTime(0)
    } catch (error) {
      console.error("Failed to stop recording:", error)
    }
  }

  const handleWeave = async () => {
    try {
      setRunningState("weaving")
      const result = await invoke<string>("run_weave")
      setResult(result)
    } catch (error) {
      console.error("Failed to weave:", error)
      setResult(`Error: ${error}`)
    } finally {
      setRunningState("idle")
    }
  }

  const handleAsk = async (query: string) => {
    if (!query.trim()) return
    try {
      setRunningState("thinking")
      const result = await invoke<string>("run_ask", { query })
      setResult(result)
    } catch (error) {
      console.error("Failed to ask:", error)
      setResult(`Error: ${error}`)
    } finally {
      setRunningState("idle")
    }
  }

  const handleCopy = async () => {
    if (result) {
      await navigator.clipboard.writeText(result)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    }
  }

  const isAskCommand = inputValue.toLowerCase().startsWith("ask:")

  return (
    <div className="h-screen w-screen bg-transparent p-4 flex items-center justify-center">
      <Command className="rounded-xl border border-slate-800 bg-slate-950 text-slate-50 shadow-2xl max-w-2xl w-full overflow-hidden">
        <CommandInput
          placeholder="Type a command or ask your vault..."
          value={inputValue}
          onValueChange={setInputValue}
          onKeyDown={(e) => {
            if (e.key === "Enter" && isAskCommand) {
              const query = inputValue.slice(4).trim()
              handleAsk(query)
            }
          }}
        />
        <CommandList>
          {runningState === "idle" && !result && (
            <>
              <CommandEmpty>No results found.</CommandEmpty>
              <CommandGroup heading="Core Actions">
                <CommandItem onSelect={handleStartRecording}>
                  <Mic className="mr-2 h-4 w-4 text-red-400" />
                  Tether: Spool (Record)
                </CommandItem>
                <CommandItem onSelect={handleWeave}>
                  <Network className="mr-2 h-4 w-4 text-cyan-400" />
                  Tether: Weave (Build Graph)
                </CommandItem>
              </CommandGroup>
              <CommandSeparator />
              <CommandGroup heading="Quick Actions">
                <CommandItem onSelect={() => setInputValue("Ask: ")}>
                  <Search className="mr-2 h-4 w-4 text-slate-400" />
                  Ask: Your question...
                </CommandItem>
              </CommandGroup>
            </>
          )}

          {runningState === "recording" && (
            <div className="p-4 flex items-center justify-center space-x-3">
              <div className="h-3 w-3 bg-red-500 rounded-full animate-pulse" />
              <span className="text-slate-200 font-mono">
                Recording... {formatTime(recordingTime)}
              </span>
              <button
                onClick={handleStopRecording}
                className="ml-4 px-3 py-1 bg-slate-800 hover:bg-slate-700 rounded text-sm"
              >
                Stop
              </button>
            </div>
          )}

          {runningState === "thinking" && (
            <div className="p-4 flex items-center justify-center space-x-3">
              <Loader2 className="h-5 w-5 animate-spin text-cyan-400" />
              <span className="text-slate-400">Thinking...</span>
            </div>
          )}

          {runningState === "weaving" && (
            <div className="p-4 flex items-center justify-center space-x-3">
              <Loader2 className="h-5 w-5 animate-spin text-cyan-400" />
              <span className="text-slate-400">Weaving thoughts...</span>
            </div>
          )}

          {result && runningState === "idle" && (
            <div className="p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-slate-400">Result:</span>
                <button
                  onClick={handleCopy}
                  className="flex items-center space-x-1 text-xs text-slate-400 hover:text-slate-200"
                >
                  {copied ? (
                    <>
                      <Check className="h-3 w-3" />
                      <span>Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="h-3 w-3" />
                      <span>Copy</span>
                    </>
                  )}
                </button>
              </div>
              <div className="bg-slate-900 rounded-lg p-3 text-sm whitespace-pre-wrap">
                {result}
              </div>
              <button
                onClick={() => {
                  setResult(null)
                  setInputValue("")
                }}
                className="mt-3 w-full py-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm"
              >
                Back
              </button>
            </div>
          )}
        </CommandList>
      </Command>
    </div>
  )
}
