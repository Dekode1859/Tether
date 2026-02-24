import sys
import time
import threading
from pathlib import Path

from core import ensure_directories, get_config
from app.tray import TrayIcon
from app.stt import Transcriber, Spool


def on_audio_ready(audio_path: str):
    """Callback when audio recording is complete - transcribe and spool."""
    print(f"Processing: {audio_path}")

    def process():
        try:
            # Transcribe audio
            transcriber = Transcriber()
            text = transcriber.transcribe(audio_path)

            if text:
                # Append to spool
                spool = Spool()
                spool.append(text)
                print(f"Transcribed and spooled: {text[:50]}...")
            else:
                print("No text transcribed")
        except Exception as e:
            print(f"Error processing audio: {e}")

    # Run transcription in background thread to not block UI
    thread = threading.Thread(target=process, daemon=True)
    thread.start()


def main():
    """Main entry point for Tether."""
    ensure_directories()

    config = get_config()

    print("Starting Tether - Press Ctrl+Shift+Space to toggle recording")
    print("Click the tray icon to access menu")

    # Create tray with transcription callback
    tray = TrayIcon(on_audio_ready=on_audio_ready)
    tray.run()

    scheduler = None
    if config.llm_enabled:
        from jobs import start_scheduler

        scheduler = start_scheduler(
            hour=config.daily_summary_hour, minute=config.daily_summary_minute
        )
        print(
            f"Scheduler started - Daily summary at {config.daily_summary_hour:02d}:{config.daily_summary_minute:02d}"
        )
    else:
        print("LLM Summaries disabled - No scheduling configured")
        print("Enable via tray menu: Right-click > Enable LLM Summaries")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        if scheduler:
            scheduler.stop()
        tray.stop()


if __name__ == "__main__":
    main()
