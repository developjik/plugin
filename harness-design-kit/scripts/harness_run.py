#!/usr/bin/env python3

from __future__ import annotations

import argparse

from harness_lib import (
    ValidationError,
    append_event,
    build_compact_state_markdown,
    build_handoff_markdown,
    collect_compact_source_artifacts,
    load_state,
    read_events,
    utc_now,
    validate_contract_artifact,
    validate_session_bundle,
    write_state,
    write_text,
)


RESET_FAIL_THRESHOLD = 2
RESET_SIGNAL_THRESHOLD = 3
COMPACTION_FAIL_THRESHOLD = 1
COMPACTION_SIGNAL_THRESHOLD = 2


def event_path(session_path):
    return session_path / "events.jsonl"


def recommend_next_actor(state):
    phase = state.get("phase")
    mode = state.get("mode")
    contract_status = state.get("contract_status")
    if phase in {"clarify", "plan"}:
        return "planner", "Expand or refine the product spec before implementation."
    if phase == "contract":
        if contract_status in {"none", "draft", "rejected"}:
            return "generator", "Draft or revise the sprint contract."
        if contract_status == "proposed":
            return "qa-evaluator", "Review the contract and approve or reject it."
        return "generator", "Implement the approved contract."
    if phase == "build":
        return "generator", "Implement the active scope and record progress."
    if phase == "evaluate":
        evaluator = "design-evaluator" if mode == "frontend" else "qa-evaluator"
        return evaluator, "Evaluate the live system and record a scored verdict."
    if phase == "handoff":
        return "planner", "Resume from handoff artifacts in a fresh context."
    return "none", "Session is complete."


def status(session_ref: str | None) -> int:
    session_path, state = load_state(session_ref)
    validate_session_bundle(session_path, state)
    actor, action = recommend_next_actor(state)
    print(
        f"Session {state['session_id']} | phase={state['phase']} | "
        f"contract={state.get('contract_status', 'n/a')} | "
        f"round={state.get('current_round', 0)} | "
        f"last_verdict={state.get('last_evaluation_verdict', '') or 'none'}"
    )
    print(f"Next actor: {actor}")
    print(f"Suggested action: {action}")
    return 0


def advance(session_ref: str | None) -> int:
    session_path, state = load_state(session_ref)
    current_phase = state.get("phase")
    mode = state.get("mode", "app")
    architecture_profile = state.get("architecture_profile", "sprint")
    contract_status = state.get("contract_status", "none")
    verdict = state.get("last_evaluation_verdict", "")
    evaluator_mode = state.get("evaluator_mode", "always")

    if current_phase == "clarify":
        next_phase = "plan"
    elif current_phase == "plan":
        if mode == "app":
            next_phase = "contract"
            if contract_status == "none":
                state["contract_status"] = "draft"
        else:
            next_phase = "build" if architecture_profile == "continuous" else "contract"
    elif current_phase == "contract":
        if contract_status != "approved":
            raise ValidationError("contract phase cannot advance until contract_status=approved")
        validate_contract_artifact(session_path)
        next_phase = "build"
    elif current_phase == "build":
        if evaluator_mode == "always":
            next_phase = "evaluate"
        elif evaluator_mode == "final-pass":
            if not state.get("final_pass_requested"):
                raise ValidationError(
                    "final-pass mode requires request-final-pass before advancing from build"
                )
            next_phase = "evaluate"
        elif evaluator_mode == "edge-only":
            if state.get("needs_evaluation"):
                next_phase = "evaluate"
            else:
                next_phase = "completed" if architecture_profile == "continuous" else "plan"
                if next_phase == "completed":
                    state["status"] = "completed"
                else:
                    state["contract_status"] = "draft"
                    state["active_strategy"] = "idle"
                append_event(
                    event_path(session_path),
                    {
                        "ts": utc_now(),
                        "type": "evaluation_skipped",
                        "reason": "edge-only mode did not require evaluation for this build",
                    },
                )
        elif evaluator_mode == "off":
            next_phase = "completed" if architecture_profile == "continuous" else "plan"
            if next_phase == "completed":
                state["status"] = "completed"
            else:
                state["contract_status"] = "draft"
                state["active_strategy"] = "idle"
            append_event(
                event_path(session_path),
                {
                    "ts": utc_now(),
                    "type": "evaluation_skipped",
                    "reason": "evaluation mode is off",
                },
            )
        else:
            raise ValidationError(f"unsupported evaluator_mode: {evaluator_mode}")
    elif current_phase == "evaluate":
        if verdict == "pass":
            if architecture_profile == "continuous":
                next_phase = "completed"
                state["status"] = "completed"
            else:
                next_phase = "plan"
                state["contract_status"] = "draft"
                state["active_strategy"] = "idle"
        elif verdict == "pivot":
            next_phase = "plan"
            state["active_strategy"] = "pivot"
        elif verdict in {"fail", "revise"}:
            next_phase = "build"
            state["active_strategy"] = "refine"
        else:
            raise ValidationError("evaluate phase requires a recorded verdict before advancing")
    elif current_phase == "handoff":
        next_phase = "plan"
        state["status"] = "in_progress"
    elif current_phase == "completed":
        print("Session is already completed.")
        return 0
    else:
        raise ValidationError(f"unsupported phase: {current_phase}")

    state["phase"] = next_phase
    if current_phase == "build" and next_phase == "evaluate":
        state["needs_evaluation"] = False
    validate_session_bundle(session_path, state)
    write_state(session_path, state)
    append_event(
        event_path(session_path),
        {
            "ts": utc_now(),
            "type": "phase_advanced",
            "from_phase": current_phase,
            "to_phase": next_phase,
        },
    )
    print(f"Advanced {state['session_id']} from {current_phase} to {next_phase}")
    return 0


def _consecutive_failures(events):
    failures = 0
    for event in reversed(events):
        if event.get("type") != "evaluation_recorded":
            continue
        if event.get("verdict") in {"fail", "revise", "pivot"}:
            failures += 1
            continue
        if event.get("verdict") == "pass":
            break
    return failures


def _reset_signal_count(events):
    return sum(1 for event in events[-10:] if event.get("type") == "reset_signal")


def _frontend_iteration_budget_open(state):
    if state.get("mode") != "frontend":
        return False
    if state.get("architecture_profile") != "continuous":
        return False
    current_round = int(state.get("current_round", 0) or 0)
    round_budget = max(int(state.get("round_budget", 3) or 3), 1)
    return current_round <= round_budget


def _determine_reset_reason(state, events):
    if state.get("execution_mode") != "auto":
        return None
    if _frontend_iteration_budget_open(state):
        return None
    if int(state.get("compaction_cycle_failures", 0) or 0) >= 2:
        return "repeated compact resume failures triggered auto reset"
    compaction_count = int(state.get("compaction_count", 0) or 0)
    if compaction_count <= 0:
        return None
    if _consecutive_failures(events) >= RESET_FAIL_THRESHOLD:
        return "multiple failing evaluation cycles triggered auto reset"
    if _reset_signal_count(events) >= RESET_SIGNAL_THRESHOLD:
        return "repeated reset signals triggered auto reset"
    if state.get("contract_status") == "rejected":
        rejected_count = sum(1 for event in events[-10:] if event.get("type") == "contract_rejected")
        if rejected_count >= 2:
            return "repeated contract rejection triggered auto reset"
    return None


def _determine_compaction_reason(state, events):
    execution_mode = state.get("execution_mode")
    if execution_mode not in {"auto", "continuous"}:
        return None
    if _frontend_iteration_budget_open(state):
        return None
    recent_types = [event.get("type") for event in events[-5:]]
    if "compaction_prepared" in recent_types:
        return None
    if _consecutive_failures(events) >= COMPACTION_FAIL_THRESHOLD:
        return "failing evaluation cycle triggered compaction"
    if _reset_signal_count(events) >= COMPACTION_SIGNAL_THRESHOLD:
        return "repeated reset signals triggered compaction"
    if state.get("contract_status") == "rejected":
        rejected_count = sum(1 for event in events[-10:] if event.get("type") == "contract_rejected")
        if rejected_count >= 1:
            return "contract rejection triggered compaction"
    return None


def check_reset(session_ref: str | None, quiet: bool = False) -> int:
    session_path, state = load_state(session_ref)
    events = read_events(event_path(session_path))
    reason = _determine_reset_reason(state, events)
    if reason:
        state["execution_mode"] = "reset"
        state["context_strategy"] = "full"
        state["phase"] = "handoff"
        state["status"] = "paused"
        state["last_reset_reason"] = reason
        handoff = build_handoff_markdown(state, session_path, reason)
        write_text(session_path / "handoff.md", handoff)
        validate_session_bundle(session_path, state)
        write_state(session_path, state)
        append_event(
            event_path(session_path),
            {
                "ts": utc_now(),
                "type": "auto_reset_prepared",
                "reason": reason,
            },
        )
        if not quiet:
            print(f"Auto reset prepared for {state['session_id']}: {reason}")
        return 0

    compaction_reason = _determine_compaction_reason(state, events)
    if not compaction_reason:
        if not quiet:
            print("No reset required.")
        return 0

    state["last_compaction_reason"] = compaction_reason
    state["last_compaction_at"] = utc_now()
    state["last_compaction_artifact"] = "compact-state.md"
    state["last_compaction_actor"] = ""
    state["last_compaction_model"] = ""
    state["compaction_count"] = int(state.get("compaction_count", 0) or 0) + 1
    state["compaction_cycle_failures"] = 0
    state["context_strategy"] = "compact"
    next_actor, next_action = recommend_next_actor(state)
    state["compact_source_artifacts"] = collect_compact_source_artifacts(session_path, state)
    compact_state = build_compact_state_markdown(
        state,
        session_path,
        compaction_reason,
        next_actor=next_actor,
        next_action=next_action,
        source_artifacts=state["compact_source_artifacts"],
    )
    write_text(session_path / "compact-state.md", compact_state)
    validate_session_bundle(session_path, state)
    write_state(session_path, state)
    append_event(
        event_path(session_path),
        {
            "ts": utc_now(),
            "type": "compaction_prepared",
            "reason": compaction_reason,
            "count": state["compaction_count"],
            "next_actor": next_actor,
        },
    )
    if not quiet:
        print(f"Compaction prepared for {state['session_id']}: {compaction_reason}")
    return 0


def prepare_handoff(session_ref: str | None, reason: str) -> int:
    session_path, state = load_state(session_ref)
    handoff = build_handoff_markdown(state, session_path, reason)
    write_text(session_path / "handoff.md", handoff)
    append_event(
        event_path(session_path),
        {
            "ts": utc_now(),
            "type": "handoff_prepared",
            "reason": reason,
        },
    )
    validate_session_bundle(session_path, state)
    print(f"Handoff prepared for {state['session_id']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Harness Design Kit runtime helper")
    parser.add_argument("--session", help="Session id or path. Defaults to current session.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("status")
    subparsers.add_parser("advance")
    subparsers.add_parser("check-reset")
    handoff_parser = subparsers.add_parser("prepare-handoff")
    handoff_parser.add_argument("reason", nargs="?", default="manual handoff requested")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "status":
            return status(args.session)
        if args.command == "advance":
            return advance(args.session)
        if args.command == "check-reset":
            return check_reset(args.session)
        if args.command == "prepare-handoff":
            return prepare_handoff(args.session, args.reason)
    except (FileNotFoundError, ValidationError) as exc:
        print(str(exc))
        return 1
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
