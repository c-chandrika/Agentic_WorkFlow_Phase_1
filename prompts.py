OUTPUT_SCHEMA = """
Return ONLY a raw JSON array (no markdown fences, no commentary), valid UTF-8, parseable by json.loads.
Each object must have exactly these keys:
  "question": string
  "options": array of 4 distinct strings (the full answer texts, not just letters)
  "answer": string, must equal exactly one of the four strings in "options"
  "explanation": string (short rationale)
  "level": string, must be exactly "{level}"
  "topic": string, should be "{topic}"
"""

def build_prompt(topic, level, samples="", references="", eval_feedback=""):
    feedback_block = ""
    if eval_feedback.strip():
        feedback_block = f"""
Prior automated review rejected the previous batch. Produce a NEW set of 10 MCQs (fresh stems and options; do not paraphrase the failed set).
Address every point below:

{eval_feedback.strip()}

For wrong options: each should plausibly come from a specific student error (e.g. wrong formula, misread distribution, independence slip, integration bounds, algebra), not a lone magic number with no link to the stem.
"""

    return f"""
Generate 10 MCQs.

Topic: {topic}
Difficulty: {level}

Rules:
- Exactly 10 questions
- 4 options each (full text of each choice)
- "answer" must duplicate the correct option string verbatim
- Only ONE correct answer per question
- Avoid repetition across questions
- Match difficulty strictly (L2 = intermediate undergraduate probability)
- Options must be clearly distinct; wrong options should be plausible under a mistaken but coherent approach
- Avoid trivial or obvious incorrect answers
- Avoid repeating similar question patterns
- Use varied contexts (real-world, theoretical, numerical)
- Ensure answer is exactly copied from options (no rephrasing)
- Do not include markdown, explanations outside JSON, or comments
- Ensure all 10 questions test different concepts or variations
{feedback_block}
Samples:
{samples}

References:
{references}

{OUTPUT_SCHEMA.format(topic=topic, level=level)}
"""