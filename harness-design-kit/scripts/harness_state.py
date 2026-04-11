#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from harness_lib import (
    ARTIFACT_SCHEMA_BY_FILENAME,
    STATE_DIR,
    ValidationError,
    append_event,
    build_compact_state_markdown,
    build_handoff_markdown,
    collect_compact_source_artifacts,
    current_pointer,
    initialize_artifacts,
    load_json,
    load_pointer,
    load_state,
    read_events,
    resolve_workspace_root,
    session_files,
    slugify,
    state_root,
    utc_now,
    validate_contract_artifact,
    validate_evaluation_artifact,
    validate_session_bundle,
    write_json,
    write_state,
    write_text,
)


def _print_session_summary(payload: dict[str, Any]) -> None:
    print(
        "Harness Design Kit: "
        f"{payload['session_id']} | "
        f"mode={payload.get('mode', 'unknown')} | "
        f"arch={payload.get('architecture_profile', 'unknown')} | "
        f"exec={payload.get('execution_mode', 'unknown')} | "
        f"eval={payload.get('evaluator_mode', 'unknown')} | "
        f"phase={payload.get('phase', 'unknown')} | "
        f"status={payload.get('status', 'unknown')} | "
        f"round={payload.get('current_round', 0)} | "
        f"goal={payload.get('goal', 'unknown')}"
    )


def _event_path(session_path: Path) -> Path:
    return session_path / "events.jsonl"


def _parse_json_argument(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("payload_json must decode to an object")
    return payload


MANUAL_STATE_FIELD_ENUMS = {
    "execution_mode": {"auto", "continuous", "reset"},
    "evaluator_mode": {"always", "final-pass", "edge-only", "off"},
}
MANUAL_STATE_FIELDS = {"qa_target_url", "qa_flow_path", *MANUAL_STATE_FIELD_ENUMS.keys()}


def _mutate_state(
    session_ref: str | None,
    updates: dict[str, Any],
    event_type: str | None = None,
    event_payload: dict[str, Any] | None = None,
) -> int:
    session_path, state = load_state(session_ref)
    state.update(updates)
    validate_session_bundle(session_path, state)
    write_state(session_path, state)
    if event_type:
        append_event(
            _event_path(session_path),
            {
                "ts": utc_now(),
                "type": event_type,
                **(event_payload or {}),
            },
        )
    return 0


def _candidate_entries(state: dict[str, Any]) -> list[dict[str, Any]]:
    entries = state.get("candidates", [])
    if isinstance(entries, list):
        return [entry for entry in entries if isinstance(entry, dict)]
    return []


def _candidate_index(entries: list[dict[str, Any]], candidate_id: str) -> int:
    for index, entry in enumerate(entries):
        if entry.get("candidate_id") == candidate_id:
            return index
    return -1


def _upsert_candidate(entries: list[dict[str, Any]], candidate: dict[str, Any]) -> list[dict[str, Any]]:
    index = _candidate_index(entries, str(candidate.get("candidate_id", "")))
    if index >= 0:
        merged = dict(entries[index])
        merged.update(candidate)
        entries[index] = merged
        return entries
    entries.append(candidate)
    return entries


def init_session(label: str, mode: str, architecture_profile: str | None) -> int:
    if mode not in {"app", "frontend"}:
        raise ValueError("mode must be one of: app, frontend")
    if architecture_profile is None:
        architecture_profile = "continuous" if mode == "frontend" else "sprint"
    if architecture_profile not in {"sprint", "continuous"}:
        raise ValueError("architecture_profile must be one of: sprint, continuous")

    root = state_root()
    base_session_id = f"{datetime.now().strftime('%Y-%m-%dT%H-%M-%S')}-{slugify(label)}"
    session_id = base_session_id
    session_path = root / "sessions" / session_id
    suffix = 2
    while session_path.exists():
        session_id = f"{base_session_id}-{suffix}"
        session_path = root / "sessions" / session_id
        suffix += 1
    session_path.mkdir(parents=True, exist_ok=True)

    state = {
        "session_id": session_id,
        "session_path": str(Path(STATE_DIR) / "sessions" / session_id),
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "status": "in_progress",
        "phase": "clarify",
        "goal": label,
        "mode": mode,
        "architecture_profile": architecture_profile,
        "execution_mode": "auto",
        "evaluator_mode": "always",
        "contract_status": "none" if mode == "frontend" and architecture_profile == "continuous" else "draft",
        "current_round": 0,
        "current_candidate_id": None,
        "best_candidate_id": None,
        "parent_session_id": None,
        "resumed_from_handoff": False,
        "active_strategy": "idle",
        "last_reset_reason": "",
        "last_evaluator_run": "",
        "last_evaluation_verdict": "",
        "last_evaluation_scores": [],
        "last_evaluation_weighted_average": None,
        "last_evaluation_weighted_threshold": None,
        "last_evaluation_priority_criteria": [],
        "last_evaluation_decision_basis": "",
        "last_evaluation_threshold_misses": [],
        "last_evaluation_artifacts": [],
        "last_evaluation_recommendation": "",
        "needs_evaluation": False,
        "final_pass_requested": False,
        "last_live_eval_artifact": "",
        "qa_target_url": "",
        "qa_flow_path": "",
        "context_strategy": "full",
        "last_compaction_reason": "",
        "last_compaction_at": "",
        "last_compaction_artifact": "",
        "compaction_count": 0,
        "compaction_resume_count": 0,
        "last_compaction_actor": "",
        "last_compaction_model": "",
        "last_runner_provider": "",
        "last_runner_model": "",
        "consecutive_runner_failures": 0,
        "compaction_cycle_failures": 0,
        "compact_source_artifacts": [],
        "last_contract_review_artifact": "",
        "last_contract_review_decision": "",
        "last_contract_review_findings": [],
        "candidate_sequence": 0,
        "round_budget": 3 if mode == "frontend" else 1,
        "candidates": [],
        "limitations": [
            "local workflow only",
            "no hosted resume service",
            "no dedicated sandbox pool",
            "no credential vault or proxy",
        ],
        "artifacts": session_files(session_path),
    }

    write_state(session_path, state)
    initialize_artifacts(
        session_path,
        {
            "goal": label,
            "mode": mode,
            "session_id": session_id,
            "architecture_profile": architecture_profile,
            "created_at": state["created_at"],
        },
    )
    append_event(
        _event_path(session_path),
        {
            "ts": utc_now(),
            "type": "session_initialized",
            "goal": label,
            "mode": mode,
            "architecture_profile": architecture_profile,
            "execution_mode": state["execution_mode"],
            "evaluator_mode": state["evaluator_mode"],
        },
    )
    validate_session_bundle(session_path, state)
    print(session_id)
    return 0


def summary(session_ref: str | None) -> int:
    if session_ref is None:
        pointer = load_pointer()
        if not pointer:
            print("Harness Design Kit: no active session")
            return 0
    _, state = load_state(session_ref)
    _print_session_summary(state)
    return 0


def validate(session_ref: str | None) -> int:
    session_path, state = load_state(session_ref)
    validated = validate_session_bundle(session_path, state)
    print(f"Validated {session_path.name}: {', '.join(validated)}")
    return 0


def append_session_event(session_ref: str | None, event_type: str, payload_json: str | None) -> int:
    session_path, _ = load_state(session_ref)
    payload = _parse_json_argument(payload_json)
    append_event(
        _event_path(session_path),
        {
            "ts": utc_now(),
            "type": event_type,
            **payload,
        },
    )
    print(f"Appended event {event_type} to {session_path.name}")
    return 0


def set_field(session_ref: str | None, field_name: str, value: Any) -> int:
    if field_name not in MANUAL_STATE_FIELDS:
        allowed = ", ".join(sorted(MANUAL_STATE_FIELDS))
        raise ValidationError(
            f"{field_name} cannot be changed with the generic setter; use a dedicated command. "
            f"Allowed fields: {allowed}"
        )
    if field_name in MANUAL_STATE_FIELD_ENUMS and value not in MANUAL_STATE_FIELD_ENUMS[field_name]:
        allowed = ", ".join(sorted(MANUAL_STATE_FIELD_ENUMS[field_name]))
        raise ValueError(f"{field_name} must be one of: {allowed}")
    return _mutate_state(
        session_ref,
        {field_name: value},
        event_type="state_updated",
        event_payload={"field": field_name, "value": value},
    )


def approve_contract(session_ref: str | None, approved_by: str) -> int:
    session_path, state = load_state(session_ref)
    if state.get("phase") != "contract":
        raise ValidationError("approve-contract is only valid during the contract phase")
    if state.get("contract_status") != "proposed":
        raise ValidationError("approve-contract requires contract_status=proposed")
    validate_contract_artifact(session_path)
    return _mutate_state(
        session_ref,
        {"contract_status": "approved"},
        event_type="contract_approved",
        event_payload={"approved_by": approved_by},
    )


def reject_contract(session_ref: str | None, reason: str) -> int:
    _, state = load_state(session_ref)
    if state.get("phase") != "contract":
        raise ValidationError("reject-contract is only valid during the contract phase")
    if state.get("contract_status") != "proposed":
        raise ValidationError("reject-contract requires contract_status=proposed")
    return _mutate_state(
        session_ref,
        {"contract_status": "rejected"},
        event_type="contract_rejected",
        event_payload={"reason": reason},
    )


def propose_contract(session_ref: str | None, proposed_by: str) -> int:
    session_path, state = load_state(session_ref)
    if state.get("phase") != "contract":
        raise ValidationError("propose-contract is only valid during the contract phase")
    if state.get("contract_status") not in {"draft", "rejected"}:
        raise ValidationError("propose-contract requires contract_status=draft or rejected")
    validate_contract_artifact(session_path)
    return _mutate_state(
        session_ref,
        {"contract_status": "proposed"},
        event_type="contract_proposed",
        event_payload={"proposed_by": proposed_by},
    )


def record_evaluation(session_ref: str | None, verdict: str, evaluator: str | None) -> int:
    session_path, state = load_state(session_ref)
    if state.get("phase") != "evaluate":
        raise ValidationError("record-evaluation is only valid during the evaluate phase")
    if verdict not in {"pass", "fail", "revise", "pivot"}:
        raise ValueError("verdict must be one of: pass, fail, revise, pivot")
    evaluation = validate_evaluation_artifact(session_path, state, verdict)
    updates = {
        "last_evaluator_run": utc_now(),
        "last_evaluation_verdict": verdict,
        "last_evaluation_scores": evaluation["scores"],
        "last_evaluation_weighted_average": evaluation["weighted_average"],
        "last_evaluation_weighted_threshold": evaluation["weighted_threshold"],
        "last_evaluation_priority_criteria": evaluation["priority_criteria"],
        "last_evaluation_decision_basis": evaluation["decision_basis"],
        "last_evaluation_threshold_misses": evaluation["threshold_misses"],
        "last_evaluation_artifacts": evaluation["artifact_refs"],
        "last_evaluation_recommendation": evaluation["recommendation_action"],
        "needs_evaluation": False,
        "final_pass_requested": False,
        "context_strategy": "full",
    }
    if state.get("mode") == "frontend":
        candidate_entries = _candidate_entries(state)
        recommendation_action = evaluation["recommendation_action"]
        updates["active_strategy"] = recommendation_action if recommendation_action in {"refine", "pivot", "accept"} else state.get("active_strategy", "idle")
        if recommendation_action == "accept" and state.get("current_candidate_id"):
            updates["best_candidate_id"] = state["current_candidate_id"]
        current_candidate_id = str(state.get("current_candidate_id") or "")
        if current_candidate_id:
            candidate_status = "active"
            if recommendation_action == "accept":
                candidate_status = "accepted"
            elif recommendation_action == "pivot":
                candidate_status = "superseded"
            candidate_entries = _upsert_candidate(
                candidate_entries,
                {
                    "candidate_id": current_candidate_id,
                    "parent_candidate_id": next(
                        (
                            entry.get("parent_candidate_id")
                            for entry in candidate_entries
                            if entry.get("candidate_id") == current_candidate_id
                        ),
                        None,
                    ),
                    "round_started": int(state.get("current_round", 0) or 0),
                    "strategy": recommendation_action if recommendation_action in {"refine", "pivot", "accept"} else state.get("active_strategy", "idle"),
                    "status": candidate_status,
                    "last_verdict": verdict,
                    "last_recommendation": recommendation_action,
                    "last_weighted_average": evaluation["weighted_average"],
                },
            )
            updates["candidates"] = candidate_entries
    payload = {"verdict": verdict}
    if evaluator:
        payload["evaluator"] = evaluator
    if evaluation["threshold_misses"]:
        payload["threshold_misses"] = evaluation["threshold_misses"]
    state.update(updates)
    validate_session_bundle(session_path, state)
    write_state(session_path, state)
    append_event(
        _event_path(session_path),
        {
            "ts": utc_now(),
            "type": "evaluation_recorded",
            **payload,
        },
    )
    return 0


def start_round(session_ref: str | None, candidate_id: str | None) -> int:
    session_path, state = load_state(session_ref)
    if state.get("mode") != "frontend":
        raise ValidationError("start-round is intended for frontend sessions")
    next_round = int(state.get("current_round", 0)) + 1
    current_candidate = str(state.get("current_candidate_id") or "")
    if candidate_id:
        candidate = candidate_id
    elif current_candidate and state.get("active_strategy") != "pivot":
        candidate = current_candidate
    else:
        next_sequence = int(state.get("candidate_sequence", 0) or 0) + 1
        state["candidate_sequence"] = next_sequence
        candidate = f"candidate-r{next_round}-{next_sequence}"
    parent_candidate_id = None
    if current_candidate and current_candidate != candidate and state.get("active_strategy") == "pivot":
        parent_candidate_id = current_candidate
    state["current_round"] = next_round
    state["current_candidate_id"] = candidate
    state["active_strategy"] = "refine" if state.get("active_strategy") == "idle" else state.get("active_strategy")
    entries = _candidate_entries(state)
    existing_parent = next(
        (
            entry.get("parent_candidate_id")
            for entry in entries
            if entry.get("candidate_id") == candidate
        ),
        None,
    )
    state["candidates"] = _upsert_candidate(
        entries,
        {
            "candidate_id": candidate,
            "parent_candidate_id": parent_candidate_id if parent_candidate_id is not None else existing_parent,
            "round_started": next_round,
            "strategy": "initial" if next_round == 1 and not current_candidate else state.get("active_strategy", "refine"),
            "status": "active",
            "last_verdict": "",
            "last_recommendation": "",
            "last_weighted_average": None,
        },
    )
    validate_session_bundle(session_path, state)
    write_state(session_path, state)
    append_event(
        _event_path(session_path),
        {
            "ts": utc_now(),
            "type": "round_started",
            "round": next_round,
            "candidate_id": candidate,
        },
    )
    print(f"Started round {next_round} with {candidate}")
    return 0


def finish_round(session_ref: str | None, decision: str, candidate_id: str | None) -> int:
    session_path, state = load_state(session_ref)
    if decision not in {"refine", "pivot", "accept"}:
        raise ValueError("decision must be one of: refine, pivot, accept")
    candidate = candidate_id or state.get("current_candidate_id")
    state["active_strategy"] = decision
    if candidate:
        state["current_candidate_id"] = candidate
    if decision == "accept" and candidate:
        state["best_candidate_id"] = candidate
    entries = _candidate_entries(state)
    if candidate:
        status = "accepted" if decision == "accept" else ("superseded" if decision == "pivot" else "active")
        state["candidates"] = _upsert_candidate(
            entries,
            {
                "candidate_id": candidate,
                "parent_candidate_id": next(
                    (
                        entry.get("parent_candidate_id")
                        for entry in entries
                        if entry.get("candidate_id") == candidate
                    ),
                    None,
                ),
                "round_started": int(state.get("current_round", 0) or 0),
                "strategy": decision,
                "status": status,
                "last_verdict": next(
                    (
                        entry.get("last_verdict", "")
                        for entry in entries
                        if entry.get("candidate_id") == candidate
                    ),
                    "",
                ),
                "last_recommendation": decision,
                "last_weighted_average": next(
                    (
                        entry.get("last_weighted_average")
                        for entry in entries
                        if entry.get("candidate_id") == candidate
                    ),
                    None,
                ),
            },
        )
    validate_session_bundle(session_path, state)
    write_state(session_path, state)
    append_event(
        _event_path(session_path),
        {
            "ts": utc_now(),
            "type": "round_finished",
            "round": state.get("current_round", 0),
            "candidate_id": candidate,
            "decision": decision,
        },
    )
    print(f"Finished round {state.get('current_round', 0)} with decision={decision}")
    return 0


def mark_best_candidate(session_ref: str | None, candidate_id: str) -> int:
    return _mutate_state(
        session_ref,
        {"best_candidate_id": candidate_id},
        event_type="best_candidate_marked",
        event_payload={"candidate_id": candidate_id},
    )


def request_evaluation(session_ref: str | None, reason: str) -> int:
    return _mutate_state(
        session_ref,
        {"needs_evaluation": True},
        event_type="evaluation_requested",
        event_payload={"reason": reason},
    )


def request_final_pass(session_ref: str | None, reason: str) -> int:
    return _mutate_state(
        session_ref,
        {
            "needs_evaluation": True,
            "final_pass_requested": True,
        },
        event_type="final_pass_requested",
        event_payload={"reason": reason},
    )


def set_live_eval_artifact(session_ref: str | None, artifact_path: str) -> int:
    return _mutate_state(
        session_ref,
        {"last_live_eval_artifact": artifact_path},
        event_type="live_eval_artifact_recorded",
        event_payload={"artifact_path": artifact_path},
    )


def write_handoff(session_ref: str | None, reason: str) -> int:
    session_path, state = load_state(session_ref)
    content = build_handoff_markdown(state, session_path, reason)
    write_text(session_path / "handoff.md", content)
    validate_session_bundle(session_path, state)
    append_event(
        _event_path(session_path),
        {
            "ts": utc_now(),
            "type": "handoff_written",
            "reason": reason,
        },
    )
    print(f"Wrote handoff for {session_path.name}")
    return 0


def prepare_reset(session_ref: str | None, reason: str) -> int:
    session_path, state = load_state(session_ref)
    state["execution_mode"] = "reset"
    state["context_strategy"] = "full"
    state["phase"] = "handoff"
    state["status"] = "paused"
    state["last_reset_reason"] = reason
    content = build_handoff_markdown(state, session_path, reason)
    write_text(session_path / "handoff.md", content)
    validate_session_bundle(session_path, state)
    write_state(session_path, state)
    append_event(
        _event_path(session_path),
        {
            "ts": utc_now(),
            "type": "reset_prepared",
            "reason": reason,
        },
    )
    print(f"Prepared reset for {session_path.name}")
    return 0


def prepare_compaction(session_ref: str | None, reason: str) -> int:
    import harness_run

    session_path, state = load_state(session_ref)
    next_actor, next_action = harness_run.recommend_next_actor(state)
    source_artifacts = collect_compact_source_artifacts(session_path, state)
    state["context_strategy"] = "compact"
    state["last_compaction_reason"] = reason
    state["last_compaction_at"] = utc_now()
    state["last_compaction_artifact"] = "compact-state.md"
    state["last_compaction_actor"] = ""
    state["last_compaction_model"] = ""
    state["compaction_count"] = int(state.get("compaction_count", 0)) + 1
    state["compaction_cycle_failures"] = 0
    state["compact_source_artifacts"] = source_artifacts
    content = build_compact_state_markdown(
        state,
        session_path,
        reason,
        next_actor=next_actor,
        next_action=next_action,
        source_artifacts=source_artifacts,
    )
    write_text(session_path / "compact-state.md", content)
    validate_session_bundle(session_path, state)
    write_state(session_path, state)
    append_event(
        _event_path(session_path),
        {
            "ts": utc_now(),
            "type": "compaction_prepared",
            "reason": reason,
            "count": state["compaction_count"],
            "next_actor": next_actor,
        },
    )
    print(f"Prepared compaction for {session_path.name}")
    return 0


def record_contract_review(
    session_ref: str | None,
    artifact_path: str,
    decision: str,
    findings: list[str],
) -> int:
    session_path, state = load_state(session_ref)
    state["last_contract_review_artifact"] = artifact_path
    state["last_contract_review_decision"] = decision
    state["last_contract_review_findings"] = findings
    validate_session_bundle(session_path, state)
    write_state(session_path, state)
    return 0


def history(session_ref: str | None, limit: int) -> int:
    session_path, _ = load_state(session_ref)
    events = read_events(_event_path(session_path))
    for event in events[-limit:]:
        print(json.dumps(event, ensure_ascii=True))
    return 0


def list_sessions(limit: int) -> int:
    sessions_root = state_root() / "sessions"
    if not sessions_root.exists():
        print("Harness Design Kit: no sessions found")
        return 0

    sessions: list[dict[str, Any]] = []
    for session_path in sessions_root.iterdir():
        if not session_path.is_dir():
            continue
        try:
            payload = load_json(session_path / "state.json")
            if not isinstance(payload, dict):
                raise ValidationError("state.json must decode to an object")
            payload.setdefault("session_id", session_path.name)
        except (FileNotFoundError, ValidationError, json.JSONDecodeError) as exc:
            payload = {
                "session_id": session_path.name,
                "status": "invalid",
                "phase": "unknown",
                "mode": "unknown",
                "goal": f"invalid state.json ({exc})",
                "updated_at": "",
            }
        sessions.append(payload)

    if not sessions:
        print("Harness Design Kit: no sessions found")
        return 0

    sessions.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
    for payload in sessions[:limit]:
        lineage = ""
        if payload.get("resumed_from_handoff") and payload.get("parent_session_id"):
            lineage = f" | parent={payload['parent_session_id']}"
        print(
            f"{payload['session_id']} | status={payload.get('status', 'unknown')} | "
            f"phase={payload.get('phase', 'unknown')} | mode={payload.get('mode', 'unknown')} | "
            f"goal={payload.get('goal', 'unknown')}{lineage}"
        )
    return 0


def select_session(session_ref: str) -> int:
    session_path, state = load_state(session_ref)
    if not isinstance(state, dict):
        raise ValidationError("state.json must decode to an object")
    validate_session_bundle(session_path, state)
    write_json(
        current_pointer(),
        {
            "session_id": state["session_id"],
            "session_path": state["session_path"],
            "updated_at": utc_now(),
        },
    )
    print(f"Selected {state['session_id']}")
    return 0


def doctor(session_ref: str | None) -> int:
    workspace_root = resolve_workspace_root()
    state_dir = state_root()
    python_path = shutil.which("python3") or ""
    node_path = shutil.which("node") or ""
    npx_path = shutil.which("npx") or ""

    print("Harness Design Kit Doctor")
    print(f"- Workspace root: {workspace_root}")
    print(f"- State root: {state_dir} ({'present' if state_dir.exists() else 'missing'})")
    print(f"- python3: {python_path or 'missing'}")
    print(f"- node: {node_path or 'missing'}")
    print(f"- npx: {npx_path or 'missing'}")

    try:
        if session_ref is None:
            pointer = load_pointer()
            if not pointer:
                print("- Current session: none")
                return 0
        session_path, state = load_state(session_ref)
        validate_session_bundle(session_path, state)
        print(
            f"- Current session: {state['session_id']} "
            f"(phase={state['phase']}, status={state['status']}, valid=yes)"
        )
        if state.get("qa_flow_path"):
            flow_path = Path(state["qa_flow_path"])
            if not flow_path.is_absolute():
                flow_path = (workspace_root / flow_path).resolve()
            print(f"- QA flow: {flow_path} ({'present' if flow_path.exists() else 'missing'})")
    except (FileNotFoundError, ValidationError, json.JSONDecodeError) as exc:
        print(f"- Current session: invalid ({exc})")
        return 1
    return 0


def resume_from_handoff(session_ref: str | None, reason: str) -> int:
    parent_session_path, parent_state = load_state(session_ref)
    handoff_path = parent_session_path / "handoff.md"
    if not handoff_path.exists():
        raise ValidationError("resume-from-handoff requires handoff.md in the source session")
    if parent_state.get("phase") != "handoff" or parent_state.get("status") != "paused":
        raise ValidationError(
            "resume-from-handoff requires the source session to be paused in the handoff phase"
        )

    init_session(
        parent_state.get("goal", parent_session_path.name),
        parent_state.get("mode", "app"),
        parent_state.get("architecture_profile"),
    )
    child_session_path, child_state = load_state(None)

    for filename in ARTIFACT_SCHEMA_BY_FILENAME:
        source_path = parent_session_path / filename
        target_path = child_session_path / filename
        if source_path.exists():
            write_text(target_path, source_path.read_text(encoding="utf-8"))
    parent_artifact_dir = parent_session_path / "artifacts"
    child_artifact_dir = child_session_path / "artifacts"
    if parent_artifact_dir.exists():
        shutil.copytree(parent_artifact_dir, child_artifact_dir, dirs_exist_ok=True)

    child_contract_status = (
        "none"
        if child_state.get("mode") == "frontend" and child_state.get("architecture_profile") == "continuous"
        else "draft"
    )

    child_state.update(
        {
            "phase": "plan",
            "status": "in_progress",
            "execution_mode": "auto",
            "context_strategy": "full",
            "evaluator_mode": parent_state.get("evaluator_mode", "always"),
            "contract_status": child_contract_status,
            "current_round": parent_state.get("current_round", 0),
            "current_candidate_id": parent_state.get("current_candidate_id"),
            "best_candidate_id": parent_state.get("best_candidate_id"),
            "candidate_sequence": parent_state.get("candidate_sequence", 0),
            "round_budget": parent_state.get("round_budget", 3 if parent_state.get("mode") == "frontend" else 1),
            "candidates": parent_state.get("candidates", []),
            "parent_session_id": parent_state.get("session_id"),
            "resumed_from_handoff": True,
            "last_reset_reason": parent_state.get("last_reset_reason", ""),
            "qa_target_url": parent_state.get("qa_target_url", ""),
            "qa_flow_path": parent_state.get("qa_flow_path", ""),
            "last_contract_review_artifact": parent_state.get("last_contract_review_artifact", ""),
            "last_contract_review_decision": parent_state.get("last_contract_review_decision", ""),
            "last_contract_review_findings": parent_state.get("last_contract_review_findings", []),
            "last_compaction_actor": "",
            "last_compaction_model": "",
            "last_runner_provider": parent_state.get("last_runner_provider", ""),
            "last_runner_model": parent_state.get("last_runner_model", ""),
            "consecutive_runner_failures": 0,
            "compaction_cycle_failures": 0,
            "compact_source_artifacts": parent_state.get("compact_source_artifacts", []),
        }
    )
    write_text(
        child_session_path / "handoff.md",
        build_handoff_markdown(
            child_state,
            child_session_path,
            f"resumed from {parent_state.get('session_id', parent_session_path.name)}: {reason}",
        ),
    )
    validate_session_bundle(child_session_path, child_state)
    write_state(child_session_path, child_state)
    append_event(
        _event_path(parent_session_path),
        {
            "ts": utc_now(),
            "type": "handoff_resumed_into",
            "child_session_id": child_state["session_id"],
            "reason": reason,
        },
    )
    append_event(
        _event_path(child_session_path),
        {
            "ts": utc_now(),
            "type": "session_resumed_from_handoff",
            "parent_session_id": parent_state.get("session_id"),
            "reason": reason,
        },
    )
    print(child_state["session_id"])
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Harness Design Kit state manager")
    parser.add_argument("--session", help="Session id or path. Defaults to current session.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("label")
    init_parser.add_argument("mode", nargs="?", default="app")
    init_parser.add_argument("architecture_profile", nargs="?")

    subparsers.add_parser("summary")
    subparsers.add_parser("validate")

    append_parser = subparsers.add_parser("append-event")
    append_parser.add_argument("event_type")
    append_parser.add_argument("payload_json", nargs="?")

    for command_name, field_name in (
        ("set-execution-mode", "execution_mode"),
        ("set-evaluator-mode", "evaluator_mode"),
        ("set-qa-target", "qa_target_url"),
        ("set-qa-flow", "qa_flow_path"),
    ):
        setter = subparsers.add_parser(command_name)
        setter.add_argument("value")
        setter.set_defaults(field_name=field_name)

    approve_parser = subparsers.add_parser("approve-contract")
    approve_parser.add_argument("approved_by")

    propose_parser = subparsers.add_parser("propose-contract")
    propose_parser.add_argument("proposed_by")

    reject_parser = subparsers.add_parser("reject-contract")
    reject_parser.add_argument("reason")

    record_eval_parser = subparsers.add_parser("record-evaluation")
    record_eval_parser.add_argument("verdict")
    record_eval_parser.add_argument("evaluator", nargs="?")

    start_round_parser = subparsers.add_parser("start-round")
    start_round_parser.add_argument("candidate_id", nargs="?")

    finish_round_parser = subparsers.add_parser("finish-round")
    finish_round_parser.add_argument("decision")
    finish_round_parser.add_argument("candidate_id", nargs="?")

    best_candidate_parser = subparsers.add_parser("mark-best-candidate")
    best_candidate_parser.add_argument("candidate_id")

    eval_request_parser = subparsers.add_parser("request-evaluation")
    eval_request_parser.add_argument("reason", nargs="?", default="manual evaluator request")

    final_pass_parser = subparsers.add_parser("request-final-pass")
    final_pass_parser.add_argument("reason", nargs="?", default="final pass requested")

    live_eval_parser = subparsers.add_parser("set-live-eval-artifact")
    live_eval_parser.add_argument("artifact_path")

    handoff_parser = subparsers.add_parser("write-handoff")
    handoff_parser.add_argument("reason", nargs="?", default="manual handoff")

    reset_parser = subparsers.add_parser("prepare-reset")
    reset_parser.add_argument("reason", nargs="?", default="manual reset requested")

    compact_parser = subparsers.add_parser("prepare-compaction")
    compact_parser.add_argument("reason", nargs="?", default="manual compaction requested")

    history_parser = subparsers.add_parser("history")
    history_parser.add_argument("limit", nargs="?", type=int, default=20)

    list_parser = subparsers.add_parser("list-sessions")
    list_parser.add_argument("limit", nargs="?", type=int, default=20)

    select_parser = subparsers.add_parser("select-session")
    select_parser.add_argument("session_ref")

    subparsers.add_parser("doctor")

    resume_parser = subparsers.add_parser("resume-from-handoff")
    resume_parser.add_argument("reason", nargs="?", default="fresh context resume requested")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "init":
            return init_session(args.label, args.mode, args.architecture_profile)
        if args.command == "summary":
            return summary(args.session)
        if args.command == "validate":
            return validate(args.session)
        if args.command == "append-event":
            return append_session_event(args.session, args.event_type, args.payload_json)
        if args.command in {
            "set-execution-mode",
            "set-evaluator-mode",
            "set-qa-target",
            "set-qa-flow",
        }:
            return set_field(args.session, args.field_name, args.value)
        if args.command == "approve-contract":
            return approve_contract(args.session, args.approved_by)
        if args.command == "propose-contract":
            return propose_contract(args.session, args.proposed_by)
        if args.command == "reject-contract":
            return reject_contract(args.session, args.reason)
        if args.command == "record-evaluation":
            return record_evaluation(args.session, args.verdict, args.evaluator)
        if args.command == "start-round":
            return start_round(args.session, args.candidate_id)
        if args.command == "finish-round":
            return finish_round(args.session, args.decision, args.candidate_id)
        if args.command == "mark-best-candidate":
            return mark_best_candidate(args.session, args.candidate_id)
        if args.command == "request-evaluation":
            return request_evaluation(args.session, args.reason)
        if args.command == "request-final-pass":
            return request_final_pass(args.session, args.reason)
        if args.command == "set-live-eval-artifact":
            return set_live_eval_artifact(args.session, args.artifact_path)
        if args.command == "write-handoff":
            return write_handoff(args.session, args.reason)
        if args.command == "prepare-reset":
            return prepare_reset(args.session, args.reason)
        if args.command == "prepare-compaction":
            return prepare_compaction(args.session, args.reason)
        if args.command == "history":
            return history(args.session, args.limit)
        if args.command == "list-sessions":
            return list_sessions(args.limit)
        if args.command == "select-session":
            return select_session(args.session_ref)
        if args.command == "doctor":
            return doctor(args.session)
        if args.command == "resume-from-handoff":
            return resume_from_handoff(args.session, args.reason)
    except (FileNotFoundError, ValidationError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc))
        return 1

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
