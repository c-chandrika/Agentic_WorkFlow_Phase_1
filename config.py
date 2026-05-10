import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env", override=True)

# Gemini model id for generator + evaluator (see https://ai.google.dev/gemini-api/docs/models/gemini )
GEMINI_MODEL = "gemini-2.5-flash"

MAX_RETRIES = 2
TEMPERATURE = 0.7
# Slightly lower temperature when regenerating after evaluator feedback (attempt 2).
TEMPERATURE_WITH_FEEDBACK = 0.45

# LangGraph SqliteSaver path (override with env ``AGENTIC_CHECKPOINT_DB``).
CHECKPOINT_DB = os.getenv("AGENTIC_CHECKPOINT_DB", "workflow_checkpoints.sqlite")