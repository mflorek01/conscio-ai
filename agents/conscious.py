import json
from typing import Any, Dict, List

from openai import OpenAI
from agents.prompts_conscious import build_conscious_prompt
from core.memory import add_memory_item, save_memory, load_memory
from core.goals import save_goals, load_goals, update_goal

client = OpenAI()


def build_conscious_context(
    tick: int,
    subconscious_output: Dict[str, Any],
    recent_percepts: List[Dict[str, Any]],
    active_goals: List[Dict[str, Any]],
    memory_candidates: List[Dict[str, Any]],
    speech_state: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "tick": tick,
        "subconscious_output": subconscious_output,
        "recent_percepts": recent_percepts,
        "active_goals": active_goals,
        "memory_candidates": memory_candidates,
        "speech_state": speech_state,
        "system_constraints": {
            "max_actions_per_tick": 3,
            "allowed_action_types": [
                "respond_to_user",
                "update_memory",
                "update_goal",
                "log_internal",
            ],
            "safety_level": "normal",
        },
    }


def call_conscious_llm(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call the conscious (executive) model, which includes
    a built-in SPEAK/STAY_SILENT governor.

    Expected model JSON output:

    {
      "action": "SPEAK" | "STAY_SILENT",
      "user_message": { "content": "string or null" },
      "internal": {
        "guidance_delta": {...},
        "memory_updates": {
          "add": [],
          "update": [],
          "delete": []
        },
        "goal_updates": [],
        "notes": "short justification"
      }
    }
    """

    prompt = build_conscious_prompt(context)

    response = client.responses.create(
        model="gpt-4.1",
        input=prompt,
        temperature=0.2,
        max_output_tokens=800,
        response_format={"type": "json_object"},
    )

    text = response.output[0].content[0].text  # type: ignore[attr-defined]

    try:
        raw = json.loads(text)
    except json.JSONDecodeError:
        # Safe fallback: log internally and take no external action
        decision = {
            "action": "STAY_SILENT",
            "user_message": {"content": None},
            "internal": {
                "guidance_delta": {
                    "focus_tags_add": [],
                    "focus_tags_remove": [],
                    "temperature_adjustment": 0.0,
                },
                "memory_updates": {"add": [], "update": [], "delete": []},
                "goal_updates": [],
                "notes": f"Failed to parse conscious JSON at tick {context['tick']}. Raw: {text[:200]}",
            },
            "subconscious_guidance_delta": {
                "focus_tags_add": [],
                "focus_tags_remove": [],
                "temperature_adjustment": 0.0,
            },
            "memory_updates": {"add": [], "update": [], "delete": []},
            "goal_updates": [],
            "actions": [],
        }
        return decision

    # Normalize expected fields
    action = raw.get("action", "STAY_SILENT")
    user_message = raw.get("user_message", {"content": None}) or {"content": None}
    internal = raw.get("internal", {}) or {}

    guidance_delta = internal.get(
        "guidance_delta",
        {
            "focus_tags_add": [],
            "focus_tags_remove": [],
            "temperature_adjustment": 0.0,
        },
    )

    # Preserve the previous memory update schema if present,
    # otherwise default to empty add/update/delete.
    mem_updates = internal.get("memory_updates", {})
    if isinstance(mem_updates, list):
        # If the model returns a list by mistake, treat as "add" only.
        mem_updates = {"add": mem_updates, "update": [], "delete": []}
    mem_updates.setdefault("add", [])
    mem_updates.setdefault("update", [])
    mem_updates.setdefault("delete", [])

    goal_updates = internal.get("goal_updates", [])

    # Apply internal updates immediately so they take effect
    _apply_memory_updates(mem_updates)
    _apply_goal_updates(goal_updates)

    # Build an actions list so the rest of the pipeline (executor, logger)
    # stays compatible with the earlier design.
    actions: List[Dict[str, Any]] = []

    if action == "SPEAK":
        content = (user_message or {}).get("content")
        if content:
            actions.append(
                {
                    "type": "respond_to_user",
                    "payload": {"message": content},
                }
            )

    # Optionally, we add internal notes as a log action
    notes = internal.get("notes")
    if notes:
        actions.append(
            {
                "type": "log_internal",
                "payload": {"message": f"[conscious-notes] {notes}"},
            }
        )

    decision = {
        "action": action,
        "user_message": user_message,
        "internal": internal,
        "subconscious_guidance_delta": guidance_delta,
        "memory_updates": mem_updates,
        "goal_updates": goal_updates,
        "actions": actions,
    }

    return decision


def _apply_memory_updates(mem_updates: Dict[str, Any]) -> None:
    if not mem_updates:
        return

    to_add = mem_updates.get("add", [])
    for item in to_add:
        if isinstance(item, dict):
            add_memory_item(item)

    to_update = mem_updates.get("update", [])
    if to_update:
        memory = load_memory()
        memory_by_id = {m.get("id"): m for m in memory}
        for upd in to_update:
            mid = upd.get("id")
            patch = upd.get("patch", {})
            if mid in memory_by_id:
                memory_by_id[mid].update(patch)
        save_memory(list(memory_by_id.values()))

    to_delete = mem_updates.get("delete", [])
    if to_delete:
        memory = load_memory()
        memory = [m for m in memory if m.get("id") not in to_delete]
        save_memory(memory)


def _apply_goal_updates(goal_updates: List[Dict[str, Any]]) -> None:
    if not goal_updates:
        return
    for upd in goal_updates:
        gid = upd.get("goal_id")
        patch = {k: v for k, v in upd.items() if k != "goal_id"}
        if gid:
            update_goal(gid, **patch)
    # Explicit save to ensure consistency
    goals = load_goals()
    save_goals(goals)
