#!/usr/bin/env python3
"""
Tether Engine - CLI for thought ingestion
Usage:
    python main.py --spool      # Start recording
    python main.py --weave      # Process daily notes into knowledge graph
    python main.py --ask "?"   # Query the vault
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from engine.utils import status, get_tether_dir, get_vault_dir
from engine.audio import AudioRecorder
from engine.stt import Transcriber, Spool, get_daily_dir
from engine.ai import (
    LLMClient,
    ENTITY_EXTRACTION_PROMPT,
    ASK_VAULT_PROMPT,
    SYSTEM_PROMPT,
)


def cmd_spool():
    """Record audio and transcribe to vault."""
    import threading

    status.write_status("recording", "spool", os.getpid())
    print("Recording started...", flush=True)

    recorder = AudioRecorder()
    transcriber = Transcriber()
    spool = Spool()

    # Start recording
    recorder.start()

    # Keep running until interrupted
    try:
        while recorder.is_recording():
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nStopping recording...", flush=True)

    # Stop and save
    audio_path = recorder.stop()

    if audio_path and audio_path.exists():
        print(f"Audio saved to: {audio_path}", flush=True)

        # Transcribe
        print("Transcribing...", flush=True)
        text = transcriber.transcribe(str(audio_path))

        if text:
            # Save to spool
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

    # Read today's daily note
    spool = Spool()
    daily_content = spool.read_today()

    if not daily_content.strip():
        print("No content to weave.", flush=True)
        status.mark_idle()
        return

    # Check Ollama availability
    llm = LLMClient()
    if not llm.is_available():
        print("Ollama not available. Install and run 'ollama serve'.", flush=True)
        status.mark_idle()
        return

    # Extract entities
    print("Extracting entities...", flush=True)
    prompt = ENTITY_EXTRACTION_PROMPT.format(daily_content=daily_content)

    try:
        result = llm.query(prompt, SYSTEM_PROMPT)

        # Parse JSON
        try:
            entities = json.loads(result)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            start = result.find("{")
            end = result.rfind("}") + 1
            if start >= 0 and end > start:
                entities = json.loads(result[start:end])
            else:
                entities = {"projects": [], "people": [], "ideas": []}

        print(f"Extracted entities: {json.dumps(entities, indent=2)}", flush=True)

        # Update daily note with links
        _update_daily_with_links(daily_content, entities)

        # Write to vault folders
        _write_to_vault_folders(entities)

        print("Weave complete!", flush=True)

    except Exception as e:
        print(f"Weave failed: {e}", flush=True)

    status.mark_idle()


def _update_daily_with_links(daily_content: str, entities: dict) -> None:
    """Update daily note with wiki-style links."""
    daily_path = get_daily_dir() / Path(__file__).name.replace(
        ".py", ""
    )  # This won't work, fix below

    # Get today's date
    from datetime import datetime

    today = datetime.now().strftime("%Y-%m-%d")
    daily_path = get_daily_dir() / f"{today}.md"

    if not daily_path.exists():
        return

    updated_content = daily_content

    # Add links for projects
    for project in entities.get("projects", []):
        name = project.get("name", "")
        if name:
            updated_content = updated_content.replace(name, f"[[{name}]]")

    # Add links for people
    for person in entities.get("people", []):
        name = person.get("name", "")
        if name:
            updated_content = updated_content.replace(name, f"[[{name}]]")

    daily_path.write_text(updated_content, encoding="utf-8")


def _write_to_vault_folders(entities: dict) -> None:
    """Write extracted entities to vault folders."""
    vault_dir = get_vault_dir()

    # Projects
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

    # People
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

    # Ideas
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

    # Search vault for relevant content
    vault_dir = get_vault_dir()
    context = _search_vault(query, vault_dir)

    if not context:
        print("No relevant context found in vault.", flush=True)
        status.mark_idle()
        return "No relevant context found in vault."

    # Query LLM
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

    # Extract keywords from query
    keywords = re.findall(r"\w+", query.lower())
    keywords = [w for w in keywords if len(w) > 3]

    if not keywords:
        return ""

    results = []

    # Search all markdown files
    for md_file in vault_dir.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            content_lower = content.lower()

            # Check if any keyword matches
            for keyword in keywords:
                if keyword in content_lower:
                    # Get relative path for context
                    rel_path = md_file.relative_to(vault_dir)
                    results.append(f"--- From {rel_path} ---\n{content[:500]}")
                    break
        except Exception:
            continue

    return "\n\n".join(results[:5])  # Limit to top 5 files


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

    args = parser.parse_args()

    if args.spool:
        cmd_spool()
    elif args.weave:
        cmd_weave()
    elif args.ask:
        result = cmd_ask(args.ask)
        print(result)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
