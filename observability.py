"""Lightweight structured logging for workflow nodes (no external APM required)."""

import logging
import time
from collections.abc import Callable
from typing import Any, TypeVar

logger = logging.getLogger("agentic.workflow")

F = TypeVar("F", bound=Callable[..., Any])


def configure_logging(level: int = logging.INFO) -> None:
    if logger.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.setLevel(level)


def log_event(event: str, **fields: Any) -> None:
    """Emit one line: node name first (when present), then event, then key=value pairs."""
    parts: list[str] = ["[agentic.workflow]"]
    node = fields.get("node")
    if node is not None:
        parts.append(f"node={node}")
    parts.append(f"event={event}")
    for key, val in fields.items():
        if key == "node" or val is None:
            continue
        parts.append(f"{key}={val}")
    logger.info(" ".join(str(p) for p in parts))


def extract_gemini_usage_deltas(response: Any) -> dict[str, int]:
    """Map Gemini ``usage_metadata`` into graph state fields (for ``operator.add`` reducers)."""
    um = getattr(response, "usage_metadata", None)
    if um is None:
        return {}
    pairs = (
        ("usage_prompt_tokens", "prompt_token_count"),
        ("usage_candidates_tokens", "candidates_token_count"),
        ("usage_total_tokens", "total_token_count"),
        ("usage_cached_tokens", "cached_content_token_count"),
    )
    deltas: dict[str, int] = {}
    for state_key, attr in pairs:
        val = getattr(um, attr, None)
        if val is not None:
            deltas[state_key] = int(val)
    return deltas


def log_gemini_usage(
    *,
    call: str,
    response: Any,
    attempt_idx: int | None = None,
    node: str | None = None,
) -> None:
    """Log token counts from a Gemini ``generate_content`` response (if the API returns them)."""
    deltas = extract_gemini_usage_deltas(response)
    fields: dict[str, Any] = {"call": call}
    if node is not None:
        fields["node"] = node
    if attempt_idx is not None:
        fields["attempt_idx"] = attempt_idx
    log_keys = (
        ("usage_prompt_tokens", "prompt_token_count"),
        ("usage_candidates_tokens", "candidates_token_count"),
        ("usage_total_tokens", "total_token_count"),
        ("usage_cached_tokens", "cached_content_token_count"),
    )
    for state_key, log_key in log_keys:
        if state_key in deltas:
            fields[log_key] = deltas[state_key]
    if not deltas and getattr(response, "usage_metadata", None) is None:
        log_event("llm_usage", **fields, note="no_usage_metadata")
        return
    log_event("llm_usage", **fields)


def traced_node(name: str) -> Callable[[F], F]:
    def decorator(fn: F) -> F:
        def wrapper(state: dict) -> dict:
            t0 = time.perf_counter()
            log_event("node_start", node=name, attempt_idx=state.get("attempt_idx"))
            try:
                out = fn(state)
            except Exception:
                log_event("node_error", node=name, attempt_idx=state.get("attempt_idx"))
                raise
            elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
            log_event(
                "node_end",
                node=name,
                attempt_idx=state.get("attempt_idx"),
                duration_ms=elapsed_ms,
            )
            return out

        return wrapper  # type: ignore[return-value]

    return decorator
