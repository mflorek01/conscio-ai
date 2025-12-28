import json
import os
import threading
from typing import Any


_file_lock = threading.Lock()


def load_json(path: str, default: Any) -> Any:
    with _file_lock:
        if not os.path.exists(path):
            return default
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return default


def save_json(path: str, data: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = path + ".tmp"
    with _file_lock:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, path)
