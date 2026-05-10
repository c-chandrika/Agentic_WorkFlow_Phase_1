"""Decode LangGraph SQLite checkpoints (BLOBs require the graph + SqliteSaver to read)."""

import argparse
import json
import sqlite3
import sys
from argparse import Namespace
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


def run_inspect(ns: Namespace) -> int:
    db_path = Path(ns.db)
    if not db_path.is_file():
        print(f"No database file: {db_path.resolve()}", file=sys.stderr)
        return 1

    if ns.list_threads:
        for tid in list_thread_ids(str(db_path)):
            print(tid)
        return 0

    if not ns.thread_id:
        print("Provide --thread-id ID or use --list-threads", file=sys.stderr)
        return 1

    config = {"configurable": {"thread_id": ns.thread_id}}

    with SqliteSaver.from_conn_string(str(db_path)) as checkpointer:
        graph = build_graph(checkpointer)
        snap = graph.get_state(config)

    if ns.json:
        vals = dict(snap.values) if snap.values else {}
        if not ns.full:
            if isinstance(vals.get("questions"), list):
                vals = {**vals, "questions": f"<list len={len(vals['questions'])}>"}
            if isinstance(vals.get("raw_generation"), str) and len(vals["raw_generation"]) > 500:
                rg = vals["raw_generation"]
                vals = {**vals, "raw_generation": rg[:500] + "..."}
        print(json.dumps(vals, indent=2, default=str, ensure_ascii=False))
        print("next:", list(snap.next))
        return 0

    print("thread_id:", ns.thread_id)
    print("checkpoint:", snap.config.get("configurable", {}))
    print("next nodes:", snap.next)
    print("values (compact):")
    for k, v in compact_values(dict(snap.values) if snap.values else {}).items():
        print(f"  {k}: {v}")

    if ns.history > 0:
        print(f"\n--- last {ns.history} checkpoints (newest first) ---")
        with SqliteSaver.from_conn_string(str(db_path)) as checkpointer:
            graph = build_graph(checkpointer)
            for i, h in enumerate(graph.get_state_history(config, limit=ns.history)):
                cfg = h.config.get("configurable", {})
                cid = cfg.get("checkpoint_id", "?")
                vals = compact_values(dict(h.values) if h.values else {})
                term = vals.get("terminal", "")
                att = vals.get("attempt_idx", "")
                print(
                    f"{i + 1}. checkpoint_id={cid} attempt_idx={att} terminal={term} "
                    f"keys={list(vals.keys())}"
                )

    return 0


def build_inspect_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Decode checkpoint state from the SQLite checkpointer (not raw BLOB hex).",
    )
    p.add_argument(
        "--db",
        default=CHECKPOINT_DB,
        help=f"SQLite path (default: {CHECKPOINT_DB!r} from config / env).",
    )
    p.add_argument("--thread-id", metavar="ID", help="Thread to inspect")
    p.add_argument(
        "--list-threads",
        action="store_true",
        help="List distinct thread_id values and exit",
    )
    p.add_argument(
        "--history",
        type=int,
        metavar="N",
        default=0,
        help="Show last N checkpoints (newest first); 0 = latest only",
    )
    p.add_argument(
        "--json",
        action="store_true",
        help="Print values as JSON (truncated unless --full)",
    )
    p.add_argument(
        "--full",
        action="store_true",
        help="With --json, dump full state (can be large)",
    )
    return p
