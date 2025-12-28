import os
import random
from typing import List


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
WORDS_FILE = os.path.join(DATA_DIR, "random_words.txt")


def load_word_pool() -> List[str]:
    """
    Loads entropy seed words from /data/random_words.txt.
    Supports:
      - comma-delimited lists
      - multi-line words
      - ignores blank lines and # comments
      - unlimited length
    """
    if not os.path.exists(WORDS_FILE):
        return []

    words: List[str] = []

    with open(WORDS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue
            if line.startswith("#"):  # comment support
                continue

            # allow comma OR newline based structure
            parts = [w.strip() for w in line.split(",") if w.strip()]
            words.extend(parts)

    # remove duplicates, preserve order
    seen = set()
    unique_words = []
    for w in words:
        if w not in seen:
            seen.add(w)
            unique_words.append(w)

    return unique_words


def sample_random_seed_words(n: int = 3) -> List[str]:
    pool = load_word_pool()
    if not pool:
        return ["entropy", "spark", "mirror"]  # fallback default

    if n >= len(pool):
        return random.sample(pool, len(pool))  # shuffle entire pool if requested
    return random.sample(pool, n)
