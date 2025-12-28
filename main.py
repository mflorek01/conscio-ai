import time
import threading

from core.state import load_state, save_state
from core.percepts import get_recent_percepts, record_percept
from core.goals import get_active_goals
from core.memory import get_recent_memory
from agents.subconscious import build_subconscious_context, call_subconscious_llm
from agents.conscious import build_conscious_context, call_conscious_llm
from actions.executor import execute_actions
from utils.logging_utils import log_thoughts, log_decision


TICK_INTERVAL_SECONDS = 1.0
IDLE_TIMEOUT_SECONDS = 30.0  # configurable idle shutoff window

_running = True  # simple flag to stop both loops on Ctrl+C


def cli_input_worker() -> None:
    """
    Background thread that reads user input from the terminal
    and turns each line into a Percept.
    """
    print("[CLI] Type messages and press Enter. Ctrl+C in main window to quit.")
    while _running:
        try:
            line = input()
        except EOFError:
            break
        if not line:
            continue
        text = line.strip()
        if not text:
            continue

        if text.lower() in {"quit", "exit"}:
            print("[CLI] Received 'quit' command. Use Ctrl+C in main window to stop the loop.")
        # Record as a percept for the mind to use next ticks
        record_percept(source="user", content=text, tags=["cli"])
        print(f"[CLI] Recorded percept from user: {text}")


def _update_speech_state_from_percepts(state: dict, recent_percepts: list) -> None:
    """Update last_user_tick and last_user_wall_time if recent percepts contain user messages."""
    import time as _time

    speech_state = state.get("speech_state", {})
    tick = state.get("tick", 0)

    if any(p.get("source") == "user" for p in recent_percepts):
        speech_state["last_user_tick"] = tick
        speech_state["last_user_wall_time"] = _time.time()

    state["speech_state"] = speech_state


def _update_speech_state_from_decision(state: dict, decision: dict) -> None:
    """Update speech state based on whether the conscious chose to speak."""
    speech_state = state.get("speech_state", {})
    tick = state.get("tick", 0)

    action = decision.get("action", "STAY_SILENT")
    if action == "SPEAK":
        speech_state["last_speak_tick"] = tick
        last_user_tick = speech_state.get("last_user_tick", 0)
        # If we spoke without very recent user input, treat as unsolicited
        if tick - last_user_tick > 2:
            speech_state["unsolicited_speak_count"] = speech_state.get("unsolicited_speak_count", 0) + 1

    state["speech_state"] = speech_state


def tick(state: dict) -> dict:
    """One heartbeat of the system."""

    state["tick"] += 1

    recent_percepts = get_recent_percepts(limit=5)
    active_goals = get_active_goals(limit=3)
    recent_memory = get_recent_memory(limit=10)

    # Update speech_state with any recent user messages
    _update_speech_state_from_percepts(state, recent_percepts)

    # 1) Subconscious
    sub_ctx = build_subconscious_context(
        tick=state["tick"],
        recent_percepts=recent_percepts,
        active_goals=active_goals,
        recent_thoughts=state.get("recent_thoughts", []),
        guidance=state.get("subconscious_guidance", {}),
    )
    sub_output = call_subconscious_llm(sub_ctx)
    state["recent_thoughts"] = (state.get("recent_thoughts", []) + sub_output["thoughts"])[-20:]

    log_thoughts(state["tick"], sub_output["thoughts"])

    # 2) Conscious (now includes speech governor)
    cons_ctx = build_conscious_context(
        tick=state["tick"],
        subconscious_output=sub_output,
        recent_percepts=recent_percepts,
        active_goals=active_goals,
        memory_candidates=recent_memory,
        speech_state=state.get("speech_state", {}),
    )
    decision = call_conscious_llm(cons_ctx)
    log_decision(state["tick"], decision)

    # Update speech_state based on SPEAK/STAY_SILENT choice
    _update_speech_state_from_decision(state, decision)

    # 3) Apply external actions (e.g., SPEAK)
    execute_actions(decision.get("actions", []), decision, state)

    # 4) Update guidance for subconscious next tick
    guidance = state.get("subconscious_guidance", {})
    delta = decision.get("subconscious_guidance_delta", {}) or {}
    guidance.setdefault("focus_tags", [])
    for tag in delta.get("focus_tags_add", []):
        if tag not in guidance["focus_tags"]:
            guidance["focus_tags"].append(tag)
    for tag in delta.get("focus_tags_remove", []):
        if tag in guidance["focus_tags"]:
            guidance["focus_tags"].remove(tag)

    temperature = guidance.get("temperature", 0.9)
    temperature += delta.get("temperature_adjustment", 0.0)
    guidance["temperature"] = max(0.1, min(1.2, temperature))
    state["subconscious_guidance"] = guidance

    return state


def main():
    global _running

    state = load_state()

    # Initialize last_user_wall_time if not present or zero
    speech_state = state.get("speech_state", {})
    if not speech_state.get("last_user_wall_time"):
        speech_state["last_user_wall_time"] = time.time()
    state["speech_state"] = speech_state

    # Start background thread to read CLI input
    input_thread = threading.Thread(target=cli_input_worker, daemon=True)
    input_thread.start()

    try:
        while True:
            now = time.time()
            speech_state = state.get("speech_state", {})
            last_user_ts = speech_state.get("last_user_wall_time") or now

            # Idle safety cutoff: shut down if no user input for IDLE_TIMEOUT_SECONDS
            if now - last_user_ts > IDLE_TIMEOUT_SECONDS:
                print(f"\n[main] Idle timeout hit ({IDLE_TIMEOUT_SECONDS} seconds with no user input). Shutting down.")
                _running = False
                save_state(state)
                break

            state = tick(state)
            save_state(state)
            time.sleep(TICK_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\n[main] Stopped by user; saving state one last time...")
        _running = False
        save_state(state)


if __name__ == "__main__":
    main()
