import { useState, useEffect } from "react"
import { invoke } from "@tauri-apps/api/core"
import { listen } from "@tauri-apps/api/event"
import { Mic, Network, Search, Loader2, Copy, Check, Download, AlertCircle } from "lucide-react"
import {
  Command,
  CommandInput,
  CommandList,
  CommandEmpty,
  CommandGroup,
  CommandItem,
  CommandSeparator,
} from "@/components/ui/command"

type RunningState = "idle" | "recording" | "transcribing" | "thinking" | "weaving"

type OllamaStatus = {
  status: "available" | "not_installed" | "not_running"
  model: string
  error?: string
}

export default function CommandPalette() {
  const [inputValue, setInputValue] = useState("")
  const [runningState, setRunningState] = useState<RunningState>("idle")
  const [result, setResult] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)
  const [showOllamaDialog, setShowOllamaDialog] = useState(false)

  const handleHideWindow = async () => {
    try {
      await invoke("hide_main_window")
    } catch (error) {
      console.error("Failed to hide window:", error)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Escape") {
      handleHideWindow()
    }
  }

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      handleHideWindow()
    }
  }

  useEffect(() => {
    const unlistenRecordingToggle = listen("hotkey-recording-toggle", () => {
      handleToggleRecording()
    })

    return () => {
      unlistenRecordingToggle.then(fn => fn())
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
      setRunningState("transcribing")
      setRecordingTime(0)
      
      // After stopping, we need to find the latest audio file and transcribe it
      // The audio is saved to ~/.tether/audio/ directory
      // For now, we'll just show a notification that recording is saved
      // The actual transcription can be triggered separately if needed
      
      // TODO: Implement auto-transcribe by scanning audio directory for latest file
      setRunningState("idle")
    } catch (error) {
      console.error("Failed to stop recording:", error)
      setRunningState("idle")
    }
  }

  const handleToggleRecording = async () => {
    if (runningState === "recording") {
      await handleStopRecording()
    } else if (runningState === "idle") {
      await handleStartRecording()
    }
  }

  const handleWeave = async () => {
    try {
      // First check Ollama status
      const ollamaResult = await invoke<string>("check_ollama")
      const status: OllamaStatus = JSON.parse(ollamaResult)
      
      if (status.status === "not_installed") {
        // Show install dialog
        setShowOllamaDialog(true)
        return
      } else if (status.status === "not_running") {
        // Show message to start Ollama
        setResult(`Ollama is not running. Please run 'ollama serve' in your terminal, or install Ollama first.`)
        return
      }
      
      // Ollama is available, proceed with weave
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
  
  const handleInstallOllama = async () => {
    setShowOllamaDialog(false)
    try {
      setRunningState("weaving")
      const installResult = await invoke<string>("install_ollama")
      const result = JSON.parse(installResult)
      setResult(result.message || JSON.stringify(result, null, 2))
    } catch (error) {
      console.error("Failed to install Ollama:", error)
      setResult(`Error installing Ollama: ${error}`)
    } finally {
      setRunningState("idle")
    }
  }
  
  const handleAsk = async (query: string) => {
    if (!query.trim()) return
    
    // Check Ollama first
    try {
      const ollamaResult = await invoke<string>("check_ollama")
      const status: OllamaStatus = JSON.parse(ollamaResult)
      
      if (status.status !== "available") {
        setResult(`Ollama is required for asking questions. Status: ${status.status}. Please install or start Ollama.`)
        return
      }
    } catch (error) {
      console.error("Failed to check Ollama:", error)
    }
    
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
    <div 
      className="h-screen w-screen bg-transparent p-4 flex items-center justify-center"
      onKeyDown={handleKeyDown}
      onClick={handleBackdropClick}
    >
      <Command 
        className="rounded-xl border border-slate-800 bg-slate-950 text-slate-50 shadow-2xl max-w-2xl w-full overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
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
                <CommandItem onSelect={handleToggleRecording}>
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
                <CommandItem onSelect={() => setShowOllamaDialog(true)}>
                  <Download className="mr-2 h-4 w-4 text-green-400" />
                  Tether: Install Ollama
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

          {runningState === "transcribing" && (
            <div className="p-4 flex items-center justify-center space-x-3">
              <Loader2 className="h-5 w-5 animate-spin text-yellow-400" />
              <span className="text-slate-400">Transcribing...</span>
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
        
        {/* Ollama Install Dialog */}
        {showOllamaDialog && (
          <div className="p-4 border-t border-slate-800">
            <div className="bg-slate-900 rounded-lg p-4">
              <div className="flex items-start space-x-3 mb-4">
                <AlertCircle className="h-5 w-5 text-yellow-400 mt-0.5" />
                <div>
                  <h3 className="font-medium text-slate-200">Ollama Not Found</h3>
                  <p className="text-sm text-slate-400 mt-1">
                    Ollama is required for Weave and Ask features. 
                    Installation size: ~200MB + 2GB for the model.
                  </p>
                </div>
              </div>
              <div className="flex space-x-3">
                <button
                  onClick={handleInstallOllama}
                  className="flex-1 py-2 bg-cyan-600 hover:bg-cyan-500 rounded-lg text-sm font-medium"
                >
                  Install Ollama
                </button>
                <button
                  onClick={() => setShowOllamaDialog(false)}
                  className="flex-1 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-sm"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
      </Command>
    </div>
  )
}
