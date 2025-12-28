import os
import time
from typing import Any, Dict, List

from utils.persistence import load_json, save_json

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
GOALS_FILE = os.path.join(DATA_DIR, "goals.json")


def _ensure_data_dir():
    os.makedirs(DATA_DIR, exist_ok=True)


def load_goals() -> List[Dict[str, Any]]:
    _ensure_data_dir()
    return load_json(GOALS_FILE, [])


def save_goals(goals: List[Dict[str, Any]]) -> None:
    _ensure_data_dir()
    save_json(GOALS_FILE, goals)


def add_goal(description: str, priority: float = 0.5) -> Dict[str, Any]:
    goals = load_goals()
    now = time.time()
    new_goal = {
        "id": f"goal-{int(now * 1000)}",
        "description": description,
        "status": "active",
        "priority": priority,
        "created_at": now,
        "updated_at": now,
        "subgoals": [],
    }
    goals.append(new_goal)
    save_goals(goals)
    return new_goal


def update_goal(goal_id: str, **patch: Any) -> None:
    goals = load_goals()
    updated = False
    for g in goals:
        if g.get("id") == goal_id:
            g.update(patch)
            g["updated_at"] = time.time()
            updated = True
            break
    if updated:
        save_goals(goals)


def get_active_goals(limit: int = 3) -> List[Dict[str, Any]]:
    goals = [g for g in load_goals() if g.get("status") == "active"]
    goals_sorted = sorted(goals, key=lambda x: x.get("priority", 0), reverse=True)
    return goals_sorted[:limit]
