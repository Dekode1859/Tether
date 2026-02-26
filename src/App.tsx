import { useEffect, useState } from "react"
import CommandPalette from "./components/CommandPalette"
import RecordingWidget from "./components/RecordingWidget"

function App() {
  const [windowType, setWindowType] = useState<"main" | "widget">("main")

  useEffect(() => {
    const path = window.location.pathname
    if (path === "/widget") {
      setWindowType("widget")
    } else {
      setWindowType("main")
    }
  }, [])

  if (windowType === "widget") {
    return <RecordingWidget />
  }

  return <CommandPalette />
}

export default App
