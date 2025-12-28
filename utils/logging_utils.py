import os
import threading
from typing import Any, Dict, List

# Log file for internal tick logs
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
LOG_FILE = os.path.join(DATA_DIR, "tick_log.txt")

_log_lock = threading.Lock()


def _ensure_log_dir() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)


def _write_log_line(line: str) -> None:
    """Thread-safe append to the internal tick log file."""
    _ensure_log_dir()
    with _log_lock:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def log_thoughts(tick: int, thoughts: List[Dict[str, Any]]) -> None:
    """Log subconscious thoughts for this tick to a file (no console spam)."""
    if not thoughts:
        return

    _write_log_line(f"[tick {tick}] Subconscious produced {len(thoughts)} thought(s):")
    for t in thoughts:
        content = t.get("content", "")
        tags = t.get("tags", [])
        _write_log_line(f"  - {content[:200]}  (tags={tags})")


def log_decision(tick: int, decision: Dict[str, Any]) -> None:
    """Log conscious decisions for this tick to the file."""
    actions = decision.get("actions", [])
    guidance = decision.get("subconscious_guidance_delta", {})
    _write_log_line(f"[tick {tick}] Conscious decision:")
    _write_log_line(f"  Actions: {[a.get('type') for a in actions]}")
    _write_log_line(f"  Guidance delta: {guidance}")


def log_internal(message: str) -> None:
    """Internal debug logging."""
    _write_log_line(f"[internal] {message}")
