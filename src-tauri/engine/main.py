#!/usr/bin/env python3
"""
Tether Engine - CLI for thought ingestion
Usage:
    python -m engine --spool              # Start recording
    python -m engine --weave              # Process daily notes into knowledge graph
    python -m engine --ask "query"        # Query the vault
    python -m engine --check-mic           # Check microphone access
    python -m engine --check-ollama       # Check Ollama status
    python -m engine --install-ollama      # Install Ollama
"""

import argparse
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

from .utils import status, get_tether_dir, get_vault_dir
from .audio import AudioRecorder
from .stt import Transcriber, Spool, get_daily_dir
from .ai import (
    LLMClient,
    ENTITY_EXTRACTION_PROMPT,
    ASK_VAULT_PROMPT,
    SYSTEM_PROMPT,
    OLLAMA_MODEL,
)


def cmd_spool():
    """Record audio and transcribe to vault."""
    import threading

    status.write_status("recording", "spool", os.getpid())
    print("Recording started...", flush=True)

    recorder = AudioRecorder()
    transcriber = Transcriber()
    spool = Spool()

    recorder.start()

    try:
        while recorder.is_recording():
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopping recording...", flush=True)

    audio_path = recorder.stop()

    if audio_path and audio_path.exists():
        print(f"Audio saved to: {audio_path}", flush=True)

        print("Transcribing...", flush=True)
        text = transcriber.transcribe(str(audio_path))

        if text:
            spool_path = spool.append(text)
            print(f"Transcription saved to: {spool_path}", flush=True)
            print(f"Text: {text}", flush=True)
        else:
            print("No text transcribed.", flush=True)
    else:
        print("No audio recorded.", flush=True)

    status.mark_idle()
    print("Recording stopped.", flush=True)


def cmd_weave():
    """Process daily notes into knowledge graph."""
    status.write_status("busy", "weave", os.getpid())
    print("Starting weave...", flush=True)

    spool = Spool()
    daily_content = spool.read_today()

    if not daily_content.strip():
        print("No content to weave.", flush=True)
        status.mark_idle()
        return

    llm = LLMClient()
    if not llm.is_available():
        print("Ollama not available. Install and run 'ollama serve'.", flush=True)
        status.mark_idle()
        return

    print("Extracting entities...", flush=True)
    prompt = ENTITY_EXTRACTION_PROMPT.format(daily_content=daily_content)

    try:
        result = llm.query(prompt, SYSTEM_PROMPT)

        try:
            entities = json.loads(result)
        except json.JSONDecodeError:
            start = result.find("{")
            end = result.rfind("}") + 1
            if start >= 0 and end > start:
                entities = json.loads(result[start:end])
            else:
                entities = {"projects": [], "people": [], "ideas": []}

        print(f"Extracted entities: {json.dumps(entities, indent=2)}", flush=True)

        _update_daily_with_links(daily_content, entities)
        _write_to_vault_folders(entities)

        print("Weave complete!", flush=True)

    except Exception as e:
        print(f"Weave failed: {e}", flush=True)

    status.mark_idle()


def _update_daily_with_links(daily_content: str, entities: dict) -> None:
    """Update daily note with wiki-style links."""
    from datetime import datetime

    today = datetime.now().strftime("%Y-%m-%d")
    daily_path = get_daily_dir() / f"{today}.md"

    if not daily_path.exists():
        return

    updated_content = daily_content

    for project in entities.get("projects", []):
        name = project.get("name", "")
        if name:
            updated_content = updated_content.replace(name, f"[[{name}]]")

    for person in entities.get("people", []):
        name = person.get("name", "")
        if name:
            updated_content = updated_content.replace(name, f"[[{name}]]")

    daily_path.write_text(updated_content, encoding="utf-8")


def _write_to_vault_folders(entities: dict) -> None:
    """Write extracted entities to vault folders."""
    vault_dir = get_vault_dir()

    projects_dir = vault_dir / "Projects"
    projects_dir.mkdir(exist_ok=True)
    for project in entities.get("projects", []):
        name = project.get("name", "")
        context = project.get("context", "")
        if name:
            project_file = projects_dir / f"{name}.md"
            existing = (
                project_file.read_text(encoding="utf-8")
                if project_file.exists()
                else ""
            )
            from datetime import datetime

            entry = f"\n- {datetime.now().strftime('%Y-%m-%d')}: {context}\n"
            project_file.write_text(existing + entry, encoding="utf-8")

    people_dir = vault_dir / "People"
    people_dir.mkdir(exist_ok=True)
    for person in entities.get("people", []):
        name = person.get("name", "")
        context = person.get("context", "")
        if name:
            person_file = people_dir / f"{name}.md"
            existing = (
                person_file.read_text(encoding="utf-8") if person_file.exists() else ""
            )
            from datetime import datetime

            entry = f"\n- {datetime.now().strftime('%Y-%m-%d')}: {context}\n"
            person_file.write_text(existing + entry, encoding="utf-8")

    ideas_dir = vault_dir / "Ideas"
    ideas_dir.mkdir(exist_ok=True)
    for idea in entities.get("ideas", []):
        name = idea.get("name", "")
        context = idea.get("context", "")
        if name:
            idea_file = ideas_dir / f"{name}.md"
            existing = (
                idea_file.read_text(encoding="utf-8") if idea_file.exists() else ""
            )
            from datetime import datetime

            entry = f"\n- {datetime.now().strftime('%Y-%m-%d')}: {context}\n"
            idea_file.write_text(existing + entry, encoding="utf-8")


def cmd_ask(query: str):
    """Query the vault using RAG."""
    status.write_status("busy", "ask", os.getpid())
    print(f"Processing query: {query}", flush=True)

    vault_dir = get_vault_dir()
    context = _search_vault(query, vault_dir)

    if not context:
        print("No relevant context found in vault.", flush=True)
        status.mark_idle()
        return "No relevant context found in vault."

    llm = LLMClient()
    if not llm.is_available():
        print("Ollama not available.", flush=True)
        status.mark_idle()
        return "Ollama not available. Please install and run 'ollama serve'."

    prompt = ASK_VAULT_PROMPT.format(vault_context=context, user_question=query)

    try:
        result = llm.query(prompt, SYSTEM_PROMPT)
        print(f"Answer: {result}", flush=True)
        status.mark_idle()
        return result
    except Exception as e:
        print(f"Query failed: {e}", flush=True)
        status.mark_idle()
        return f"Error: {e}"


def _search_vault(query: str, vault_dir: Path) -> str:
    """Search vault for files containing query terms."""
    import re

    keywords = re.findall(r"\w+", query.lower())
    keywords = [w for w in keywords if len(w) > 3]

    if not keywords:
        return ""

    results = []

    for md_file in vault_dir.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            content_lower = content.lower()

            for keyword in keywords:
                if keyword in content_lower:
                    rel_path = md_file.relative_to(vault_dir)
                    results.append(f"--- From {rel_path} ---\n{content[:500]}")
                    break
        except Exception:
            continue

    return "\n\n".join(results[:5])


def cmd_check_mic():
    """Check microphone access and list available devices."""
    result = {"available": False, "devices": [], "error": None}

    try:
        import sounddevice as sd

        devices = sd.query_devices()
        input_devices = []

        if hasattr(devices, "__iter__"):
            for idx, dev in enumerate(devices):
                try:
                    if dev.get("max_input_channels", 0) > 0:
                        input_devices.append(
                            {
                                "name": dev.get("name", f"Device {idx}"),
                                "channels": dev.get("max_input_channels", 0),
                            }
                        )
                except (TypeError, AttributeError):
                    continue
        elif hasattr(devices, "get"):
            if devices.get("max_input_channels", 0) > 0:
                input_devices.append(
                    {
                        "name": devices.get("name", "Default"),
                        "channels": devices.get("max_input_channels", 0),
                    }
                )

        result["available"] = len(input_devices) > 0
        result["devices"] = input_devices

    except Exception as e:
        result["error"] = str(e)

    print(json.dumps(result), flush=True)
    return result


def cmd_check_ollama():
    """Check Ollama status."""
    result = {"status": "not_installed", "model": OLLAMA_MODEL, "error": None}

    try:
        system = platform.system().lower()

        if system == "windows":
            check_cmd = ["where", "ollama"]
        else:
            check_cmd = ["which", "ollama"]

        subprocess.run(check_cmd, capture_output=True, check=True)
    except subprocess.CalledProcessError:
        result["status"] = "not_installed"
        print(json.dumps(result), flush=True)
        return result

    try:
        llm = LLMClient()
        if llm.is_available():
            result["status"] = "available"
        else:
            result["status"] = "not_running"
    except Exception as e:
        result["status"] = "not_running"
        result["error"] = str(e)

    print(json.dumps(result), flush=True)
    return result


def cmd_install_ollama():
    """Install Ollama and pull the model."""
    system = platform.system().lower()
    result = {
        "status": "downloading",
        "message": "Starting Ollama installation...",
        "error": None,
    }

    try:
        if system == "windows":
            install_cmd = [
                "powershell",
                "-Command",
                "irm https://ollama.com/install.ps1 | iex",
            ]
            result["message"] = "Downloading Ollama for Windows..."
        elif system == "darwin":
            install_cmd = ["brew", "install", "ollama"]
            result["message"] = "Installing Ollama via Homebrew..."
        else:
            install_cmd = [
                "bash",
                "-c",
                "curl -fsSL https://ollama.com/install.sh | sh",
            ]
            result["message"] = "Installing Ollama via curl..."

        print(json.dumps(result), flush=True)

        process = subprocess.Popen(
            install_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        process.wait()

        if process.returncode == 0:
            result["status"] = "pulling_model"
            result["message"] = (
                f"Installing Ollama complete. Pulling model {OLLAMA_MODEL}..."
            )
            print(json.dumps(result), flush=True)

            pull_cmd = ["ollama", "pull", OLLAMA_MODEL]
            pull_process = subprocess.Popen(
                pull_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            pull_process.wait()

            if pull_process.returncode == 0:
                result["status"] = "ready"
                result["message"] = f"Ollama and {OLLAMA_MODEL} installed successfully!"
            else:
                result["status"] = "error"
                result["error"] = "Failed to pull model"
        else:
            result["status"] = "error"
            result["error"] = "Installation failed"

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)

    print(json.dumps(result), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Tether Engine - Privacy-first thought ingestion"
    )

    parser.add_argument(
        "--spool", action="store_true", help="Start recording and transcribe"
    )

    parser.add_argument(
        "--weave", action="store_true", help="Process daily notes into knowledge graph"
    )

    parser.add_argument("--ask", type=str, metavar="QUERY", help="Query the vault")

    parser.add_argument(
        "--check-mic", action="store_true", help="Check microphone access"
    )

    parser.add_argument(
        "--check-ollama", action="store_true", help="Check Ollama status"
    )

    parser.add_argument("--install-ollama", action="store_true", help="Install Ollama")

    args = parser.parse_args()

    if args.spool:
        cmd_spool()
    elif args.weave:
        cmd_weave()
    elif args.ask:
        result = cmd_ask(args.ask)
        print(result)
    elif args.check_mic:
        cmd_check_mic()
    elif args.check_ollama:
        cmd_check_ollama()
    elif args.install_ollama:
        cmd_install_ollama()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
