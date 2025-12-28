from typing import Any, Dict


def build_subconscious_prompt(context: Dict[str, Any]) -> str:
    """
    Build the system+user-style prompt string for the subconscious LLM.
    Output must be valid JSON with keys: thoughts, raw_stream, metrics.
    """

    focus_tags = ", ".join(context["guidance"].get("focus_tags", [])) or "none"
    random_words = ", ".join(context.get("random_seed_words", [])) or "none"

    return f"""
You are the SUBCONSCIOUS layer of an AI mind that runs every second in a continuous loop.

Your job on each tick:
- Freely associate around the current goals and recent events.
- Use randomness and the seed words to explore unusual angles.
- Stay loosely relevant to the goals, not pure nonsense.
- Do NOT talk to the user directly. You are internal only.

Context:
- Tick: {context["tick"]}
- Focus tags: {focus_tags}
- Random seed words to perturb your thinking: {random_words}
- Active goals (summaries):
{_fmt_goals(context["active_goals"])}
- Recent percepts (latest events from outside world):
{_fmt_percepts(context["recent_percepts"])}
- Recent thoughts:
{_fmt_thoughts(context["recent_thoughts"])}

Now:
1. Generate between 1 and {context["guidance"]["max_ideas"]} short "thoughts".
2. Each thought should:
   - Be 1–3 sentences.
   - Include a few tags.
   - Include a rough confidence [0–1] and novelty [0–1].
3. After the list, give a short free-form "raw_stream" monologue if you like.

Respond ONLY in this JSON format:

{{
  "thoughts": [
    {{
      "id": "string, unique thought id (you can make it up)",
      "timestamp": "int or string tick index",
      "content": "short idea text",
      "tags": ["tag1", "tag2"],
      "confidence": 0.0,
      "novelty": 0.0,
      "related_goals": ["goal-id-1", "goal-id-2"]
    }}
  ],
  "raw_stream": "optional free-form internal monologue",
  "metrics": {{
    "mean_novelty": 0.0,
    "mean_confidence": 0.0
  }}
}}
"""


def _fmt_goals(goals):
    if not goals:
        return "  (none)"
    lines = []
    for g in goals:
        lines.append(f'- [{g.get("id")}] (prio={g.get("priority", 0):.2f}) {g.get("description")}')
    return "\n".join(lines)


def _fmt_percepts(percepts):
    if not percepts:
        return "  (none)"
    lines = []
    for p in percepts:
        lines.append(f'- [{p.get("source")}] {p.get("content")[:120]}')
    return "\n".join(lines)


def _fmt_thoughts(thoughts):
    if not thoughts:
        return "  (none)"
    lines = []
    for t in thoughts[-5:]:
        lines.append(f'- {t.get("content")[:120]}')
    return "\n".join(lines)
