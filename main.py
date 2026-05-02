import argparse
from pathlib import Path

from config import MAX_RETRIES
from generator import generate_questions
from validator import validate_questions
from evaluator import llm_evaluate
from exporter import export_csv, export_json


def _read_text_file(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def run(topic, level, samples="", references=""):
    eval_feedback = ""
    for attempt in range(MAX_RETRIES):
        n = attempt + 1
        raw = generate_questions(
            topic,
            level,
            samples=samples,
            references=references,
            eval_feedback=eval_feedback,
        )

        valid, result = validate_questions(raw, expected_level=level)

        if not valid:
            print(f"Attempt {n}/{MAX_RETRIES}: validation failed - {result}")
            Path(f"raw_failed_attempt_{n}.txt").write_text(raw)
            continue

        eval_result = llm_evaluate(result)

        if "PASS" in (eval_result or "").upper():            
            suffix = f" (attempt {n}/{MAX_RETRIES})" if n > 1 else ""
            print(f"Success!{suffix}")
            export_json(result)
            export_csv(result)
            return

        print(f"Attempt {n}/{MAX_RETRIES}: eval failed - {eval_result}")
        export_json(result, filename=f"questions_failed_attempt_{n}.json")
        eval_feedback = (eval_result or "")[:1000]  # limit size

    print("Failed after retries")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate MCQs (JSON + CSV) using topic, level, optional samples/references."
    )
    parser.add_argument("topic", nargs="?", default="Probability", help="Subject topic")
    parser.add_argument("level", nargs="?", default="L2", help="Difficulty e.g. L1, L2, L3")
    parser.add_argument(
        "--samples",
        default="",
        metavar="TEXT",
        help="Example questions or style notes (inline). Ignored if --samples-file is set.",
    )
    parser.add_argument(
        "--references",
        default="",
        metavar="TEXT",
        help="Syllabus snippets, book refs, formulas (inline). Ignored if --references-file is set.",
    )
    parser.add_argument(
        "--samples-file",
        metavar="PATH",
        help="UTF-8 file whose contents are passed as Samples (overrides --samples).",
    )
    parser.add_argument(
        "--references-file",
        metavar="PATH",
        help="UTF-8 file whose contents are passed as References (overrides --references).",
    )
    args = parser.parse_args()
    samples = _read_text_file(args.samples_file) if args.samples_file else args.samples
    references = (
        _read_text_file(args.references_file) if args.references_file else args.references
    )
    run(args.topic, args.level, samples=samples, references=references)