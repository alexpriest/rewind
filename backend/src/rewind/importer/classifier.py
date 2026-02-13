import json
import logging

import anthropic

from rewind.config import settings

logger = logging.getLogger(__name__)

BATCH_SIZE = 50

SYSTEM_PROMPT = (
    "You are a tag classifier. For each tag, classify it as 'person' "
    "(a human name, first name, nickname, or full name) or 'topic' "
    "(an activity, theme, emotion, place, or concept). "
    "Return ONLY a JSON object mapping each tag to its type. "
    "No explanation, no markdown fences, just the JSON object."
)


def classify_tags(tag_names: list[str]) -> dict[str, str]:
    """Classify tags as 'person' or 'topic' using Claude.

    Returns dict of {tag_name: 'person' | 'topic'}.
    Skips gracefully if no API key is configured.
    """
    if not settings.ANTHROPIC_API_KEY:
        logger.info("No ANTHROPIC_API_KEY configured, skipping tag classification")
        return {}

    if not tag_names:
        return {}

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    results: dict[str, str] = {}

    for i in range(0, len(tag_names), BATCH_SIZE):
        batch = tag_names[i : i + BATCH_SIZE]
        try:
            result = _classify_batch(client, batch)
            results.update(result)
        except Exception:
            logger.exception(f"Failed to classify batch starting at index {i}")

    return results


def _classify_batch(
    client: anthropic.Anthropic, batch: list[str]
) -> dict[str, str]:
    tag_list = json.dumps(batch)
    prompt = f"Classify these tags: {tag_list}"

    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    text = response.content[0].text.strip()

    # Handle potential markdown fences
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1])

    mapping = json.loads(text)

    # Validate and filter to only valid types
    valid: dict[str, str] = {}
    for name, tag_type in mapping.items():
        if tag_type in ("person", "topic"):
            valid[name] = tag_type
        else:
            logger.warning(f"Unexpected tag type '{tag_type}' for '{name}', defaulting to 'topic'")
            valid[name] = "topic"

    return valid
