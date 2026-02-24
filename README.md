# Tether

A privacy-first, local-only thought ingestion engine. Capture raw, unstructured verbal thoughts and distill them into a structured Second Brain using exclusively local AI processing.

## Features

- **System Tray App** - Runs quietly in the background with visual state indicators
- **Global Hotkeys** - Toggle recording from anywhere with `Ctrl+Shift+Space`
- **Settings Menu** - Toggle LLM summaries via tray icon (right-click)
- **Local Transcription** - Speech-to-text using faster-whisper (runs entirely offline)
- **Optional LLM Processing** - Uses Ollama for parsing and summarization (can be disabled)
- **Smart Scheduling** - Daily summaries only run if LLM is enabled
- **100% Private** - No audio or text ever leaves your machine

## Architecture

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  Tray    │────▶│  Audio   │────▶│   STT    │────▶│  LLM     │
│  Icon    │     │ Recorder │     │Transcriber│    │(Optional)│
└──────────┘     └──────────┘     └──────────┘     └──────────┘
     │                                                     │
     │ Hotkey: Ctrl+Shift+Space                          │
     ▼                                                     ▼
┌──────────┐                                       ┌──────────┐
│  Hotkey  │                                       │ Markdown │
│  Manager │                                       │ Summary  │
└──────────┘                                       └──────────┘
                                                          │
                                                          ▼
                                                 ┌──────────────┐
                                                 │   Scheduler  │
                                                 │  (schedule)  │
                                                 └──────────────┘
                                                          │
                                                          ▼
                                                 ┌──────────────┐
                                                 │  Notifier    │
                                                 │  (OS Notify) │
                                                 └──────────────┘
```

## Storage

All data is stored locally in `~/.tether/`:

```
~/.tether/
├── config.json              # User settings (LLM toggle, schedule time)
├── raw/                    # Daily spool files (YYYY-MM-DD-spool.txt)
├── audio/                  # Raw audio recordings (YYYY-MM-DD-HHMMSS.wav)
└── summaries/              # Generated markdown summaries (YYYY-MM-DD-summary.md)
```

### Spool File Format

Each entry in the spool file uses ISO timestamps:

```
[2026-02-24 14:30:00] First thought of the day...
[2026-02-24 14:32:15] Another thought recorded...
```

## Prerequisites

1. **Python 3.11+**
2. **Ollama** - Download from https://ollama.ai and keep running in background (optional - can disable via tray menu)
3. **ffmpeg** - Required for audio processing (install via your system package manager)

## Quick Setup

```bash
# Clone the repository
cd tether

# Install dependencies
uv sync

# Pull the Whisper model (small.en - fast and accurate)
# This downloads ~75MB - run once
python -c "from faster_whisper import WhisperModel; WhisperModel('small.en', device='cpu', compute_type='int8')"

# Pull an Ollama model (llama3 or mistral) - optional
ollama pull llama3
```

## Running Tether

```bash
# Start Tether
python main.py
```

This will:
- Show a system tray icon (gray = idle, red = recording)
- Register the global hotkey `Ctrl+Shift+Space`
- Start the background scheduler (only if LLM is enabled)

### Usage

1. **Start Recording** - Press `Ctrl+Shift+Space` or click the tray icon and select "Start Recording"
2. **Stop Recording** - Press `Ctrl+Shift+Space` again or click "Stop Recording"
3. **View Spool** - Check `~/.tether/raw/` for transcribed text with timestamps
4. **Daily Summary** - At 5:00 PM (if LLM enabled), Tether will:
   - Read your day's spool content
   - Generate a structured summary using Ollama
   - Save to `~/.tether/summaries/YYYY-MM-DD-summary.md`
   - Send an OS notification when complete

### Tray Menu

- **Start/Stop Recording** - Toggle audio capture
- **Enable LLM Summaries** - Toggle LLM processing (checkable)
- **Exit** - Close Tether

### Config File

Settings are stored in `~/.tether/config.json`:

```json
{
  "llm_enabled": true,
  "daily_summary_hour": 17,
  "daily_summary_minute": 0
}
```

- **`llm_enabled`**: Set to `false` to disable LLM summaries and scheduling
- **`daily_summary_hour`**: Hour to run daily summary (24-hour format)
- **`daily_summary_minute`**: Minute to run daily summary

## Configuration

Edit `core/config.py` to change defaults, or modify `~/.tether/config.json` after first run:

| Setting | Default | Description |
|---------|---------|-------------|
| `HOTKEY_DEFAULT` | `ctrl+shift+space` | Global hotkey |
| `WHISPER_MODEL` | `small.en` | Whisper model |
| `OLLAMA_MODEL` | `llama3` | Ollama model |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama API |
| `DAILY_SUMMARY_HOUR` | `17` | Summary time (hour) |
| `DAILY_SUMMARY_MINUTE` | `0` | Summary time (minute) |

## Development

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific phase
pytest tests/test_phase1.py -v
```

### Building Executable

```bash
# Install build dependencies
uv sync --all-extras

# Build with PyInstaller
pyinstaller tether.spec

# Output: dist/Tether.exe
```

## Project Structure

```
/Tether
├── app/
│   ├── tray/          # System tray & hotkeys
│   ├── audio/         # Audio capture
│   └── stt/          # Speech-to-text
├── jobs/             # Scheduler & summarization
├── core/             # Config, prompts, LLM client
├── scripts/          # Build scripts
└── tests/            # Test suite
```

## Dependencies

- **pystray** - System tray
- **sounddevice** - Audio capture
- **faster-whisper** - Speech-to-text
- **ollama** - LLM client
- **schedule** - Job scheduling
- **plyer** - OS notifications
- **httpx** - HTTP client

## License

MIT
