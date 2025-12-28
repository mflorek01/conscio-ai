from typing import Any, Dict, List

from core.memory import add_memory_item
from core.goals import update_goal
from utils.logging_utils import log_internal

# ANSI color codes
GREEN = "\033[92m"
RESET = "\033[0m"


def execute_actions(actions: List[Dict[str, Any]], decision: Dict[str, Any], state: Dict[str, Any]) -> None:
    """
    Execute an ActionPlan produced by the conscious layer.
    For now, we just print responses and apply simple updates.
    """

    for action in actions:
        a_type = action.get("type")
        payload = action.get("payload", {})

        if a_type == "respond_to_user":
            message = payload.get("message", "").strip()
            if message:
                # Whole line in bright green
                print(f"\n{GREEN}[AI -> User] {message}{RESET}\n")

        elif a_type == "update_memory":
            item = payload.get("item")
            if isinstance(item, dict):
                add_memory_item(item)

        elif a_type == "update_goal":
            goal_id = payload.get("goal_id")
            patch = payload.get("patch", {})
            if goal_id:
                update_goal(goal_id, **patch)

        elif a_type == "log_internal":
            msg = payload.get("message", "")
            log_internal(msg)

        else:
            log_internal(f"Unknown action type: {a_type}")
