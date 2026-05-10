"""LangGraph state machine: generate → validate → evaluate → export with retries."""

import operator
import uuid
from pathlib import Path
from typing import Annotated, Literal, TypedDict

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph

from config import CHECKPOINT_DB, MAX_RETRIES
from evaluator import llm_evaluate
from exporter import export_csv, export_json
from generator import generate_questions
from observability import log_event, traced_node
from validator import validate_questions


class WorkflowState(TypedDict, total=False):
    topic: str
    level: str
    samples: str
    references: str
    attempt_idx: int
    eval_feedback: str
    raw_generation: str
    valid: bool
    validation_message: str
    questions: list
    eval_result: str
    terminal: Literal["success", "failed"]
    usage_prompt_tokens: Annotated[int, operator.add]
    usage_candidates_tokens: Annotated[int, operator.add]
    usage_total_tokens: Annotated[int, operator.add]
    usage_cached_tokens: Annotated[int, operator.add]


def _run_token_summary_fields(state: WorkflowState) -> dict:
    return {
        "usage_prompt_tokens": state.get("usage_prompt_tokens", 0),
        "usage_candidates_tokens": state.get("usage_candidates_tokens", 0),
        "usage_total_tokens": state.get("usage_total_tokens", 0),
        "usage_cached_tokens": state.get("usage_cached_tokens", 0),
    }


@traced_node("generate")
def node_generate(state: WorkflowState) -> dict:
    raw, usage_deltas = generate_questions(
        state["topic"],
        state["level"],
        samples=state.get("samples") or "",
        references=state.get("references") or "",
        eval_feedback=state.get("eval_feedback") or "",
        attempt_idx=state.get("attempt_idx"),
    )
    out: dict = {"raw_generation": raw}
    out.update(usage_deltas)
    return out


@traced_node("validate")
def node_validate(state: WorkflowState) -> dict:
    raw = state["raw_generation"]
    n = state["attempt_idx"] + 1
    valid, result = validate_questions(raw, expected_level=state["level"])
    if not valid:
        print(f"Attempt {n}/{MAX_RETRIES}: validation failed - {result}")
        Path(f"raw_failed_attempt_{n}.txt").write_text(raw, encoding="utf-8")
        return {
            "valid": False,
            "validation_message": str(result),
            "questions": [],
        }
    return {"valid": True, "validation_message": "", "questions": result}


def route_after_validate(state: WorkflowState) -> str:
    if state.get("valid"):
        return "evaluate"
    if state["attempt_idx"] < MAX_RETRIES - 1:
        return "bump_after_validate"
    print("Failed after retries")
    return "finish_failed"


@traced_node("bump_after_validate")
def node_bump_after_validate(state: WorkflowState) -> dict:
    return {"attempt_idx": state["attempt_idx"] + 1}


@traced_node("evaluate")
def node_evaluate(state: WorkflowState) -> dict:
    qs = state["questions"]
    n = state["attempt_idx"] + 1
    eval_result, usage_deltas = llm_evaluate(qs, attempt_idx=state.get("attempt_idx"))
    updates: dict = {"eval_result": eval_result}
    updates.update(usage_deltas)
    er = eval_result or ""
    if "PASS" not in er.upper():
        print(f"Attempt {n}/{MAX_RETRIES}: eval failed - {eval_result}")
        export_json(qs, filename=f"questions_failed_attempt_{n}.json")
        updates["eval_feedback"] = er[:1000]
    return updates


def route_after_evaluate(state: WorkflowState) -> str:
    er = state.get("eval_result") or ""
    if "PASS" in er.upper():
        return "export"
    if state["attempt_idx"] < MAX_RETRIES - 1:
        return "bump_after_eval"
    print("Failed after retries")
    return "finish_failed"


@traced_node("bump_after_eval")
def node_bump_after_eval(state: WorkflowState) -> dict:
    return {"attempt_idx": state["attempt_idx"] + 1}


@traced_node("export")
def node_export(state: WorkflowState) -> dict:
    n = state["attempt_idx"] + 1
    qs = state["questions"]
    export_json(qs)
    export_csv(qs)
    suffix = f" (attempt {n}/{MAX_RETRIES})" if n > 1 else ""
    print(f"Success!{suffix}")
    return {"terminal": "success"}


@traced_node("finish_failed")
def node_finish_failed(_state: WorkflowState) -> dict:
    return {"terminal": "failed"}


def build_graph(checkpointer=None):
    g = StateGraph(WorkflowState)
    g.add_node("generate", node_generate)
    g.add_node("validate", node_validate)
    g.add_node("bump_after_validate", node_bump_after_validate)
    g.add_node("evaluate", node_evaluate)
    g.add_node("bump_after_eval", node_bump_after_eval)
    g.add_node("export", node_export)
    g.add_node("finish_failed", node_finish_failed)

    g.add_edge(START, "generate")
    g.add_edge("generate", "validate")
    g.add_conditional_edges(
        "validate",
        route_after_validate,
        {
            "evaluate": "evaluate",
            "bump_after_validate": "bump_after_validate",
            "finish_failed": "finish_failed",
        },
    )
    g.add_edge("bump_after_validate", "generate")
    g.add_conditional_edges(
        "evaluate",
        route_after_evaluate,
        {
            "export": "export",
            "bump_after_eval": "bump_after_eval",
            "finish_failed": "finish_failed",
        },
    )
    g.add_edge("bump_after_eval", "generate")
    g.add_edge("export", END)
    g.add_edge("finish_failed", END)
    return g.compile(checkpointer=checkpointer)


def run_workflow(
    topic: str,
    level: str,
    samples: str = "",
    references: str = "",
    *,
    checkpoint_db: str | None = CHECKPOINT_DB,
    thread_id: str | None = None,
) -> WorkflowState:
    tid = thread_id or uuid.uuid4().hex
    initial: WorkflowState = {
        "topic": topic,
        "level": level,
        "samples": samples,
        "references": references,
        "attempt_idx": 0,
        "eval_feedback": "",
        "usage_prompt_tokens": 0,
        "usage_candidates_tokens": 0,
        "usage_total_tokens": 0,
        "usage_cached_tokens": 0,
    }
    config = {"configurable": {"thread_id": tid}}

    if checkpoint_db:
        with SqliteSaver.from_conn_string(checkpoint_db) as checkpointer:
            graph = build_graph(checkpointer)
            final = graph.invoke(initial, config)
    else:
        graph = build_graph(checkpointer=None)
        final = graph.invoke(initial, config)

    log_event(
        "run_token_summary",
        terminal=final.get("terminal", "unknown"),
        thread_id=tid,
        checkpoint_db=checkpoint_db or "",
        **_run_token_summary_fields(final),
    )
    return final
