from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PLUGIN_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import harness_lib  # noqa: E402
import harness_orchestrator  # noqa: E402
import harness_runner  # noqa: E402
import harness_state  # noqa: E402


def current_session_path(root: Path) -> Path:
    pointer = json.loads((root / ".harness-design-kit" / "current.json").read_text(encoding="utf-8"))
    return root / pointer["session_path"]


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


def native_response_payload(provider: str, markdown: str) -> dict[str, object]:
    if provider == "anthropic":
        return {"content": [{"type": "text", "text": markdown}]}
    return {"output": [{"content": [{"type": "output_text", "text": markdown}]}]}


class HarnessNativeRunnerTests(unittest.TestCase):
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

    def native_runner_side_effect(self, provider: str, responder):
        def side_effect(url: str, headers: dict[str, str], payload: dict[str, object]) -> dict[str, object]:
            prompt = extract_prompt_from_payload(payload)
            actor = extract_actor_from_prompt(prompt)
            markdown = responder(actor, prompt, url, headers, payload)
            return native_response_payload(provider, markdown)

        return side_effect

    def test_provider_selection_prefers_explicit_provider(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "HARNESS_DESIGN_KIT_PROVIDER": "openai",
                "OPENAI_API_KEY": "openai-key",
                "ANTHROPIC_API_KEY": "anthropic-key",
            },
            clear=False,
        ):
            self.assertEqual(harness_runner.configured_provider(), "openai")

    def test_provider_selection_autodetects_anthropic_before_openai(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "OPENAI_API_KEY": "openai-key",
                "ANTHROPIC_API_KEY": "anthropic-key",
            },
            clear=True,
        ):
            self.assertEqual(harness_runner.configured_provider(), "anthropic")

    def test_run_actor_requires_configured_provider(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(harness_runner.RunnerError):
                harness_runner.run_actor("planner", "test prompt", {}, Path.cwd())

    def test_configured_model_prefers_role_specific_and_compaction_overrides(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "HARNESS_DESIGN_KIT_PROVIDER": "openai",
                "HARNESS_DESIGN_KIT_MODEL": "shared-model",
                "HARNESS_DESIGN_KIT_MODEL_PLANNER": "planner-model",
                "HARNESS_DESIGN_KIT_MODEL_EVALUATOR": "evaluator-model",
                "HARNESS_DESIGN_KIT_COMPACTION_MODEL": "compaction-model",
            },
            clear=True,
        ):
            self.assertEqual(harness_runner.configured_model("planner"), "planner-model")
            self.assertEqual(harness_runner.configured_model("generator"), "shared-model")
            self.assertEqual(harness_runner.configured_model("qa-evaluator"), "evaluator-model")
            self.assertEqual(harness_runner.configured_model("compactor"), "compaction-model")

    def test_openai_responses_payload_is_parsed(self) -> None:
        captured: dict[str, object] = {}

        def fake_request(url: str, headers: dict[str, str], payload: dict[str, object]) -> dict[str, object]:
            captured["url"] = url
            captured["headers"] = headers
            captured["payload"] = payload
            return native_response_payload(
                "openai",
                "# Product Spec\n\n## Problem And Target User\n- Goal: payload parsing\n",
            )

        with mock.patch.dict(
            os.environ,
            {"HARNESS_DESIGN_KIT_PROVIDER": "openai", "OPENAI_API_KEY": "test-openai"},
            clear=True,
        ):
            with mock.patch.object(harness_runner, "_request_json", side_effect=fake_request):
                result = harness_runner.run_actor("planner", "prompt body", {"phase": "clarify"}, Path.cwd())

        self.assertEqual(result.provider, "openai")
        self.assertEqual(result.model, harness_runner.configured_model("planner", "openai"))
        self.assertIn("/responses", str(captured["url"]))
        payload = captured["payload"]
        self.assertIsInstance(payload, dict)
        self.assertEqual(payload["model"], result.model)
        self.assertIn("prompt body", extract_prompt_from_payload(payload))
        self.assertIn("Product Spec", result.output)

    def test_anthropic_messages_payload_is_parsed(self) -> None:
        captured: dict[str, object] = {}

        def fake_request(url: str, headers: dict[str, str], payload: dict[str, object]) -> dict[str, object]:
            captured["url"] = url
            captured["headers"] = headers
            captured["payload"] = payload
            return native_response_payload(
                "anthropic",
                "# Evaluation\n\n## Verdict\n- Evaluator: qa-evaluator\n- Verdict: pass\n- Round: 1\n",
            )

        with mock.patch.dict(
            os.environ,
            {"HARNESS_DESIGN_KIT_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "test-anthropic"},
            clear=True,
        ):
            with mock.patch.object(harness_runner, "_request_json", side_effect=fake_request):
                result = harness_runner.run_actor("qa-evaluator", "prompt body", {"phase": "evaluate"}, Path.cwd())

        self.assertEqual(result.provider, "anthropic")
        self.assertIn("/messages", str(captured["url"]))
        payload = captured["payload"]
        self.assertIsInstance(payload, dict)
        self.assertEqual(payload["model"], result.model)
        self.assertEqual(payload["messages"][0]["content"], "prompt body")
        self.assertIn("Verdict", result.output)

    def test_external_runner_override_is_supported(self) -> None:
        runner_path = self.root / "external_runner.py"
        runner_path.write_text(
            """#!/usr/bin/env python3
print("# Progress\\n\\n## Implemented Scope\\n- External runner path works.\\n")
""",
            encoding="utf-8",
        )
        runner_path.chmod(0o755)

        with mock.patch.dict(
            os.environ,
            {
                "HARNESS_DESIGN_KIT_PROVIDER": "external",
                "HARNESS_DESIGN_KIT_AGENT_RUNNER": f"python3 {runner_path}",
            },
            clear=True,
        ):
            result = harness_runner.run_actor("generator", "prompt body", {"phase": "build"}, self.root)

        self.assertEqual(result.provider, "external")
        self.assertEqual(result.model, "external-command")
        self.assertIn("External runner path works", result.output)

    def test_anthropic_runner_completes_orchestrator_loop(self) -> None:
        self.init_session("Anthropic Loop", "app", "continuous")

        def responder(actor: str, prompt: str, url: str, headers: dict[str, str], payload: dict[str, object]) -> str:
            phase = extract_phase_from_prompt(prompt)
            if actor == "planner":
                return """# Product Spec

## Problem And Target User
- Goal: Validate the Anthropic native path.
- Target user: plugin authors running local harness loops.

## Product Goals
- Keep the provider abstraction local.

## Non-Goals
- Hosted orchestration services.

## Design Direction
- Use file-based artifacts and explicit transitions.

## AI Opportunities
- Run planner, generator, and evaluator through native providers.

## Sprint Candidates
- Candidate 1: provider adapters.

## Verification Risks
- Risk 1: request payload drift.
"""
            if actor == "generator" and phase == "contract":
                return """# Sprint Contract

## Objective
- Deliver a native Anthropic-backed loop.

## Deliverables
- Add a local provider adapter.

## Out Of Scope
- Hosted execution services.

## Acceptance Tests
- A continuous app session can complete through the native provider path.

## Verification Steps
- Run the orchestrator loop in a temp session.

## Evidence Requirements
- Capture the generated artifacts.

## Exit Criteria
- Planner, contract review, build, and evaluation all complete.

## Contract Status
- Status: draft
- Unit type: sprint
"""
            if actor == "qa-evaluator" and phase == "contract":
                return """# Contract Review

## Contract Decision
- Decision: approve

## Findings
- The contract is narrow and testable.
"""
            if actor == "generator" and phase == "build":
                return """# Progress

## Implemented Scope
- Routed the actor through the Anthropic provider path.

## Verification Run
- Command 1: python3 scripts/harness_orchestrator.py run-loop --max-steps 8
- Result 1: expected green loop in the temp session.

## Generator Self-Check
- The provider path matches the approved contract.

## Known Risks
- Real credentials are still required outside the test harness.

## Next Suggested Step
- Run the evaluator.
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
- Score: 8
- Threshold: 7
- Weight: 1.0
- Criterion: code quality
- Score: 8
- Threshold: 7
- Weight: 1.0

## Findings
- The native Anthropic loop produced the required artifacts.

## Evidence
- Reviewed the generated state and markdown artifacts.

## Reproduction Steps
- Initialize a session and run the loop once.

## Artifact References
- progress.md

## Recommendation
- accept the scope
"""
            raise AssertionError(f"unexpected actor={actor} phase={phase}")

        with mock.patch.dict(
            os.environ,
            {"HARNESS_DESIGN_KIT_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "test-anthropic"},
            clear=False,
        ):
            with mock.patch.object(
                harness_runner,
                "_request_json",
                side_effect=self.native_runner_side_effect("anthropic", responder),
            ):
                harness_orchestrator.run_loop(None, 8)

        _, state = harness_lib.load_state(None)
        self.assertEqual(state["phase"], "completed")
        self.assertEqual(state["last_runner_provider"], "anthropic")
        self.assertEqual(state["last_evaluation_verdict"], "pass")

    def test_compaction_failure_escalates_to_reset_after_two_failed_native_runs(self) -> None:
        self.init_session("Compaction Reset", "app", "continuous")
        harness_state.prepare_compaction(None, "conversation drifted")

        with mock.patch.dict(
            os.environ,
            {"HARNESS_DESIGN_KIT_PROVIDER": "openai", "OPENAI_API_KEY": "test-openai"},
            clear=False,
        ):
            with mock.patch.object(
                harness_runner,
                "_request_json",
                side_effect=harness_runner.RunnerError("forced compactor failure"),
            ):
                harness_orchestrator.run_once(None)
                _, first_state = harness_lib.load_state(None)
                self.assertEqual(first_state["context_strategy"], "compact")
                self.assertEqual(first_state["compaction_cycle_failures"], 1)
                self.assertEqual(first_state["phase"], "clarify")

                harness_orchestrator.run_once(None)

        _, state = harness_lib.load_state(None)
        self.assertEqual(state["phase"], "handoff")
        self.assertEqual(state["status"], "paused")
        self.assertEqual(state["execution_mode"], "reset")


if __name__ == "__main__":
    unittest.main()
