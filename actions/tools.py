from typing import Any, Dict


def echo_tool(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Placeholder example tool.

    In future you might add:
    - web search
    - file operations
    - running code
    - discord / slack messages
    """
    return {"echo": payload}
