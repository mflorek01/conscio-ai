import os
import time
from typing import Any, Dict, List

from utils.persistence import load_json, save_json

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
MEMORY_FILE = os.path.join(DATA_DIR, "memory.json")


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def load_memory() -> List[Dict[str, Any]]:
    _ensure_data_dir()
    return load_json(MEMORY_FILE, [])


def save_memory(items: List[Dict[str, Any]]) -> None:
    _ensure_data_dir()
    save_json(MEMORY_FILE, items)


def add_memory_item(item: Dict[str, Any]) -> None:
    items = load_memory()
    now = time.time()
    item.setdefault("id", f"mem-{int(now * 1000)}")
    item.setdefault("created_at", now)
    item.setdefault("last_accessed", now)
    items.append(item)
    save_memory(items)


def get_recent_memory(limit: int = 10) -> List[Dict[str, Any]]:
    items = load_memory()
    items_sorted = sorted(items, key=lambda x: x.get("last_accessed", x.get("created_at", 0)), reverse=True)
    return items_sorted[:limit]
