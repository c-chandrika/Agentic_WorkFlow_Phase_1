import json
import re

REQUIRED_KEYS = frozenset(
    {"question", "options", "answer", "explanation", "level", "topic"}
)


def parse_questions_json(raw):
    """
    Extract the first JSON array from model output and decode it.
    Uses JSONDecoder.raw_decode so ']' inside strings does not break parsing.
    Returns (questions, None) on success, or (None, error_message).
    """
    text = (raw or "").strip().lstrip("\ufeff")
    if "```" in text:
        for chunk in text.split("```"):
            c = chunk.strip()
            if c.lower().startswith("json"):
                c = c[4:].strip()
            if c.startswith("["):
                text = c
                break
    i = text.find("[")
    if i == -1:
        return None, "No JSON array found (missing '[')"
    decoder = json.JSONDecoder()
    try:
        questions, _end = decoder.raw_decode(text, i)
    except json.JSONDecodeError as e:
        return None, f"JSON parse error: {e.msg} (line {e.lineno}, col {e.colno})"
    if not isinstance(questions, list):
        return None, "JSON root is not an array"
    return questions, None


def extract_json(text):
    """Legacy helper: return substring that raw_decode would use (for debugging)."""
    text = (text or "").strip().lstrip("\ufeff")
    if "```" in text:
        for chunk in text.split("```"):
            c = chunk.strip()
            if c.lower().startswith("json"):
                c = c[4:].strip()
            if c.startswith("["):
                return c
    m = re.search(r"\[", text)
    if not m:
        return text
    decoder = json.JSONDecoder()
    try:
        _obj, end = decoder.raw_decode(text, m.start())
        return text[m.start() : end]
    except json.JSONDecodeError:
        return text[m.start() :]


def validate_questions(raw, expected_level=None):
    questions, parse_err = parse_questions_json(raw)
    if parse_err:
        return False, parse_err

    if len(questions) != 10:
        return False, f"Expected 10 questions, got {len(questions)}"

    for i, q in enumerate(questions):
        if not isinstance(q, dict):
            return False, f"Question {i} is not an object"
        missing = REQUIRED_KEYS - q.keys()
        if missing:
            return False, f"Question {i} missing keys: {sorted(missing)}"
        opts = q["options"]
        if not isinstance(opts, list) or len(opts) != 4:
            return False, f"Question {i} must have exactly 4 string options"
        if len(set(opts)) != 4:
            return False, f"Question {i} options must be distinct"
        if not all(isinstance(o, str) and o.strip() for o in opts):
            return False, f"Question {i} options must be non-empty strings"
        ans = q.get("answer")
        if not isinstance(ans, str) or not ans.strip():
            return False, f"Question {i} needs a non-empty answer"
        if ans.strip() not in [o.strip() for o in opts]:
            return False, f"Question {i} answer must match one option"
        if expected_level and q.get("level") != expected_level:
            return False, f"Question {i} level must be {expected_level}"
        if len(q["question"].strip()) < 10:
            return False, f"Question {i} too short"

    return True, questions
