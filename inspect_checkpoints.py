#!/usr/bin/env python3
"""
Decode LangGraph SQLite checkpoints into readable state (BLOBs are not plain JSON).

Usage:
  .venv/bin/python inspect_checkpoints.py --list-threads
  .venv/bin/python inspect_checkpoints.py --thread-id my-run-1
  .venv/bin/python inspect_checkpoints.py --thread-id my-run-1 --history 20 --json
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from langgraph.checkpoint.sqlite import SqliteSaver

from config import CHECKPOINT_DB
from workflow_graph import build_graph


def list_thread_ids(db_path: str) -> list[str]:
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "SELECT DISTINCT thread_id FROM checkpoints ORDER BY thread_id"
        ).fetchall()
    finally:
        con.close()
    return [r[0] for r in rows]


def compact_values(values: dict | None) -> dict:
    """Shrink large fields for terminal viewing."""
    if not values:
        return {}
    out: dict = {}
    for key, val in values.items():
        if key == "questions" and isinstance(val, list):
            out[key] = f"<list len={len(val)}>"
        elif key == "raw_generation" and isinstance(val, str):
            tail = "..." if len(val) > 200 else ""
            out[key] = val[:200] + tail
        elif key == "samples" and isinstance(val, str) and len(val) > 120:
            out[key] = val[:120] + "..."
        elif key == "references" and isinstance(val, str) and len(val) > 120:
            out[key] = val[:120] + "..."
        else:
            out[key] = val
    return out


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect LangGraph checkpoint state (decoded, not raw SQLite BLOBs)."
    )
    parser.add_argument(
        "--db",
        default=CHECKPOINT_DB,
        help=f"SQLite path (default: config CHECKPOINT_DB / env AGENTIC_CHECKPOINT_DB, else {CHECKPOINT_DB!r})",
    )
    parser.add_argument("--thread-id", metavar="ID", help="Thread to inspect")
    parser.add_argument(
        "--list-threads",
        action="store_true",
        help="Print distinct thread_id values in the DB and exit",
    )
    parser.add_argument(
        "--history",
        type=int,
        metavar="N",
        default=0,
        help="Also print last N checkpoints (newest first); 0 = only latest",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print values as JSON (still compacts questions/raw_generation unless --full)",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="With --json, dump full state (large)",
    )
    args = parser.parse_args()
    db_path = Path(args.db)
    if not db_path.is_file():
        print(f"No database file: {db_path.resolve()}", file=sys.stderr)
        return 1

    if args.list_threads:
        for tid in list_thread_ids(str(db_path)):
            print(tid)
        return 0

    if not args.thread_id:
        print("Provide --thread-id ID or use --list-threads", file=sys.stderr)
        return 1

    config = {"configurable": {"thread_id": args.thread_id}}

    with SqliteSaver.from_conn_string(str(db_path)) as checkpointer:
        graph = build_graph(checkpointer)
        snap = graph.get_state(config)

    if args.json:
        vals = dict(snap.values) if snap.values else {}
        if not args.full:
            if isinstance(vals.get("questions"), list):
                vals = {**vals, "questions": f"<list len={len(vals['questions'])}>"}
            if isinstance(vals.get("raw_generation"), str) and len(vals["raw_generation"]) > 500:
                rg = vals["raw_generation"]
                vals = {**vals, "raw_generation": rg[:500] + "..."}
        print(json.dumps(vals, indent=2, default=str, ensure_ascii=False))
        print("next:", list(snap.next))
        return 0

    print("thread_id:", args.thread_id)
    print("checkpoint:", snap.config.get("configurable", {}))
    print("next nodes:", snap.next)
    print("values (compact):")
    for k, v in compact_values(dict(snap.values) if snap.values else {}).items():
        print(f"  {k}: {v}")

    if args.history > 0:
        print(f"\n--- last {args.history} checkpoints (newest first) ---")
        with SqliteSaver.from_conn_string(str(db_path)) as checkpointer:
            graph = build_graph(checkpointer)
            for i, h in enumerate(graph.get_state_history(config, limit=args.history)):
                cfg = h.config.get("configurable", {})
                cid = cfg.get("checkpoint_id", "?")
                vals = compact_values(dict(h.values) if h.values else {})
                term = vals.get("terminal", "")
                att = vals.get("attempt_idx", "")
                print(f"{i + 1}. checkpoint_id={cid} attempt_idx={att} terminal={term} keys={list(vals.keys())}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
