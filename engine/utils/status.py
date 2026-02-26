import json
import os
import threading
from pathlib import Path
from datetime import datetime
from typing import Optional

_LOCK = threading.Lock()


def get_tether_dir() -> Path:
    """Get the tether config directory."""
    home = Path.home()
    tether_dir = home / ".tether"
    tether_dir.mkdir(exist_ok=True)
    return tether_dir


def get_vault_dir() -> Path:
    """Get the vault directory."""
    vault_dir = get_tether_dir() / "vault"
    vault_dir.mkdir(exist_ok=True)
    return vault_dir


def get_daily_dir() -> Path:
    """Get the daily notes directory."""
    daily_dir = get_vault_dir() / "Daily"
    daily_dir.mkdir(exist_ok=True)
    return daily_dir


def get_status_file_path() -> Path:
    """Get the path to the engine status file."""
    return get_tether_dir() / "engine_status.json"


def get_default_status() -> dict:
    """Get default status."""
    return {"pid": None, "status": "idle", "task": None, "started_at": None}


def read_status() -> dict:
    """Read the current engine status."""
    path = get_status_file_path()

    if not path.exists():
        return get_default_status()

    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return get_default_status()


def write_status(
    status: str = "idle", task: Optional[str] = None, pid: Optional[int] = None
) -> dict:
    """Write the engine status."""
    path = get_status_file_path()

    with _LOCK:
        data = get_default_status()
        data["status"] = status

        if task is not None:
            data["task"] = task

        if pid is not None:
            data["pid"] = pid

        if status in ("busy", "recording"):
            data["started_at"] = datetime.now().isoformat()
        else:
            data["started_at"] = None

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

        return data


def is_busy() -> bool:
    """Check if the engine is currently busy."""
    status = read_status()
    return status.get("status") in ("busy", "recording")


def get_current_task() -> Optional[str]:
    """Get the current task name."""
    status = read_status()
    return status.get("task")


def mark_idle() -> None:
    """Mark the engine as idle."""
    write_status("idle", None, None)
