import argparse
import sys
from pathlib import Path

from config import CHECKPOINT_DB
from observability import configure_logging
from workflow_graph import run_workflow


def _read_text_file(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def _build_generate_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Generate MCQs (JSON + CSV) using topic, level, optional samples/references, optional RAG.",
        epilog="Inspect checkpoints:  python main.py inspect-checkpoints --help",
    )
    p.formatter_class = argparse.RawDescriptionHelpFormatter
    p.add_argument("topic", nargs="?", default="Probability", help="Subject topic")
    p.add_argument("level", nargs="?", default="L2", help="Difficulty e.g. L1, L2, L3")
    p.add_argument(
        "--samples",
        default="",
        metavar="TEXT",
        help="Example questions or style notes (inline). Ignored if --samples-file is set.",
    )
    p.add_argument(
        "--references",
        default="",
        metavar="TEXT",
        help="Syllabus snippets, book refs, formulas (inline). Ignored if --references-file is set.",
    )
    p.add_argument(
        "--samples-file",
        metavar="PATH",
        help="UTF-8 file whose contents are passed as Samples (overrides --samples).",
    )
    p.add_argument(
        "--references-file",
        metavar="PATH",
        help="UTF-8 file whose contents are passed as References (overrides --references).",
    )
    p.add_argument(
        "--rag-dir",
        metavar="PATH",
        default=None,
        help="Directory of .txt/.md files to retrieve from (BM25); chunks are appended to References.",
    )
    p.add_argument(
        "--rag-top-k",
        type=int,
        default=5,
        metavar="N",
        help="Number of RAG chunks to append (default: 5).",
    )
    p.add_argument(
        "--no-checkpoint",
        action="store_true",
        help="Disable LangGraph SQLite checkpointing.",
    )
    p.add_argument(
        "--checkpoint-db",
        metavar="PATH",
        default=CHECKPOINT_DB,
        help=f"SQLite file for graph checkpoints (default: {CHECKPOINT_DB!r}).",
    )
    p.add_argument(
        "--thread-id",
        metavar="ID",
        default=None,
        help="Stable thread id for checkpoint history (default: random).",
    )
    return p


def _run_generate(args: argparse.Namespace) -> None:
    samples = _read_text_file(args.samples_file) if args.samples_file else args.samples
    references = (
        _read_text_file(args.references_file) if args.references_file else args.references
    )
    if args.rag_dir:
        from rag_retrieval import augment_references_with_rag

        references = augment_references_with_rag(
            args.topic,
            references,
            Path(args.rag_dir),
            top_k=args.rag_top_k,
        )
    run_workflow(
        args.topic,
        args.level,
        samples=samples,
        references=references,
        checkpoint_db=None if args.no_checkpoint else args.checkpoint_db,
        thread_id=args.thread_id,
    )


if __name__ == "__main__":
    configure_logging()
    argv = sys.argv[1:]
    if argv and argv[0] == "inspect-checkpoints":
        from checkpoint_inspection import build_inspect_parser, run_inspect

        sys.argv.pop(1)
        raise SystemExit(run_inspect(build_inspect_parser().parse_args()))

    gen = _build_generate_parser()
    _run_generate(gen.parse_args())
