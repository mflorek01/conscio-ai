import json
from typing import Any, Dict, List

from openai import OpenAI
from agents.prompts_subconscious import build_subconscious_prompt
from utils.randomness import sample_random_seed_words

client = OpenAI()


def build_subconscious_context(
    tick: int,
    recent_percepts: List[Dict[str, Any]],
    active_goals: List[Dict[str, Any]],
    recent_thoughts: List[Dict[str, Any]],
    guidance: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "tick": tick,
        "recent_percepts": recent_percepts,
        "active_goals": active_goals,
        "recent_thoughts": recent_thoughts,
        "guidance": {
            "focus_tags": guidance.get("focus_tags", []),
            "style": guidance.get("style", "free_association"),
            "max_ideas": guidance.get("max_ideas", 5),
            "temperature": guidance.get("temperature", 0.9),
        },
        "random_seed_words": sample_random_seed_words(3),
    }


def call_subconscious_llm(context: Dict[str, Any]) -> Dict[str, Any]:
    prompt = build_subconscious_prompt(context)

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
        temperature=context["guidance"].get("temperature", 0.9),
        max_output_tokens=400,
        response_format={"type": "json_object"},
    )

    text = response.output[0].content[0].text  # type: ignore[attr-defined]
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Fallback: wrap raw text in a single "thought"
        data = {
            "thoughts": [
                {
                    "id": f"thought-fallback-{context['tick']}",
                    "timestamp": context["tick"],
                    "content": text,
                    "tags": ["fallback"],
                    "confidence": 0.3,
                    "novelty": 0.5,
                    "related_goals": [],
                }
            ],
            "raw_stream": text,
            "metrics": {
                "mean_novelty": 0.5,
                "mean_confidence": 0.3,
            },
        }

    # Minimal normalization
    data.setdefault("thoughts", [])
    data.setdefault("raw_stream", "")
    data.setdefault("metrics", {})
    return data
