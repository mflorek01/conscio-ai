import os
from typing import Any, Dict

from utils.persistence import load_json, save_json

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
STATE_FILE = os.path.join(DATA_DIR, "state.json")
GUIDANCE_FILE = os.path.join(DATA_DIR, "subconscious_guidance.json")


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def _default_speech_state() -> Dict[str, Any]:
    """
    Tracks how the agent behaves conversationally.

    mode:
      - passive: respond mostly when directly addressed
      - cohost: respond to user + occasionally volunteer comments
      - teacher: more talkative, offers explanations often
    """
    return {
        "mode": "cohost",
        "last_user_tick": 0,
        "last_speak_tick": 0,
        "unsolicited_speak_count": 0,
        "silence_until_tick": 0,
        # Wall-clock seconds of last user input; 0 means "not initialized yet".
        "last_user_wall_time": 0.0,
    }


def default_state() -> Dict[str, Any]:
    return {
        "tick": 0,
        "recent_thoughts": [],
        "subconscious_guidance": {
            "focus_tags": [],
            "temperature": 0.9,
        },
        "speech_state": _default_speech_state(),
    }


def load_state() -> Dict[str, Any]:
    _ensure_data_dir()
    state = load_json(STATE_FILE, default_state())

    # Ensure required keys exist even if file is older
    base = default_state()
    for k, v in base.items():
        if k == "speech_state":
            # merge default speech_state with any existing
            existing = state.get("speech_state", {})
            merged = _default_speech_state()
            merged.update(existing)
            state["speech_state"] = merged
        else:
            state.setdefault(k, v)

    # Load guidance if stored separately
    guidance = load_json(GUIDANCE_FILE, state.get("subconscious_guidance", {}))
    state["subconscious_guidance"] = guidance

    return state


def save_state(state: Dict[str, Any]) -> None:
    _ensure_data_dir()
    save_json(STATE_FILE, state)
    if "subconscious_guidance" in state:
        save_json(GUIDANCE_FILE, state["subconscious_guidance"])
