import argparse
from pathlib import Path

from observability import configure_logging
from workflow_graph import run_workflow


def _read_text_file(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


if __name__ == "__main__":
    configure_logging()
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
    run_workflow(args.topic, args.level, samples=samples, references=references)
