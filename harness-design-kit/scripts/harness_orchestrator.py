#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path

import harness_run
import harness_runner
import harness_state
from harness_lib import (
    ValidationError,
    append_event,
    load_state,
    non_heading_excerpt,
    normalize_label,
    parse_label_value_lines,
    parse_markdown_list_items,
    plugin_root,
    read_events,
    session_artifact_dir,
    split_markdown_sections,
    utc_now,
    validate_compact_state_artifact,
    write_state,
    write_text,
)


def _event_path(session_path: Path) -> Path:
    return session_path / "events.jsonl"


def _agent_prompt_path(actor: str) -> Path:
    path = plugin_root() / "agents" / f"{actor}.md"
    if not path.exists():
        raise ValidationError(f"unknown actor prompt: {actor}")
    return path


def _agent_instruction(actor: str) -> str:
    return _agent_prompt_path(actor).read_text(encoding="utf-8").strip()


def _contract_review_instructions() -> str:
    return """Return markdown only in this shape:

# Contract Review

## Contract Decision
- Decision: approve|reject

## Findings
- Concrete reason 1
- Concrete reason 2
"""


def _compactor_instructions() -> str:
    return "Write the compact-state.md artifact only."


def _planned_actor_and_action(state: dict[str, object]) -> tuple[str, str]:
    return harness_run.recommend_next_actor(state)


def _resolved_actor_and_action(state: dict[str, object]) -> tuple[str, str]:
    planned_actor, planned_action = _planned_actor_and_action(state)
    if state.get("context_strategy") == "compact" and not state.get("last_compaction_actor"):
        return "compactor", f"Compact the session before rerunning {planned_actor}. {planned_action}"
    if state.get("context_strategy") == "compact":
        return planned_actor, (
            f"Use compact-state.md as the only context source, then continue. {planned_action}"
        )
    return planned_actor, planned_action


def _output_target(state: dict[str, object], actor: str) -> tuple[str, str]:
    phase = str(state.get("phase", ""))
    contract_status = str(state.get("contract_status", ""))
    if actor == "compactor":
        return "compact-state.md", _compactor_instructions()
    if actor == "planner":
        return "product-spec.md", "Write the full product spec markdown artifact only."
    if phase == "contract" and contract_status in {"draft", "rejected"}:
        return "sprint-contract.md", "Write the sprint contract markdown artifact only."
    if phase == "contract" and contract_status == "proposed":
        return "contract-review.md", _contract_review_instructions()
    if phase == "build":
        return "progress.md", "Write the progress markdown artifact only."
    if phase == "evaluate":
        return "evaluation.md", "Write the evaluation markdown artifact only."
    raise ValidationError(f"no output target is defined for actor={actor!r} in phase={phase!r}")


def _latest_contract_review_path(session_path: Path) -> Path | None:
    review_dir = session_artifact_dir(session_path) / "contract-reviews"
    if not review_dir.exists():
        return None
    reviews = sorted(path for path in review_dir.glob("review-*.md") if path.is_file())
    return reviews[-1] if reviews else None


def _latest_contract_review_excerpt(session_path: Path, max_lines: int = 10) -> str:
    path = _latest_contract_review_path(session_path)
    if path is None:
        return "_No contract review recorded yet._"
    return non_heading_excerpt(path, max_lines=max_lines)


def _latest_evaluation_excerpt(session_path: Path, max_lines: int = 10) -> str:
    return non_heading_excerpt(session_path / "evaluation.md", max_lines=max_lines)


def _candidate_snapshot(state: dict[str, object]) -> str:
    candidates = state.get("candidates", [])
    if not isinstance(candidates, list) or not candidates:
        return "_No candidate history recorded yet._"
    lines: list[str] = []
    for candidate in candidates[-4:]:
        if not isinstance(candidate, dict):
            continue
        lines.append(
            "- "
            f"{candidate.get('candidate_id', 'candidate')}: "
            f"status={candidate.get('status', 'unknown')}, "
            f"strategy={candidate.get('strategy', 'unknown')}, "
            f"verdict={candidate.get('last_verdict', '') or 'n/a'}, "
            f"recommendation={candidate.get('last_recommendation', '') or 'n/a'}"
        )
    return "\n".join(lines) if lines else "_No candidate history recorded yet._"


def _calibration_section(actor: str) -> str:
    mapping = {
        "qa-evaluator": ["qa-good.md", "qa-bad.md"],
        "design-evaluator": ["frontend-good.md", "frontend-bad.md"],
    }
    filenames = mapping.get(actor)
    if not filenames:
        return ""
    lines = ["## Calibration Anchors", ""]
    for filename in filenames:
        path = plugin_root() / "fixtures" / "calibration" / filename
        if not path.exists():
            continue
        lines.append(f"### {path.stem}")
        lines.append(path.read_text(encoding="utf-8").strip())
        lines.append("")
    return "\n".join(lines).strip()


def _contract_feedback_block(state: dict[str, object], session_path: Path) -> str:
    if state.get("phase") != "contract" or state.get("contract_status") not in {"draft", "rejected"}:
        return ""
    findings = state.get("last_contract_review_findings", [])
    if not isinstance(findings, list) or not findings:
        return ""
    latest_review = str(state.get("last_contract_review_artifact", "") or "") or "artifacts/contract-reviews/latest"
    lines = [
        "## Contract Revision Delta",
        f"- Previous decision: {state.get('last_contract_review_decision', '') or 'reject'}",
        f"- Review artifact: {latest_review}",
        "- Keep: retain the existing goal unless a finding explicitly changes scope.",
    ]
    lines.extend(f"- Change: {finding}" for finding in findings if str(finding).strip())
    lines.append("- Rule: revise the contract narrowly instead of rewriting unrelated sections.")
    return "\n".join(lines)


def _artifact_context(state: dict[str, object], session_path: Path, actor: str) -> str:
    product_spec = non_heading_excerpt(session_path / "product-spec.md", max_lines=12)
    design_brief = non_heading_excerpt(session_path / "design-brief.md", max_lines=12)
    sprint_contract = non_heading_excerpt(session_path / "sprint-contract.md", max_lines=12)
    progress = non_heading_excerpt(session_path / "progress.md", max_lines=12)
    evaluation = _latest_evaluation_excerpt(session_path, max_lines=12)
    compact_state = non_heading_excerpt(session_path / "compact-state.md", max_lines=18)
    contract_review = _latest_contract_review_excerpt(session_path, max_lines=12)
    candidate_snapshot = _candidate_snapshot(state)
    if actor == "compactor" or state.get("context_strategy") == "compact":
        source_artifacts = state.get("compact_source_artifacts", [])
        source_lines = (
            "\n".join(f"- {artifact}" for artifact in source_artifacts if isinstance(artifact, str))
            if isinstance(source_artifacts, list) and source_artifacts
            else "- compact-state.md"
        )
        return f"""## Compact Resume Contract

- compact-state.md is the only context source for this run
- preserve accepted facts only
- do not re-expand missing history from memory

## Compact State
{compact_state}

## Latest Contract Review
{contract_review}

## Latest Evaluation
{evaluation}

## Candidate Snapshot
{candidate_snapshot}

## Compact Source Artifacts
{source_lines}
"""
    return f"""## Existing Artifacts

### Product Spec
{product_spec}

### Design Brief
{design_brief}

### Sprint Contract
{sprint_contract}

### Progress
{progress}

### Evaluation
{evaluation}

### Latest Contract Review
{contract_review}

### Candidate Snapshot
{candidate_snapshot}
"""


def build_actor_prompt(session_ref: str | None = None) -> tuple[str, str]:
    session_path, state = load_state(session_ref)
    actor, action = _resolved_actor_and_action(state)
    target_name, target_instructions = _output_target(state, actor)
    calibration = _calibration_section(actor)
    calibration_block = f"\n{calibration}\n" if calibration else ""
    contract_feedback = _contract_feedback_block(state, session_path)
    contract_feedback_block = f"\n{contract_feedback}\n" if contract_feedback else ""
    prompt = f"""# Harness Actor Task

## Actor
- Name: {actor}
- Session: {state.get("session_id", "")}

## Current State
- Goal: {state.get("goal", "")}
- Mode: {state.get("mode", "")}
- Architecture profile: {state.get("architecture_profile", "")}
- Execution mode: {state.get("execution_mode", "")}
- Context strategy: {state.get("context_strategy", "")}
- Evaluator mode: {state.get("evaluator_mode", "")}
- Phase: {state.get("phase", "")}
- Contract status: {state.get("contract_status", "")}
- Round: {state.get("current_round", 0)}
- Current candidate: {state.get("current_candidate_id", "") or 'none'}
- Best candidate: {state.get("best_candidate_id", "") or 'none'}

## Recommended Action
- {action}

{_artifact_context(state, session_path, actor)}{contract_feedback_block}
## Role Instructions
{_agent_instruction(actor)}
{calibration_block}
## Output Target
- File: {target_name}
- Rule: {target_instructions}
"""
    return actor, prompt


def _parse_contract_decision(markdown: str) -> str:
    sections = split_markdown_sections(markdown)
    decision_items = parse_label_value_lines(sections.get("Contract Decision", ""))
    for label, value in decision_items:
        if normalize_label(label) == "decision":
            normalized = normalize_label(value)
            if normalized in {"approve", "approved"}:
                return "approve"
            if normalized in {"reject", "rejected"}:
                return "reject"
    raise ValidationError("contract review output must include Decision: approve|reject")


def _parse_contract_findings(markdown: str) -> list[str]:
    sections = split_markdown_sections(markdown)
    return parse_markdown_list_items(sections.get("Findings", ""))


def _parse_verdict(markdown: str) -> str:
    sections = split_markdown_sections(markdown)
    verdict_items = parse_label_value_lines(sections.get("Verdict", ""))
    for label, value in verdict_items:
        if normalize_label(label) == "verdict":
            normalized = normalize_label(value)
            if normalized in {"pass", "fail", "revise", "pivot"}:
                return normalized
    raise ValidationError("evaluation output must include Verdict: pass|fail|revise|pivot")


def _record_contract_review(session_path: Path, markdown: str) -> Path:
    artifact_dir = session_artifact_dir(session_path) / "contract-reviews"
    base_name = f"review-{utc_now().replace(':', '-')}"
    path = artifact_dir / f"{base_name}.md"
    suffix = 2
    while path.exists():
        path = artifact_dir / f"{base_name}-{suffix}.md"
        suffix += 1
    write_text(path, markdown)
    return path


def _latest_event_index(events: list[dict[str, object]], event_type: str, *, to_phase: str | None = None) -> int:
    for index in range(len(events) - 1, -1, -1):
        event = events[index]
        if event.get("type") != event_type:
            continue
        if to_phase is not None and event.get("to_phase") != to_phase:
            continue
        return index
    return -1


def _should_start_frontend_round(session_path: Path, state: dict[str, object]) -> bool:
    if state.get("mode") != "frontend" or state.get("phase") != "build":
        return False
    events = read_events(_event_path(session_path))
    if int(state.get("current_round", 0) or 0) <= 0:
        return True
    last_build_index = _latest_event_index(events, "phase_advanced", to_phase="build")
    last_round_index = _latest_event_index(events, "round_started")
    return last_round_index < last_build_index


def _prepare_session_for_run(session_ref: str | None) -> tuple[Path, dict[str, object]]:
    session_path, state = load_state(session_ref)
    if _should_start_frontend_round(session_path, state):
        harness_state.start_round(session_ref, None)
        session_path, state = load_state(session_ref)
    return session_path, state


def _mark_compaction_resumed(session_ref: str | None) -> None:
    session_path, state = load_state(session_ref)
    state["compaction_resume_count"] = int(state.get("compaction_resume_count", 0) or 0) + 1
    write_state(session_path, state)
    append_event(
        _event_path(session_path),
        {
            "ts": utc_now(),
            "type": "compaction_resumed",
            "count": state["compaction_resume_count"],
        },
    )


def _clear_compaction_context(session_ref: str | None) -> None:
    session_path, state = load_state(session_ref)
    if state.get("context_strategy") != "compact":
        return
    state["context_strategy"] = "full"
    state["compaction_cycle_failures"] = 0
    write_state(session_path, state)
    append_event(
        _event_path(session_path),
        {
            "ts": utc_now(),
            "type": "compaction_cycle_completed",
            "count": state.get("compaction_resume_count", 0),
        },
    )


def _runner_model_hint(actor: str, provider: str) -> str:
    if provider == "external":
        return "external-command"
    if provider in {"openai", "anthropic"}:
        return harness_runner.configured_model(actor, provider)
    return ""


def _run_actor_with_retry(
    session_ref: str | None,
    session_path: Path,
    actor: str,
    prompt: str,
) -> harness_runner.RunResult | None:
    for attempt in (1, 2):
        provider = harness_runner.configured_provider()
        model = _runner_model_hint(actor, provider)
        try:
            _, state = load_state(session_ref)
            result = harness_runner.run_actor(actor, prompt, state, session_path)
        except Exception as exc:
            session_path, state = load_state(session_ref)
            state["last_runner_provider"] = provider if provider != "unconfigured" else ""
            state["last_runner_model"] = model
            state["consecutive_runner_failures"] = int(state.get("consecutive_runner_failures", 0) or 0) + 1
            write_state(session_path, state)
            append_event(
                _event_path(session_path),
                {
                    "ts": utc_now(),
                    "type": "runner_failed",
                    "actor": actor,
                    "attempt": attempt,
                    "provider": provider,
                    "model": model,
                    "error": str(exc),
                },
            )
            if attempt == 2:
                if state.get("context_strategy") == "compact":
                    state["compaction_cycle_failures"] = int(state.get("compaction_cycle_failures", 0) or 0) + 1
                    write_state(session_path, state)
                    append_event(
                        _event_path(session_path),
                        {
                            "ts": utc_now(),
                            "type": "compaction_cycle_failed",
                            "actor": actor,
                            "phase": state.get("phase", ""),
                            "failures": state["compaction_cycle_failures"],
                        },
                    )
                    if int(state["compaction_cycle_failures"]) >= 2:
                        harness_state.prepare_reset(
                            session_ref,
                            f"compact resume failed twice in phase={state.get('phase', '')}",
                        )
                return None
            continue

        session_path, state = load_state(session_ref)
        state["last_runner_provider"] = result.provider
        state["last_runner_model"] = result.model
        state["consecutive_runner_failures"] = 0
        if actor == "compactor":
            state["last_compaction_actor"] = actor
            state["last_compaction_model"] = result.model
        write_state(session_path, state)
        return result
    return None


def _write_compact_state(session_ref: str | None, session_path: Path, markdown: str, result: harness_runner.RunResult) -> None:
    write_text(session_path / "compact-state.md", markdown)
    _, state = load_state(session_ref)
    validate_compact_state_artifact(markdown, state)
    append_event(
        _event_path(session_path),
        {
            "ts": utc_now(),
            "type": "compactor_ran",
            "actor": "compactor",
            "provider": result.provider,
            "model": result.model,
            "sources": state.get("compact_source_artifacts", []),
        },
    )


def run_once(session_ref: str | None = None) -> int:
    session_path, state = _prepare_session_for_run(session_ref)

    if state.get("context_strategy") == "compact" and not state.get("last_compaction_actor"):
        actor, prompt = build_actor_prompt(session_ref)
        compactor_result = _run_actor_with_retry(session_ref, session_path, actor, prompt)
        if compactor_result is None:
            return 0
        _write_compact_state(session_ref, session_path, compactor_result.output, compactor_result)
        _mark_compaction_resumed(session_ref)
        session_path, state = load_state(session_ref)

    actor, prompt = build_actor_prompt(session_ref)
    result = _run_actor_with_retry(session_ref, session_path, actor, prompt)
    if result is None:
        return 0

    target_name, _ = _output_target(state, actor)
    if target_name == "product-spec.md":
        write_text(session_path / target_name, result.output)
        append_event(
            _event_path(session_path),
            {
                "ts": utc_now(),
                "type": "planner_ran",
                "actor": actor,
                "provider": result.provider,
                "model": result.model,
            },
        )
        _clear_compaction_context(session_ref)
        return harness_run.advance(session_ref)

    if target_name == "sprint-contract.md":
        write_text(session_path / target_name, result.output)
        append_event(
            _event_path(session_path),
            {
                "ts": utc_now(),
                "type": "contract_drafted",
                "actor": actor,
                "provider": result.provider,
                "model": result.model,
            },
        )
        _clear_compaction_context(session_ref)
        return harness_state.propose_contract(session_ref, actor)

    if target_name == "contract-review.md":
        review_path = _record_contract_review(session_path, result.output)
        decision = _parse_contract_decision(result.output)
        findings = _parse_contract_findings(result.output)
        relative_review_path = str(review_path.relative_to(session_path))
        harness_state.record_contract_review(session_ref, relative_review_path, decision, findings)
        append_event(
            _event_path(session_path),
            {
                "ts": utc_now(),
                "type": "contract_review_recorded",
                "actor": actor,
                "artifact": relative_review_path,
                "decision": decision,
                "provider": result.provider,
                "model": result.model,
            },
        )
        _clear_compaction_context(session_ref)
        if decision == "approve":
            harness_state.approve_contract(session_ref, actor)
            return harness_run.advance(session_ref)
        return harness_state.reject_contract(session_ref, f"{actor} rejected the current contract")

    if target_name == "progress.md":
        write_text(session_path / target_name, result.output)
        append_event(
            _event_path(session_path),
            {
                "ts": utc_now(),
                "type": "build_progress_recorded",
                "actor": actor,
                "provider": result.provider,
                "model": result.model,
            },
        )
        _clear_compaction_context(session_ref)
        return harness_run.advance(session_ref)

    if target_name == "evaluation.md":
        write_text(session_path / target_name, result.output)
        verdict = _parse_verdict(result.output)
        harness_state.record_evaluation(session_ref, verdict, actor)
        append_event(
            _event_path(session_path),
            {
                "ts": utc_now(),
                "type": "evaluation_artifact_recorded",
                "actor": actor,
                "provider": result.provider,
                "model": result.model,
                "verdict": verdict,
            },
        )
        _clear_compaction_context(session_ref)
        return harness_run.advance(session_ref)

    raise ValidationError(f"unsupported target: {target_name}")


def run_loop(session_ref: str | None, max_steps: int) -> int:
    for _ in range(max_steps):
        _, state = load_state(session_ref)
        if state.get("phase") in {"handoff", "completed"}:
            break
        run_once(session_ref)
        _, state = load_state(session_ref)
        if state.get("phase") not in {"handoff", "completed"} and state.get("execution_mode") in {"auto", "continuous"}:
            harness_run.check_reset(session_ref, quiet=True)
    _, state = load_state(session_ref)
    print(
        f"{state['session_id']} | phase={state.get('phase')} | "
        f"contract={state.get('contract_status')} | status={state.get('status')}"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Harness Design Kit orchestrator")
    parser.add_argument("--session", help="Session id or path. Defaults to current session.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("next-prompt")
    subparsers.add_parser("run-once")
    loop_parser = subparsers.add_parser("run-loop")
    loop_parser.add_argument("--max-steps", type=int, default=8)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "next-prompt":
            _, prompt = build_actor_prompt(args.session)
            print(prompt)
            return 0
        if args.command == "run-once":
            return run_once(args.session)
        if args.command == "run-loop":
            return run_loop(args.session, args.max_steps)
    except (ValidationError, FileNotFoundError, ValueError) as exc:
        print(f"Error: {exc}")
        return 1
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
