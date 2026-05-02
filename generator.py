import os

import google.generativeai as genai

from config import GEMINI_MODEL, TEMPERATURE, TEMPERATURE_WITH_FEEDBACK
from prompts import build_prompt

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

model = genai.GenerativeModel(GEMINI_MODEL)


def generate_questions(topic, level, samples="", references="", eval_feedback=""):
    prompt = build_prompt(topic, level, samples, references, eval_feedback=eval_feedback)
    temp = (
        TEMPERATURE_WITH_FEEDBACK if eval_feedback.strip() else TEMPERATURE
    )

    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            temperature=temp,
            response_mime_type="application/json",
        ),
    )

    return response.text