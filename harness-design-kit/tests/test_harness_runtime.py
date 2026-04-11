from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PLUGIN_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import harness_lib  # noqa: E402
import harness_orchestrator  # noqa: E402
import harness_runner  # noqa: E402
import harness_run  # noqa: E402
import harness_state  # noqa: E402
import live_eval  # noqa: E402


def current_session_path(root: Path) -> Path:
    pointer = json.loads((root / ".harness-design-kit" / "current.json").read_text(encoding="utf-8"))
    return root / pointer["session_path"]


def write_contract(session_path: Path, unit_type: str = "sprint") -> None:
    (session_path / "sprint-contract.md").write_text(
        f"""# Sprint Contract

## Objective
- Deliver a testable analytics dashboard slice.

## Deliverables
- Dashboard shell with seeded project data.

## Out Of Scope
- Billing and team invites.

## Acceptance Tests
- Dashboard renders seeded project cards.

## Verification Steps
- Run `npm test`.

## Evidence Requirements
- Capture the dashboard screenshot and test logs.

## Exit Criteria
- Dashboard loads without blocking errors.

## Contract Status
- Status: draft
- Unit type: {unit_type}
""",
        encoding="utf-8",
    )


def write_app_evaluation(
    session_path: Path,
    *,
    verdict: str,
    artifact_ref: str,
    functionality_score: int = 8,
) -> None:
    (session_path / "evaluation.md").write_text(
        f"""# Evaluation

## Verdict
- Evaluator: qa-evaluator
- Verdict: {verdict}
- Round: 1

## Score Breakdown
- Criterion: product depth
- Score: 8
- Threshold: 7
- Weight: 1.0
- Criterion: functionality
- Score: {functionality_score}
- Threshold: 7
- Weight: 1.5
- Criterion: visual design
- Score: 8
- Threshold: 7
- Weight: 1.0
- Criterion: code quality
- Score: 8
- Threshold: 7
- Weight: 1.0

## Findings
- The dashboard behavior matches the agreed scope.

## Evidence
- Ran the smoke checks and reviewed the captured artifacts.

## Reproduction Steps
- Open the dashboard and load the seeded workspace.

## Artifact References
- {artifact_ref}

## Recommendation
- {"accept the scope" if verdict == "pass" else "refine the failing functionality before retrying"}
""",
        encoding="utf-8",
    )


def write_frontend_evaluation(
    session_path: Path,
    *,
    verdict: str,
    artifact_ref: str,
    design_weight: float = 2.0,
    originality_weight: float = 2.0,
    craft_weight: float = 1.0,
    functionality_weight: float = 1.0,
    design_score: int = 8,
    originality_score: int = 8,
    craft_score: int = 8,
    functionality_score: int = 8,
) -> None:
    (session_path / "evaluation.md").write_text(
        f"""# Evaluation

## Verdict
- Evaluator: design-evaluator
- Verdict: {verdict}
- Round: 1

## Score Breakdown
- Criterion: design quality
- Score: {design_score}
- Threshold: 7
- Weight: {design_weight}
- Criterion: originality
- Score: {originality_score}
- Threshold: 7
- Weight: {originality_weight}
- Criterion: craft
- Score: {craft_score}
- Threshold: 7
- Weight: {craft_weight}
- Criterion: functionality
- Score: {functionality_score}
- Threshold: 7
- Weight: {functionality_weight}

## Findings
- The design direction is consistent with the brief.

## Evidence
- Reviewed the rendered candidate and supporting notes.

## Reproduction Steps
- Open the candidate page and compare the sections against the brief.

## Artifact References
- {artifact_ref}

## Recommendation
- {"accept the candidate" if verdict == "pass" else "refine the weak candidate direction"}
""",
        encoding="utf-8",
    )


def extract_prompt_from_payload(payload: dict[str, object]) -> str:
    if "input" in payload:
        messages = payload["input"]
        if isinstance(messages, list) and messages:
            content = messages[-1].get("content", [])
            if isinstance(content, list) and content:
                return str(content[0].get("text", ""))
    messages = payload.get("messages", [])
    if isinstance(messages, list) and messages:
        content = messages[-1].get("content", "")
        if isinstance(content, str):
            return content
    raise AssertionError(f"unsupported payload shape: {payload}")


def extract_actor_from_prompt(prompt: str) -> str:
    for raw_line in prompt.splitlines():
        line = raw_line.strip()
        if line.startswith("- Name: "):
            return line.split(":", 1)[1].strip()
    raise AssertionError(f"could not infer actor from prompt:\n{prompt}")


def extract_phase_from_prompt(prompt: str) -> str:
    for raw_line in prompt.splitlines():
        line = raw_line.strip()
        if line.startswith("- Phase: "):
            return line.split(":", 1)[1].strip()
    raise AssertionError(f"could not infer phase from prompt:\n{prompt}")


def extract_round_from_prompt(prompt: str) -> int:
    for raw_line in prompt.splitlines():
        line = raw_line.strip()
        if line.startswith("- Round: "):
            return int(line.split(":", 1)[1].strip())
    return 0


def native_response_payload(provider: str, markdown: str) -> dict[str, object]:
    if provider == "anthropic":
        return {"content": [{"type": "text", "text": markdown}]}
    return {"output": [{"content": [{"type": "output_text", "text": markdown}]}]}


def sample_compact_state(goal: str, *, next_step: str, reason: str) -> str:
    return f"""# Compact State

## Current Goal
- Goal: {goal}

## Session Snapshot
- Mode: app
- Architecture profile: continuous
- Execution mode: auto
- Evaluator mode: always
- Current phase: clarify
- Current round: 0
- Compaction reason: {reason}

## Accepted Facts
- Goal: {goal}
- Session configuration: mode=app, architecture=continuous, phase=clarify, contract=draft

## Active Contract
- No approved contract yet.

## Current Progress
- No build progress recorded yet.

## Latest Failing Evidence
- No failing evidence currently recorded.

## Open Questions
- No unresolved questions currently recorded.

## Immediate Next Step
- {next_step}

## Resume Prompt
- Treat this compact state as the only context source. Resume with planner and execute: {next_step}

## Source Artifacts
- product-spec.md
"""


class HarnessRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmpdir.name)
        self.env = mock.patch.dict(
            os.environ,
            {"HARNESS_DESIGN_KIT_STATE_ROOT": str(self.root)},
            clear=False,
        )
        self.env.start()

    def tearDown(self) -> None:
        self.env.stop()
        self.tmpdir.cleanup()

    def init_session(self, label: str, mode: str = "app", architecture_profile: str | None = None) -> Path:
        harness_state.init_session(label, mode, architecture_profile)
        return current_session_path(self.root)

    def create_fake_runner(self) -> Path:
        runner_path = self.root / "fake_runner.py"
        runner_path.write_text(
            """#!/usr/bin/env python3
import os
import sys

actor = os.environ.get("HARNESS_ACTOR", "")
phase = os.environ.get("HARNESS_PHASE", "")
_prompt = sys.stdin.read()

if actor == "planner":
    print(\"\"\"# Product Spec

## Problem And Target User
- Goal: Build a durable workflow harness.
- Target user: plugin authors shipping long-running app workflows.

## Product Goals
- Automate the next actor selection.
- Keep state transitions explicit.

## Non-Goals
- Do not assume a hosted runner service.

## Design Direction
- Prefer structured markdown artifacts over chat-only state.

## AI Opportunities
- Use an external runner only through a configurable command.

## Sprint Candidates
- Candidate 1: orchestration loop.
- Candidate 2: compaction and QA hardening.

## Verification Risks
- Risk 1: invalid contract artifacts.
- Risk 2: browser runtime drift.
\"\"\")
elif actor == "generator" and phase == "contract":
    print(\"\"\"# Sprint Contract

## Objective
- Deliver one fully automated orchestration pass.

## Deliverables
- Add a runner-driven orchestration script.

## Out Of Scope
- Hosted execution services.

## Acceptance Tests
- A continuous app session can reach completed.

## Verification Steps
- Run the harness runtime unit tests.

## Evidence Requirements
- Capture the test command output.

## Exit Criteria
- The session advances through plan, contract, build, and evaluate.

## Contract Status
- Status: draft
- Unit type: sprint
\"\"\")
elif actor == "qa-evaluator" and phase == "contract":
    print(\"\"\"# Contract Review

## Contract Decision
- Decision: approve

## Findings
- The contract is specific and testable.
\"\"\")
elif actor == "generator" and phase == "build":
    print(\"\"\"# Progress

## Implemented Scope
- Added the orchestration loop script.

## Verification Run
- Command 1: python3 -m unittest -q tests/test_harness_runtime.py
- Result 1: expected green run in CI and local temp workspace.

## Generator Self-Check
- The implemented scope matches the active contract.

## Known Risks
- Browser automation still depends on the cached Playwright runtime.

## Next Suggested Step
- Run the evaluator and capture the final verdict.
\"\"\")
elif actor == "qa-evaluator" and phase == "evaluate":
    print(\"\"\"# Evaluation

## Verdict
- Evaluator: qa-evaluator
- Verdict: pass
- Round: 1

## Score Breakdown
- Criterion: product depth
- Score: 8
- Threshold: 7
- Weight: 1.0
- Criterion: functionality
- Score: 8
- Threshold: 7
- Weight: 1.5
- Criterion: visual design
- Score: 7
- Threshold: 7
- Weight: 1.0
- Criterion: code quality
- Score: 8
- Threshold: 7
- Weight: 1.0

## Findings
- The automated harness loop completed the planned slice.

## Evidence
- Reviewed the generated artifacts and state transitions.

## Reproduction Steps
- Initialize a continuous app session and run the orchestrator loop.

## Artifact References
- progress.md

## Recommendation
- accept the scope
\"\"\")
else:
    raise SystemExit(f"unsupported actor={actor} phase={phase}")
""",
            encoding="utf-8",
        )
        runner_path.chmod(0o755)
        return runner_path

    def create_contract_feedback_runner(self) -> Path:
        runner_path = self.root / "feedback_runner.py"
        runner_path.write_text(
            """#!/usr/bin/env python3
import os
import sys

actor = os.environ.get("HARNESS_ACTOR", "")
phase = os.environ.get("HARNESS_PHASE", "")
prompt = sys.stdin.read()

if actor == "planner":
    print(\"\"\"# Product Spec

## Problem And Target User
- Goal: Tighten the active scope into one verifiable slice.
- Target user: plugin authors maintaining long-running harnesses.

## Product Goals
- Keep the next loop narrow and testable.
- Use artifact-driven verification.

## Non-Goals
- Hosted orchestration.

## Design Direction
- Prefer durable local artifacts over chat-only context.

## AI Opportunities
- Let contract reviews feed the next generator prompt.

## Sprint Candidates
- Candidate 1: contract feedback loop.
- Candidate 2: compact-resume path.

## Verification Risks
- Risk 1: contract scope stays vague.
- Risk 2: review findings do not feed the next draft.
\"\"\")
elif actor == "generator" and phase == "contract":
    if "Tighten the scope to one verifiable slice." in prompt:
        objective = "Deliver one verifiable slice for the active harness goal."
    else:
        objective = "Improve the harness."
    print(f\"\"\"# Sprint Contract

## Objective
- {objective}

## Deliverables
- Update the orchestrator to carry review feedback into the next draft.

## Out Of Scope
- Hosted services.

## Acceptance Tests
- A rejected contract can be revised and approved in the next loop.

## Verification Steps
- Run python3 -m unittest -q tests/test_harness_runtime.py

## Evidence Requirements
- Capture the review artifact and the revised contract.

## Exit Criteria
- The contract is narrow enough for one iteration.

## Contract Status
- Status: draft
- Unit type: sprint
\"\"\")
elif actor == "qa-evaluator" and phase == "contract":
    if "Deliver one verifiable slice for the active harness goal." in prompt:
        print(\"\"\"# Contract Review

## Contract Decision
- Decision: approve

## Findings
- The contract is now narrow, testable, and evidence-driven.
\"\"\")
    else:
        print(\"\"\"# Contract Review

## Contract Decision
- Decision: reject

## Findings
- Tighten the scope to one verifiable slice.
\"\"\")
elif actor == "generator" and phase == "build":
    print(\"\"\"# Progress

## Implemented Scope
- Added the review-feedback loop.

## Verification Run
- Command 1: python3 -m unittest -q tests/test_harness_runtime.py
- Result 1: expected green run.

## Generator Self-Check
- The revised contract was implemented without scope creep.

## Known Risks
- Browser verification still depends on local runtime availability.

## Next Suggested Step
- Run the evaluator.
\"\"\")
elif actor == "qa-evaluator" and phase == "evaluate":
    print(\"\"\"# Evaluation

## Verdict
- Evaluator: qa-evaluator
- Verdict: pass
- Round: 1

## Score Breakdown
- Criterion: product depth
- Score: 8
- Threshold: 7
- Weight: 1.0
- Criterion: functionality
- Score: 8
- Threshold: 7
- Weight: 1.5
- Criterion: visual design
- Score: 7
- Threshold: 7
- Weight: 1.0
- Criterion: code quality
- Score: 8
- Threshold: 7
- Weight: 1.0

## Findings
- The feedback loop works end to end.

## Evidence
- Reviewed the revised contract and build progress.

## Reproduction Steps
- Run the orchestrator loop from an empty session.

## Artifact References
- progress.md

## Recommendation
- accept the scope
\"\"\")
elif actor == "compactor":
    print(\"\"\"# Compact State

## Current Goal
- Goal: Tighten the active scope into one verifiable slice.

## Session Snapshot
- Mode: app
- Architecture profile: continuous
- Execution mode: auto
- Evaluator mode: always
- Current phase: contract
- Current round: 0
- Compaction reason: contract rejection triggered compaction

## Accepted Facts
- Goal: Tighten the active scope into one verifiable slice.
- Session configuration: mode=app, architecture=continuous, phase=contract, contract=rejected

## Active Contract
- The contract needs one verifiable slice.

## Current Progress
- No build progress recorded yet.

## Latest Failing Evidence
- Tighten the scope to one verifiable slice.

## Open Questions
- No unresolved questions currently recorded.

## Immediate Next Step
- Revise the contract narrowly using the latest review findings.

## Resume Prompt
- Treat this compact state as the only context source. Resume with generator and execute: Revise the contract narrowly using the latest review findings.

## Source Artifacts
- sprint-contract.md
- artifacts/contract-reviews/latest.md
\"\"\")
else:
    raise SystemExit(f"unsupported actor={actor} phase={phase}")
""",
            encoding="utf-8",
        )
        runner_path.chmod(0o755)
        return runner_path

    def native_runner_side_effect(self, provider: str, responder):
        def side_effect(url: str, headers: dict[str, str], payload: dict[str, object]) -> dict[str, object]:
            prompt = extract_prompt_from_payload(payload)
            actor = extract_actor_from_prompt(prompt)
            markdown = responder(actor, prompt)
            return native_response_payload(provider, markdown)

        return side_effect

    def advance_app_session_to_evaluate(self, session_path: Path) -> None:
        harness_run.advance(None)
        harness_run.advance(None)
        write_contract(session_path)
        harness_state.propose_contract(None, "generator")
        harness_state.approve_contract(None, "qa-evaluator")
        harness_run.advance(None)
        harness_run.advance(None)

    def test_app_continuous_advances_to_contract(self) -> None:
        self.init_session("Continuous App", "app", "continuous")
        harness_run.advance(None)
        harness_run.advance(None)
        _, state = harness_lib.load_state(None)
        self.assertEqual(state["phase"], "contract")
        self.assertEqual(state["contract_status"], "draft")

    def test_propose_and_approve_contract_require_valid_artifact(self) -> None:
        session_path = self.init_session("Contract Flow")
        harness_run.advance(None)
        harness_run.advance(None)
        write_contract(session_path)
        harness_state.propose_contract(None, "generator")
        harness_state.approve_contract(None, "qa-evaluator")
        _, state = harness_lib.load_state(None)
        self.assertEqual(state["contract_status"], "approved")

    def test_record_evaluation_rejects_placeholder_template(self) -> None:
        session_path = self.init_session("Placeholder Eval")
        self.advance_app_session_to_evaluate(session_path)
        with self.assertRaises(harness_lib.ValidationError):
            harness_state.record_evaluation(None, "pass", "qa-evaluator")

    def test_record_evaluation_persists_structured_scores(self) -> None:
        session_path = self.init_session("Structured Eval")
        self.advance_app_session_to_evaluate(session_path)
        artifact_path = session_path / "artifacts" / "proof.txt"
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text("proof\n", encoding="utf-8")
        write_app_evaluation(session_path, verdict="pass", artifact_ref="artifacts/proof.txt")

        harness_state.record_evaluation(None, "pass", "qa-evaluator")

        _, state = harness_lib.load_state(None)
        self.assertEqual(state["last_evaluation_verdict"], "pass")
        self.assertEqual(len(state["last_evaluation_scores"]), 4)
        self.assertEqual(state["last_evaluation_threshold_misses"], [])
        self.assertEqual(state["last_evaluation_artifacts"], ["artifacts/proof.txt"])

    def test_record_evaluation_rejects_passing_threshold_miss(self) -> None:
        session_path = self.init_session("Threshold Miss")
        self.advance_app_session_to_evaluate(session_path)
        artifact_path = session_path / "artifacts" / "proof.txt"
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text("proof\n", encoding="utf-8")
        write_app_evaluation(
            session_path,
            verdict="fail",
            artifact_ref="artifacts/proof.txt",
            functionality_score=5,
        )

        with self.assertRaises(harness_lib.ValidationError):
            harness_state.record_evaluation(None, "pass", "qa-evaluator")

        harness_state.record_evaluation(None, "fail", "qa-evaluator")
        _, state = harness_lib.load_state(None)
        self.assertEqual(state["last_evaluation_threshold_misses"], ["functionality"])

    def test_record_evaluation_requires_live_eval_artifact_when_qa_url_exists(self) -> None:
        session_path = self.init_session("Live Eval Gate")
        self.advance_app_session_to_evaluate(session_path)
        harness_state.set_field(None, "qa_target_url", "https://example.com")
        artifact_path = session_path / "artifacts" / "proof.txt"
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text("proof\n", encoding="utf-8")
        write_app_evaluation(session_path, verdict="pass", artifact_ref="artifacts/proof.txt")

        with self.assertRaises(harness_lib.ValidationError):
            harness_state.record_evaluation(None, "pass", "qa-evaluator")

    def test_prepare_reset_writes_reset_mode_into_handoff(self) -> None:
        session_path = self.init_session("Reset Handoff")
        harness_state.prepare_reset(None, "repeated failures")
        handoff = (session_path / "handoff.md").read_text(encoding="utf-8")
        self.assertIn("- Execution mode: reset", handoff)

    def test_set_field_rejects_protected_runtime_fields(self) -> None:
        self.init_session("Protected Setter")
        with self.assertRaises(harness_lib.ValidationError):
            harness_state.set_field(None, "phase", "evaluate")
        harness_state.set_field(None, "qa_target_url", "https://example.com")
        _, state = harness_lib.load_state(None)
        self.assertEqual(state["qa_target_url"], "https://example.com")

    def test_live_eval_records_artifact_without_browser(self) -> None:
        self.init_session("Live Eval")
        fake_payload = {
            "ok": True,
            "status": 200,
            "url": "https://example.com",
            "headers": {"Content-Type": "text/html"},
            "body": "<html><title>Example</title><body>Hello</body></html>",
            "error": "",
        }
        with mock.patch.object(live_eval, "_fetch_url", return_value=fake_payload):
            live_eval.run_live_eval(None, "https://example.com", 5, "never", None)
        _, state = harness_lib.load_state(None)
        self.assertTrue(state["last_live_eval_artifact"].endswith(".md"))
        artifact_path = current_session_path(self.root) / state["last_live_eval_artifact"]
        self.assertTrue(artifact_path.exists())

    def test_frontend_evaluation_requires_priority_weights(self) -> None:
        session_path = self.init_session("Frontend Weights", "frontend")
        harness_run.advance(None)
        harness_run.advance(None)
        harness_run.advance(None)
        artifact_path = session_path / "artifacts" / "candidate.txt"
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text("candidate\n", encoding="utf-8")
        write_frontend_evaluation(
            session_path,
            verdict="pass",
            artifact_ref="artifacts/candidate.txt",
            design_weight=1.0,
            originality_weight=1.0,
            craft_weight=2.0,
            functionality_weight=2.0,
        )

        with self.assertRaises(harness_lib.ValidationError):
            harness_state.record_evaluation(None, "pass", "design-evaluator")

    def test_frontend_evaluation_rejects_non_positive_weight(self) -> None:
        session_path = self.init_session("Frontend Bad Weight", "frontend")
        harness_run.advance(None)
        harness_run.advance(None)
        harness_run.advance(None)
        artifact_path = session_path / "artifacts" / "candidate.txt"
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text("candidate\n", encoding="utf-8")
        write_frontend_evaluation(
            session_path,
            verdict="pass",
            artifact_ref="artifacts/candidate.txt",
            craft_weight=0.0,
        )

        with self.assertRaises(harness_lib.ValidationError):
            harness_state.record_evaluation(None, "pass", "design-evaluator")

    def test_frontend_evaluation_persists_weighted_summary(self) -> None:
        session_path = self.init_session("Frontend Summary", "frontend")
        harness_run.advance(None)
        harness_run.advance(None)
        harness_run.advance(None)
        artifact_path = session_path / "artifacts" / "candidate.txt"
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text("candidate\n", encoding="utf-8")
        write_frontend_evaluation(
            session_path,
            verdict="pass",
            artifact_ref="artifacts/candidate.txt",
        )

        harness_state.record_evaluation(None, "pass", "design-evaluator")

        _, state = harness_lib.load_state(None)
        self.assertAlmostEqual(state["last_evaluation_weighted_average"], 8.0)
        self.assertAlmostEqual(state["last_evaluation_weighted_threshold"], 7.0)
        self.assertEqual(
            state["last_evaluation_priority_criteria"],
            ["design quality", "originality"],
        )

    def test_frontend_accept_recommendation_marks_best_candidate(self) -> None:
        session_path = self.init_session("Frontend Accept", "frontend")
        harness_run.advance(None)
        harness_run.advance(None)
        harness_run.advance(None)
        harness_state.start_round(None, "candidate-a")
        artifact_path = session_path / "artifacts" / "candidate.txt"
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text("candidate\n", encoding="utf-8")
        write_frontend_evaluation(
            session_path,
            verdict="pass",
            artifact_ref="artifacts/candidate.txt",
        )
        harness_state.record_evaluation(None, "pass", "design-evaluator")
        _, state = harness_lib.load_state(None)
        self.assertEqual(state["last_evaluation_recommendation"], "accept")
        self.assertEqual(state["active_strategy"], "accept")
        self.assertEqual(state["best_candidate_id"], "candidate-a")

    def test_record_evaluation_rejects_non_actionable_recommendation(self) -> None:
        session_path = self.init_session("Recommendation Format")
        self.advance_app_session_to_evaluate(session_path)
        artifact_path = session_path / "artifacts" / "proof.txt"
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text("proof\n", encoding="utf-8")
        (session_path / "evaluation.md").write_text(
            """# Evaluation

## Verdict
- Evaluator: qa-evaluator
- Verdict: pass
- Round: 1

## Score Breakdown
- Criterion: product depth
- Score: 8
- Threshold: 7
- Weight: 1.0
- Criterion: functionality
- Score: 8
- Threshold: 7
- Weight: 1.5
- Criterion: visual design
- Score: 8
- Threshold: 7
- Weight: 1.0
- Criterion: code quality
- Score: 8
- Threshold: 7
- Weight: 1.0

## Findings
- Looks good.

## Evidence
- Reviewed the build output.

## Reproduction Steps
- Open the app.

## Artifact References
- artifacts/proof.txt

## Recommendation
- keep going with confidence
""",
            encoding="utf-8",
        )

        with self.assertRaises(harness_lib.ValidationError):
            harness_state.record_evaluation(None, "pass", "qa-evaluator")

    def test_list_and_select_sessions(self) -> None:
        first = self.init_session("First Session")
        second = self.init_session("Second Session")
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            harness_state.list_sessions(10)
        output = buffer.getvalue()
        self.assertIn(first.name, output)
        self.assertIn(second.name, output)

        harness_state.select_session(first.name)
        self.assertEqual(current_session_path(self.root), first)

    def test_list_sessions_tolerates_invalid_state_json(self) -> None:
        valid = self.init_session("Valid Session")
        broken_session = harness_lib.state_root() / "sessions" / "broken-session"
        broken_session.mkdir(parents=True, exist_ok=True)
        (broken_session / "state.json").write_text("{invalid\n", encoding="utf-8")

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            harness_state.list_sessions(10)
        output = buffer.getvalue()

        self.assertIn(valid.name, output)
        self.assertIn("broken-session | status=invalid", output)

    def test_select_session_rejects_invalid_session_bundle(self) -> None:
        broken_session = harness_lib.state_root() / "sessions" / "broken-select"
        broken_session.mkdir(parents=True, exist_ok=True)
        (broken_session / "state.json").write_text(
            json.dumps({"session_id": "broken-select"}),
            encoding="utf-8",
        )

        with self.assertRaises(harness_lib.ValidationError):
            harness_state.select_session("broken-select")

    def test_resume_from_handoff_creates_child_session(self) -> None:
        parent_session_path = self.init_session("Resume Parent")
        artifact_path = parent_session_path / "artifacts" / "live-eval" / "eval-r0.md"
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text("proof\n", encoding="utf-8")
        (parent_session_path / "progress.md").write_text(
            """# Progress

## Implemented Scope
- Implemented the first slice.

## Verification Run
- Ran smoke checks.

## Generator Self-Check
- The current slice is ready for a fresh agent to resume.

## Known Risks
- Needs a fresh resume.

## Next Suggested Step
- Continue from handoff.
""",
            encoding="utf-8",
        )
        harness_state.prepare_reset(None, "fresh context needed")
        parent_state = harness_lib.load_state(None)[1]

        harness_state.resume_from_handoff(None, "manual resume")

        child_session_path = current_session_path(self.root)
        self.assertNotEqual(child_session_path, parent_session_path)
        _, persisted_parent_state = harness_lib.load_state(parent_session_path.name)
        _, child_state = harness_lib.load_state(None)
        self.assertEqual(persisted_parent_state["phase"], "handoff")
        self.assertEqual(persisted_parent_state["status"], "paused")
        self.assertEqual(persisted_parent_state["execution_mode"], "reset")
        self.assertEqual(child_state["parent_session_id"], parent_state["session_id"])
        self.assertTrue(child_state["resumed_from_handoff"])
        self.assertEqual(child_state["phase"], "plan")
        self.assertEqual(child_state["execution_mode"], "auto")
        self.assertEqual(child_state["contract_status"], "draft")
        self.assertEqual(child_state["last_evaluation_verdict"], "")
        self.assertEqual(child_state["last_evaluation_scores"], [])
        self.assertFalse(child_state["needs_evaluation"])
        self.assertIn("- Current phase: plan", (child_session_path / "handoff.md").read_text(encoding="utf-8"))
        self.assertTrue((child_session_path / "artifacts" / "live-eval" / "eval-r0.md").exists())

    def test_live_eval_records_flow_summary(self) -> None:
        self.init_session("Live Eval Flow")
        flow_path = self.root / "qa-flow.json"
        flow_path.write_text(
            json.dumps(
                {
                    "name": "basic-flow",
                    "command_checks": [
                        {
                            "name": "db-check",
                            "command": "printf 'db ok\\n'",
                            "expect_contains": "db ok",
                        }
                    ],
                    "steps": [
                        {"type": "goto", "url": "/"},
                        {"type": "assert_text", "text": "Hello"},
                    ],
                }
            ),
            encoding="utf-8",
        )
        fake_payload = {
            "ok": True,
            "status": 200,
            "url": "https://example.com",
            "headers": {"Content-Type": "text/html"},
            "body": "<html><title>Example</title><body>Hello</body></html>",
            "error": "",
        }
        fake_audit = {
            "ok": True,
            "available": True,
            "error": "",
            "screenshot_path": "",
            "console_messages": [],
            "page_errors": [],
            "failed_requests": [],
            "response_errors": [],
            "interactive_summary": {},
            "interaction_checks": [],
            "flow_name": "basic-flow",
            "flow_results": [
                {"name": "step-1", "type": "goto", "ok": True},
                {"name": "step-2", "type": "assert_text", "ok": True},
            ],
        }
        with (
            mock.patch.object(live_eval, "_fetch_url", return_value=fake_payload),
            mock.patch.object(live_eval, "_run_playwright_audit", return_value=fake_audit),
        ):
            live_eval.run_live_eval(None, "https://example.com", 5, "auto", str(flow_path))
        _, state = harness_lib.load_state(None)
        self.assertTrue(state["qa_flow_path"].endswith("qa-flow.json"))
        artifact_path = current_session_path(self.root) / state["last_live_eval_artifact"]
        artifact = artifact_path.read_text(encoding="utf-8")
        self.assertIn("## Flow Execution", artifact)
        self.assertIn("Steps executed: 2", artifact)
        self.assertIn("## Command Checks", artifact)
        json_payload = json.loads(artifact_path.with_suffix(".json").read_text(encoding="utf-8"))
        self.assertEqual(len(json_payload["command_checks"]), 1)
        self.assertTrue(json_payload["command_checks"][0]["ok"])

    def test_live_eval_prefers_final_page_metadata_from_browser_audit(self) -> None:
        self.init_session("Live Eval Final Metadata")
        fake_payload = {
            "ok": True,
            "status": 200,
            "url": "https://example.com/start",
            "headers": {"Content-Type": "text/html"},
            "body": "<html><title>Start</title><body>Start page</body></html>",
            "error": "",
        }
        fake_audit = {
            "ok": True,
            "available": True,
            "error": "",
            "screenshot_path": "",
            "console_messages": [],
            "page_errors": [],
            "failed_requests": [],
            "response_errors": [],
            "interactive_summary": {"title": "Final Page"},
            "interaction_checks": [],
            "flow_name": "redirected-flow",
            "flow_results": [{"name": "step-1", "type": "goto", "ok": True}],
            "final_url": "https://example.com/final",
            "final_title": "Final Page",
            "final_html": "<html><title>Final Page</title><body>Final body</body></html>",
            "final_content_type": "text/html; charset=utf-8",
            "final_status": 204,
        }
        with (
            mock.patch.object(live_eval, "_fetch_url", return_value=fake_payload),
            mock.patch.object(live_eval, "_run_playwright_audit", return_value=fake_audit),
        ):
            live_eval.run_live_eval(None, "https://example.com/start", 5, "auto", None)
        _, state = harness_lib.load_state(None)
        artifact_path = current_session_path(self.root) / state["last_live_eval_artifact"]
        artifact = artifact_path.read_text(encoding="utf-8")
        json_payload = json.loads(artifact_path.with_suffix(".json").read_text(encoding="utf-8"))

        self.assertIn("Final Page", artifact)
        self.assertIn("Final body", artifact)
        self.assertEqual(json_payload["url"], "https://example.com/final")
        self.assertEqual(json_payload["title"], "Final Page")
        self.assertEqual(json_payload["status"], 204)
        self.assertEqual(json_payload["headers"]["Content-Type"], "text/html; charset=utf-8")

    def test_doctor_honors_explicit_session_without_pointer(self) -> None:
        session_path = self.init_session("Doctor Session")
        pointer_path = self.root / ".harness-design-kit" / "current.json"
        pointer_path.unlink()

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            harness_state.doctor(session_path.name)
        output = buffer.getvalue()

        self.assertIn(session_path.name, output)
        self.assertIn("valid=yes", output)

    def test_doctor_returns_non_zero_for_invalid_session(self) -> None:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = harness_state.main(["--session", "does-not-exist", "doctor"])
        output = buffer.getvalue()

        self.assertEqual(exit_code, 1)
        self.assertIn("Current session: invalid", output)

    def test_doctor_handles_corrupt_current_pointer(self) -> None:
        self.init_session("Doctor Corrupt Pointer")
        pointer_path = self.root / ".harness-design-kit" / "current.json"
        pointer_path.write_text("{invalid\n", encoding="utf-8")

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = harness_state.doctor(None)
        output = buffer.getvalue()

        self.assertEqual(exit_code, 1)
        self.assertIn("Current session: invalid", output)

    def test_doctor_prefers_explicit_session_over_corrupt_pointer(self) -> None:
        session_path = self.init_session("Doctor Explicit Session")
        pointer_path = self.root / ".harness-design-kit" / "current.json"
        pointer_path.write_text("{invalid\n", encoding="utf-8")

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            exit_code = harness_state.doctor(session_path.name)
        output = buffer.getvalue()

        self.assertEqual(exit_code, 0)
        self.assertIn(session_path.name, output)
        self.assertIn("valid=yes", output)

    def test_resume_from_handoff_requires_paused_handoff_session(self) -> None:
        self.init_session("Manual Handoff")
        harness_state.write_handoff(None, "manual note")
        with self.assertRaises(harness_lib.ValidationError):
            harness_state.resume_from_handoff(None, "should fail")

    def test_record_evaluation_rejects_duplicate_criteria(self) -> None:
        session_path = self.init_session("Duplicate Eval")
        self.advance_app_session_to_evaluate(session_path)
        artifact_path = session_path / "artifacts" / "proof.txt"
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact_path.write_text("proof\n", encoding="utf-8")
        (session_path / "evaluation.md").write_text(
            """# Evaluation

## Verdict
- Evaluator: qa-evaluator
- Verdict: pass
- Round: 1

## Score Breakdown
- Criterion: product depth
- Score: 8
- Threshold: 7
- Weight: 1.0
- Criterion: functionality
- Score: 8
- Threshold: 7
- Weight: 1.0
- Criterion: visual design
- Score: 8
- Threshold: 7
- Weight: 1.0
- Criterion: visual design
- Score: 10
- Threshold: 7
- Weight: 3.0
- Criterion: code quality
- Score: 8
- Threshold: 7
- Weight: 1.0

## Findings
- Duplicate criteria should fail validation.

## Evidence
- Reviewed the evaluation artifact.

## Reproduction Steps
- Open the generated dashboard.

## Artifact References
- artifacts/proof.txt

## Recommendation
- accept the scope
""",
            encoding="utf-8",
        )

        with self.assertRaises(harness_lib.ValidationError):
            harness_state.record_evaluation(None, "pass", "qa-evaluator")

    def test_record_evaluation_rejects_failing_live_eval_flow(self) -> None:
        session_path = self.init_session("Flow Gate")
        self.advance_app_session_to_evaluate(session_path)
        harness_state.set_field(None, "qa_target_url", "https://example.com")
        harness_state.set_field(None, "qa_flow_path", "qa-flow.json")
        live_eval_dir = session_path / "artifacts" / "live-eval"
        live_eval_dir.mkdir(parents=True, exist_ok=True)
        md_path = live_eval_dir / "eval-r0.md"
        json_path = live_eval_dir / "eval-r0.json"
        md_path.write_text(
            """# Live Evaluation

## Flow Execution
- Flow name: failing-flow
- Steps executed: 1
- Failed steps: 1
- submit: click (failed) - boom
""",
            encoding="utf-8",
        )
        json_path.write_text(
            json.dumps(
                {
                    "browser_audit": {
                        "ok": False,
                        "flow_results": [
                            {"name": "submit", "type": "click", "ok": False, "error": "boom"}
                        ],
                    }
                }
            ),
            encoding="utf-8",
        )
        harness_state.set_live_eval_artifact(None, "artifacts/live-eval/eval-r0.md")
        write_app_evaluation(
            session_path,
            verdict="pass",
            artifact_ref="artifacts/live-eval/eval-r0.md",
        )

        with self.assertRaises(harness_lib.ValidationError):
            harness_state.record_evaluation(None, "pass", "qa-evaluator")

    def test_live_eval_flow_failure_raises_validation_error(self) -> None:
        self.init_session("Live Eval Failed Flow")
        flow_path = self.root / "qa-flow-invalid.json"
        flow_path.write_text(
            json.dumps({"name": "failing-flow", "steps": [{"type": "goto", "url": "/"}]}),
            encoding="utf-8",
        )
        fake_payload = {
            "ok": True,
            "status": 200,
            "url": "https://example.com",
            "headers": {"Content-Type": "text/html"},
            "body": "<html><title>Example</title><body>Hello</body></html>",
            "error": "",
        }
        failed_audit = {
            "ok": False,
            "available": True,
            "error": "flow failed",
            "screenshot_path": "",
            "console_messages": [],
            "page_errors": [],
            "failed_requests": [],
            "response_errors": [],
            "interactive_summary": {},
            "interaction_checks": [],
            "flow_name": "failing-flow",
            "flow_results": [
                {"name": "step-1", "type": "goto", "ok": False, "error": "boom"},
            ],
        }
        with (
            mock.patch.object(live_eval, "_fetch_url", return_value=fake_payload),
            mock.patch.object(live_eval, "_run_playwright_audit", return_value=failed_audit),
        ):
            with self.assertRaises(harness_lib.ValidationError):
                live_eval.run_live_eval(None, "https://example.com", 5, "auto", str(flow_path))
        _, state = harness_lib.load_state(None)
        artifact_path = current_session_path(self.root) / state["last_live_eval_artifact"]
        self.assertTrue(artifact_path.exists())

    def test_live_eval_command_check_failure_raises_validation_error(self) -> None:
        self.init_session("Live Eval Failed Command Check")
        flow_path = self.root / "qa-flow-command-fail.json"
        flow_path.write_text(
            json.dumps(
                {
                    "name": "failing-command-flow",
                    "command_checks": [
                        {
                            "name": "sqlite-state",
                            "command": "printf 'row-count=0\\n'",
                            "expect_contains": "row-count=1",
                        }
                    ],
                    "steps": [{"type": "goto", "url": "/"}],
                }
            ),
            encoding="utf-8",
        )
        fake_payload = {
            "ok": True,
            "status": 200,
            "url": "https://example.com",
            "headers": {"Content-Type": "text/html"},
            "body": "<html><title>Example</title><body>Hello</body></html>",
            "error": "",
        }
        good_audit = {
            "ok": True,
            "available": True,
            "error": "",
            "screenshot_path": "",
            "console_messages": [],
            "page_errors": [],
            "failed_requests": [],
            "response_errors": [],
            "interactive_summary": {},
            "interaction_checks": [],
            "flow_name": "failing-command-flow",
            "flow_results": [{"name": "step-1", "type": "goto", "ok": True}],
        }
        with (
            mock.patch.object(live_eval, "_fetch_url", return_value=fake_payload),
            mock.patch.object(live_eval, "_run_playwright_audit", return_value=good_audit),
        ):
            with self.assertRaises(harness_lib.ValidationError):
                live_eval.run_live_eval(None, "https://example.com", 5, "auto", str(flow_path))

    def test_live_eval_uses_unique_artifact_names_within_round(self) -> None:
        self.init_session("Live Eval Unique Artifacts")
        fake_payload = {
            "ok": True,
            "status": 200,
            "url": "https://example.com",
            "headers": {"Content-Type": "text/html"},
            "body": "<html><title>Example</title><body>Hello</body></html>",
            "error": "",
        }
        with mock.patch.object(live_eval, "_fetch_url", return_value=fake_payload):
            live_eval.run_live_eval(None, "https://example.com", 5, "never", None)
            first_artifact = harness_lib.load_state(None)[1]["last_live_eval_artifact"]
            live_eval.run_live_eval(None, "https://example.com", 5, "never", None)
            second_artifact = harness_lib.load_state(None)[1]["last_live_eval_artifact"]

        session_path = current_session_path(self.root)
        self.assertTrue((session_path / first_artifact).exists())
        self.assertTrue((session_path / second_artifact).exists())
        self.assertNotEqual(first_artifact, second_artifact)
        self.assertTrue(second_artifact.endswith("eval-r0-2.md"))

    def test_prepare_compaction_writes_compact_state(self) -> None:
        session_path = self.init_session("Compact Session")
        harness_state.prepare_compaction(None, "conversation grew noisy")
        compact_state = (session_path / "compact-state.md").read_text(encoding="utf-8")
        _, state = harness_lib.load_state(None)
        self.assertIn("## Session Snapshot", compact_state)
        self.assertEqual(state["compaction_count"], 1)
        self.assertEqual(state["last_compaction_reason"], "conversation grew noisy")

    def test_check_reset_prefers_compaction_before_reset(self) -> None:
        session_path = self.init_session("Auto Context Guard")
        harness_state.append_session_event(None, "evaluation_recorded", json.dumps({"verdict": "fail"}))

        buffer = io.StringIO()
        with redirect_stdout(buffer):
            harness_run.check_reset(None)
        output = buffer.getvalue()
        _, compacted_state = harness_lib.load_state(None)

        self.assertIn("Compaction prepared", output)
        self.assertEqual(compacted_state["phase"], "clarify")
        self.assertEqual(compacted_state["status"], "in_progress")
        self.assertEqual(compacted_state["compaction_count"], 1)
        self.assertTrue((session_path / "compact-state.md").exists())

        harness_state.append_session_event(None, "evaluation_recorded", json.dumps({"verdict": "fail"}))
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            harness_run.check_reset(None)
        output = buffer.getvalue()
        _, reset_state = harness_lib.load_state(None)

        self.assertIn("Auto reset prepared", output)
        self.assertEqual(reset_state["phase"], "handoff")
        self.assertEqual(reset_state["status"], "paused")
        self.assertEqual(reset_state["execution_mode"], "reset")

    def test_orchestrator_run_loop_completes_continuous_app_session(self) -> None:
        self.init_session("Runner Driven Session", "app", "continuous")
        runner_path = self.create_fake_runner()
        with mock.patch.dict(
            os.environ,
            {
                "HARNESS_DESIGN_KIT_AGENT_RUNNER": f"python3 {runner_path}",
                "HARNESS_DESIGN_KIT_PROVIDER": "external",
            },
            clear=False,
        ):
            harness_orchestrator.run_loop(None, 8)
        session_path = current_session_path(self.root)
        _, state = harness_lib.load_state(None)

        self.assertEqual(state["phase"], "completed")
        self.assertEqual(state["status"], "completed")
        self.assertEqual(state["last_evaluation_verdict"], "pass")
        self.assertEqual(state["contract_status"], "approved")
        self.assertIn("Build a durable workflow harness", (session_path / "product-spec.md").read_text(encoding="utf-8"))
        self.assertIn("Deliver one fully automated orchestration pass", (session_path / "sprint-contract.md").read_text(encoding="utf-8"))
        self.assertIn("Added the orchestration loop script", (session_path / "progress.md").read_text(encoding="utf-8"))
        self.assertIn("Verdict: pass", (session_path / "evaluation.md").read_text(encoding="utf-8"))
        review_dir = session_path / "artifacts" / "contract-reviews"
        self.assertTrue(review_dir.exists())

    def test_native_openai_runner_completes_continuous_app_session(self) -> None:
        self.init_session("Native Continuous App", "app", "continuous")

        def responder(actor: str, prompt: str) -> str:
            phase = extract_phase_from_prompt(prompt)
            if actor == "planner":
                return """# Product Spec

## Problem And Target User
- Goal: Build a durable workflow harness.
- Target user: plugin authors shipping long-running app workflows.

## Product Goals
- Automate the next actor selection.
- Keep state transitions explicit.

## Non-Goals
- Do not assume a hosted runner service.

## Design Direction
- Prefer structured markdown artifacts over chat-only state.

## AI Opportunities
- Use a native model runner by default and keep an external override path.

## Sprint Candidates
- Candidate 1: orchestration loop.
- Candidate 2: compaction and QA hardening.

## Verification Risks
- Risk 1: invalid contract artifacts.
- Risk 2: browser runtime drift.
"""
            if actor == "generator" and phase == "contract":
                return """# Sprint Contract

## Objective
- Deliver one fully automated orchestration pass.

## Deliverables
- Add a runner-driven orchestration script.

## Out Of Scope
- Hosted execution services.

## Acceptance Tests
- A continuous app session can reach completed.

## Verification Steps
- Run the harness runtime unit tests.

## Evidence Requirements
- Capture the test command output.

## Exit Criteria
- The session advances through plan, contract, build, and evaluate.

## Contract Status
- Status: draft
- Unit type: sprint
"""
            if actor == "qa-evaluator" and phase == "contract":
                return """# Contract Review

## Contract Decision
- Decision: approve

## Findings
- The contract is specific and testable.
"""
            if actor == "generator" and phase == "build":
                return """# Progress

## Implemented Scope
- Added the orchestration loop script.

## Verification Run
- Command 1: python3 -m unittest -q tests/test_harness_runtime.py
- Result 1: expected green run in CI and local temp workspace.

## Generator Self-Check
- The implemented scope matches the active contract.

## Known Risks
- Browser automation still depends on the cached Playwright runtime.

## Next Suggested Step
- Run the evaluator and capture the final verdict.
"""
            if actor == "qa-evaluator" and phase == "evaluate":
                return """# Evaluation

## Verdict
- Evaluator: qa-evaluator
- Verdict: pass
- Round: 1

## Score Breakdown
- Criterion: product depth
- Score: 8
- Threshold: 7
- Weight: 1.0
- Criterion: functionality
- Score: 8
- Threshold: 7
- Weight: 1.5
- Criterion: visual design
- Score: 7
- Threshold: 7
- Weight: 1.0
- Criterion: code quality
- Score: 8
- Threshold: 7
- Weight: 1.0

## Findings
- The automated harness loop completed the planned slice.

## Evidence
- Reviewed the generated artifacts and state transitions.

## Reproduction Steps
- Initialize a continuous app session and run the orchestrator loop.

## Artifact References
- progress.md

## Recommendation
- accept the scope
"""
            raise AssertionError(f"unexpected actor={actor} phase={phase}")

        with mock.patch.dict(
            os.environ,
            {"HARNESS_DESIGN_KIT_PROVIDER": "openai", "OPENAI_API_KEY": "test-openai"},
            clear=False,
        ):
            with mock.patch.object(
                harness_runner,
                "_request_json",
                side_effect=self.native_runner_side_effect("openai", responder),
            ):
                harness_orchestrator.run_loop(None, 8)

        _, state = harness_lib.load_state(None)
        self.assertEqual(state["phase"], "completed")
        self.assertEqual(state["status"], "completed")
        self.assertEqual(state["last_evaluation_verdict"], "pass")

    def test_contract_review_feedback_is_injected_into_next_contract_prompt(self) -> None:
        self.init_session("Contract Feedback Loop", "app", "continuous")
        runner_path = self.create_contract_feedback_runner()
        with mock.patch.dict(
            os.environ,
            {"HARNESS_DESIGN_KIT_AGENT_RUNNER": f"python3 {runner_path}", "HARNESS_DESIGN_KIT_RUNNER": "external"},
            clear=False,
        ):
            harness_orchestrator.run_loop(None, 8)

        session_path = current_session_path(self.root)
        _, state = harness_lib.load_state(None)
        review_dir = session_path / "artifacts" / "contract-reviews"
        reviews = sorted(review_dir.glob("review-*.md"))

        self.assertEqual(state["phase"], "completed")
        self.assertEqual(state["last_contract_review_decision"], "approve")
        self.assertGreaterEqual(len(reviews), 2)
        self.assertIn("one verifiable slice", (session_path / "sprint-contract.md").read_text(encoding="utf-8").lower())

    def test_compaction_resume_stays_in_same_session_and_clears_context_strategy(self) -> None:
        session_path = self.init_session("Compact Resume Session", "app", "continuous")
        harness_state.prepare_compaction(None, "conversation grew noisy")

        def responder(actor: str, prompt: str) -> str:
            if actor == "compactor":
                return sample_compact_state(
                    "Compact Resume Session",
                    next_step="Expand the product spec into a durable workflow plan.",
                    reason="conversation grew noisy",
                )
            if actor == "planner":
                return """# Product Spec

## Problem And Target User
- Goal: Compact Resume Session
- Target user: plugin authors recovering long sessions.

## Product Goals
- Resume cleanly from a compacted state.

## Non-Goals
- Hosted recovery services.

## Design Direction
- Keep artifacts explicit and durable.

## AI Opportunities
- Use a dedicated compactor actor before resuming implementation.

## Sprint Candidates
- Candidate 1: compact resume.

## Verification Risks
- Risk 1: compact state drifts from verified artifacts.
"""
            raise AssertionError(f"unexpected actor={actor}")

        with mock.patch.dict(
            os.environ,
            {"HARNESS_DESIGN_KIT_PROVIDER": "openai", "OPENAI_API_KEY": "test-openai"},
            clear=False,
        ):
            with mock.patch.object(
                harness_runner,
                "_request_json",
                side_effect=self.native_runner_side_effect("openai", responder),
            ):
                harness_orchestrator.run_once(None)

        _, state = harness_lib.load_state(None)
        self.assertEqual(state["session_id"], session_path.name)
        self.assertEqual(state["compaction_resume_count"], 1)
        self.assertEqual(state["context_strategy"], "full")
        self.assertEqual(state["last_compaction_actor"], "compactor")
        self.assertIn("Goal:", (session_path / "product-spec.md").read_text(encoding="utf-8"))
        self.assertIn("## Accepted Facts", (session_path / "compact-state.md").read_text(encoding="utf-8"))

    def test_frontend_native_openai_runner_tracks_candidate_history_until_accept(self) -> None:
        self.init_session("Frontend Candidate Loop", "frontend", "continuous")

        def responder(actor: str, prompt: str) -> str:
            phase = extract_phase_from_prompt(prompt)
            round_number = extract_round_from_prompt(prompt)
            if actor == "compactor":
                return sample_compact_state(
                    "Frontend Candidate Loop",
                    next_step="Resume the active frontend round using the latest accepted evidence.",
                    reason="frontend iteration needed compaction",
                )
            if actor == "planner":
                return """# Product Spec

## Problem And Target User
- Goal: Produce a strong landing page exploration loop.
- Target user: teams iterating on a marketing launch page.

## Product Goals
- Explore multiple visual candidates.
- Keep evaluation strict on design quality and originality.

## Non-Goals
- Shipping hosted orchestration services.

## Design Direction
- Favor bold composition and differentiated hierarchy.

## AI Opportunities
- Use refine and pivot loops instead of one-pass generation.

## Sprint Candidates
- Candidate 1: hero and narrative structure.
- Candidate 2: alternate visual treatment.

## Verification Risks
- Risk 1: candidates converge to the same direction.
- Risk 2: evaluator becomes too lenient.
"""
            if actor == "generator" and phase == "build":
                return f"""# Progress

## Implemented Scope
- Produced candidate round {round_number} with a distinct layout direction.

## Verification Run
- Command 1: inspect the generated page manually.
- Result 1: candidate artifact is ready for evaluation.

## Generator Self-Check
- The candidate matches the current strategy and round intent.

## Known Risks
- The next evaluator may still ask for a pivot if originality remains weak.

## Next Suggested Step
- Run the design evaluator on this candidate.
"""
            if actor == "design-evaluator" and phase == "evaluate":
                if round_number <= 1:
                    verdict = "revise"
                    recommendation = "refine the existing candidate"
                    design_score = 7
                    originality_score = 6
                elif round_number == 2:
                    verdict = "pivot"
                    recommendation = "pivot to a new candidate direction"
                    design_score = 7
                    originality_score = 6
                else:
                    verdict = "pass"
                    recommendation = "accept the candidate"
                    design_score = 9
                    originality_score = 8
                return f"""# Evaluation

## Verdict
- Evaluator: design-evaluator
- Verdict: {verdict}
- Round: {round_number}

## Score Breakdown
- Criterion: design quality
- Score: {design_score}
- Threshold: 7
- Weight: 2.0
- Criterion: originality
- Score: {originality_score}
- Threshold: 7
- Weight: 2.0
- Criterion: craft
- Score: 8
- Threshold: 7
- Weight: 1.0
- Criterion: functionality
- Score: 8
- Threshold: 7
- Weight: 1.0

## Findings
- The candidate needs a stronger visual distinction before acceptance.

## Evidence
- Reviewed the rendered candidate and supporting notes.

## Reproduction Steps
- Open the candidate page and compare the visual direction against the brief.

## Artifact References
- progress.md

## Recommendation
- {recommendation}
"""
            raise AssertionError(f"unexpected actor={actor} phase={phase}")

        with mock.patch.dict(
            os.environ,
            {"HARNESS_DESIGN_KIT_PROVIDER": "openai", "OPENAI_API_KEY": "test-openai"},
            clear=False,
        ):
            with mock.patch.object(
                harness_runner,
                "_request_json",
                side_effect=self.native_runner_side_effect("openai", responder),
            ):
                harness_orchestrator.run_loop(None, 12)

        _, state = harness_lib.load_state(None)
        statuses = {entry["status"] for entry in state["candidates"]}
        self.assertEqual(state["phase"], "completed")
        self.assertEqual(state["last_evaluation_verdict"], "pass")
        self.assertEqual(state["last_evaluation_recommendation"], "accept")
        self.assertGreaterEqual(state["current_round"], 3)
        self.assertTrue(state["best_candidate_id"])
        self.assertIn("accepted", statuses)
        self.assertIn("superseded", statuses)

    def test_build_actor_prompt_includes_calibration_anchors_for_evaluator(self) -> None:
        self.init_session("Prompt Calibration", "frontend", "continuous")
        harness_run.advance(None)
        harness_run.advance(None)
        harness_run.advance(None)

        actor, prompt = harness_orchestrator.build_actor_prompt(None)

        self.assertEqual(actor, "design-evaluator")
        self.assertIn("## Calibration Anchors", prompt)
        self.assertIn("Frontend Good Example", prompt)
        self.assertIn("Frontend Bad Example", prompt)


if __name__ == "__main__":
    unittest.main()
