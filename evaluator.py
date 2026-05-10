import json
import os
import re

import google.generativeai as genai

from config import GEMINI_MODEL
from observability import extract_gemini_usage_deltas, log_gemini_usage

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel(GEMINI_MODEL)


def _extract_json_object(text: str) -> str | None:
    text = (text or "").strip()
    m = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if m:
        return m.group(1)
    m2 = re.search(r"\{.*\}", text, re.DOTALL)
    if m2:
        return m2.group(0)
    return None


def llm_evaluate(questions, attempt_idx=None) -> tuple[str, dict[str, int]]:
    payload = json.dumps(questions, ensure_ascii=False, indent=2)
    prompt = f"""
Evaluate these MCQs.

FAIL the batch ONLY if there is a serious problem, such as:
- wrong keyed answer or explanation contradicts the marked answer
- more than one option is defensibly correct, or the stem is ambiguous in a way that changes the answer
- question is off-topic or clearly not L2-level for undergraduate probability
- garbled or unreadable stem/options

Do NOT fail for: mild distractor nitpicks, "could be stronger" wording, or stylistic preferences.
Wrong options need only be plausible mistakes, not each labeled with a named error story.

Return ONLY strict JSON (no markdown fences):
{{
  "status": "PASS",
  "issues": []
}}
or
{{
  "status": "FAIL",
  "issues": ["short issue descriptions"]
}}

MCQs (JSON array):
{payload}
"""
    res = model.generate_content(prompt)
    deltas = extract_gemini_usage_deltas(res)
    log_gemini_usage(
        call="llm_evaluate",
        response=res,
        attempt_idx=attempt_idx,
        node="evaluate",
    )
    text = (res.text or "").strip()
    if not text:
        fb = getattr(res, "prompt_feedback", None)
        return f"FAIL: empty model response; prompt_feedback={fb}", deltas

    blob = _extract_json_object(text)
    if blob:
        try:
            data = json.loads(blob)
        except json.JSONDecodeError:
            return text, deltas
        status = (data.get("status") or "").strip().upper()
        issues = data.get("issues") or []
        if status == "PASS":
            return "PASS", deltas
        if status == "FAIL":
            return "FAIL: " + "; ".join(str(i) for i in issues), deltas
    first = (text.split(None, 1)[0] if text else "").upper()
    if first == "PASS":
        return "PASS", deltas
    return text, deltas
