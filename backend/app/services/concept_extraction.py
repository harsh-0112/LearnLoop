"""Extract a curriculum concept graph from raw document text using Claude."""

from __future__ import annotations

import json
import logging
import re

from anthropic import Anthropic

from app.config import settings

logger = logging.getLogger(__name__)

MODEL_NAME = "claude-sonnet-4-6"
MAX_TOKENS = 8000
MAX_INPUT_CHARS = 60_000
MIN_CONCEPTS = 10
MAX_CONCEPTS = 30

SYSTEM_PROMPT = (
    "You are a curriculum analyst. Extract the teachable concepts from study material.\n"
    "Respond with STRICT JSON only: a single object of the form\n"
    '{"concepts": [{"name": str, "description": str, "difficulty_level": int, '
    '"prerequisites": [str]}]}\n'
    f"Return between {MIN_CONCEPTS} and {MAX_CONCEPTS} concepts, ordered so that "
    "prerequisites come before the concepts that depend on them.\n"
    "Rules: difficulty_level is an integer 1 (easiest) to 5 (hardest); prerequisites "
    "list only names that also appear in the concepts array; names are short noun "
    "phrases; descriptions are one sentence.\n"
    "Do not include markdown, code fences, commentary or trailing text."
)

CODE_FENCE_RE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.IGNORECASE)


class ConceptExtractionError(RuntimeError):
    """Raised when the model response cannot be parsed into concepts."""


def _get_client() -> Anthropic:
    return Anthropic(api_key=settings.anthropic_api_key)


def _response_text(message: object) -> str:
    """Concatenate the text blocks of an Anthropic message response."""
    parts: list[str] = []
    for block in getattr(message, "content", []) or []:
        text = getattr(block, "text", None)
        if text is None and isinstance(block, dict):
            text = block.get("text")
        if text:
            parts.append(text)
    return "".join(parts).strip()


def _strip_code_fences(raw: str) -> str:
    stripped = CODE_FENCE_RE.sub("", raw.strip())
    start, end = stripped.find("{"), stripped.rfind("}")
    if start != -1 and end > start:
        return stripped[start : end + 1]
    return stripped


def _coerce_difficulty(value: object) -> int:
    try:
        level = int(float(value))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 3
    return min(max(level, 1), 5)


def _normalize(payload: object) -> list[dict]:
    """Validate the parsed payload and drop entries the model got wrong."""
    if isinstance(payload, dict):
        raw_concepts = payload.get("concepts")
    elif isinstance(payload, list):
        raw_concepts = payload
    else:
        raw_concepts = None

    if not isinstance(raw_concepts, list):
        raise ConceptExtractionError("response did not contain a concepts array")

    concepts: list[dict] = []
    seen: set[str] = set()
    for entry in raw_concepts:
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("name") or "").strip()
        if not name or name.lower() in seen:
            continue
        seen.add(name.lower())

        prerequisites = [
            str(prerequisite).strip()
            for prerequisite in entry.get("prerequisites") or []
            if str(prerequisite).strip()
        ]
        concepts.append(
            {
                "name": name,
                "description": str(entry.get("description") or "").strip(),
                "difficulty_level": _coerce_difficulty(entry.get("difficulty_level")),
                "prerequisites": prerequisites,
            }
        )

    if not concepts:
        raise ConceptExtractionError("response contained no usable concepts")

    concepts = concepts[:MAX_CONCEPTS]
    known = {concept["name"].lower() for concept in concepts}
    for concept in concepts:
        concept["prerequisites"] = [
            prerequisite
            for prerequisite in concept["prerequisites"]
            if prerequisite.lower() in known and prerequisite.lower() != concept["name"].lower()
        ]
    return concepts


def _user_prompt(text: str, subject: str) -> str:
    return (
        f"Subject: {subject}\n\n"
        "Extract the concepts taught in the following study material.\n\n"
        f"<material>\n{text[:MAX_INPUT_CHARS]}\n</material>"
    )


def extract_concepts_from_text(text: str, subject: str) -> list[dict]:
    """Return concepts extracted from ``text``.

    Each concept is ``{"name", "description", "difficulty_level", "prerequisites"}``.
    The model is asked once, and asked again with a corrective prompt if the first
    response is not parseable JSON.
    """
    if not text.strip():
        raise ConceptExtractionError("cannot extract concepts from empty text")

    client = _get_client()
    messages: list[dict] = [{"role": "user", "content": _user_prompt(text, subject)}]
    last_error: Exception | None = None

    for attempt in range(2):
        response = client.messages.create(
            model=MODEL_NAME,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=messages,
        )
        raw = _response_text(response)
        try:
            return _normalize(json.loads(_strip_code_fences(raw)))
        except (json.JSONDecodeError, ConceptExtractionError) as error:
            last_error = error
            logger.warning("concept extraction attempt %s failed: %s", attempt + 1, error)
            messages = [
                messages[0],
                {"role": "assistant", "content": raw or "(empty response)"},
                {
                    "role": "user",
                    "content": (
                        "That response was not valid JSON matching the required schema "
                        f"({error}). Reply again with the JSON object only."
                    ),
                },
            ]

    raise ConceptExtractionError(f"could not parse concepts from model response: {last_error}")
