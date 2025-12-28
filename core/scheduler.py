import time
from typing import Callable


def run_loop(tick_fn: Callable[[], None], interval_seconds: float = 1.0) -> None:
    """Generic scheduler if you ever want to use it instead of main's while loop."""
    try:
        while True:
            tick_fn()
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        print("\n[scheduler] Loop stopped by user.")
