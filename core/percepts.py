import os
import json
import time
from typing import Any, Dict, List

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
PERCEPTS_FILE = os.path.join(DATA_DIR, "percepts.jsonl")


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def record_percept(source: str, content: str, tags: List[str] | None = None) -> Dict[str, Any]:
    """Append a percept to the log and return it."""
    _ensure_data_dir()
    now = time.time()
    percept = {
        "id": f"percept-{int(now * 1000)}",
        "source": source,
        "timestamp": now,
        "content": content,
        "tags": tags or [],
    }
    with open(PERCEPTS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(percept) + "\n")
    return percept


def get_recent_percepts(limit: int = 5) -> List[Dict[str, Any]]:
    """Load up to the last `limit` percepts from the log."""
    _ensure_data_dir()
    if not os.path.exists(PERCEPTS_FILE):
        return []

    with open(PERCEPTS_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    recent_lines = lines[-limit:]
    return [json.loads(line) for line in recent_lines]
