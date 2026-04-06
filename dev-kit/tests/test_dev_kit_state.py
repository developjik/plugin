from __future__ import annotations

import argparse
import importlib.util
import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "dev_kit_state.py"
SESSION_START_HOOK = PLUGIN_ROOT / "hooks" / "session-start.sh"
USER_PROMPT_SUBMIT_HOOK = PLUGIN_ROOT / "hooks" / "user-prompt-submit.sh"
SPEC = importlib.util.spec_from_file_location("dev_kit_state", SCRIPT_PATH)
assert SPEC and SPEC.loader
dev_kit_state = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(dev_kit_state)


def workflow_state(
    session_id: str = "2026-04-06T16-30-example",
    *,
    status: str = "in_progress",
    current_phase: str = "clarify",
    execution_profile: str | None = None,
    plan_status: str = "not_started",
    plan_version: int = 0,
    next_action: str = "Complete clarify and write brief.md.",
    brief: str | None = None,
    plan: str | None = None,
    plan_review: str | None = None,
    review: str | None = None,
    phase_status: dict[str, str] | None = None,
    updated_at: str = "2026-04-06T16:45:00+09:00",
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "session_id": session_id,
        "title": "Example Session",
        "feature_slug": "example",
        "status": status,
        "current_phase": current_phase,
        "execution_profile": execution_profile,
        "plan_status": plan_status,
        "plan_version": plan_version,
        "next_action": next_action,
        "artifacts": {
            "brief": brief,
            "plan": plan,
            "plan_review": plan_review,
            "review": review,
        },
        "phase_status": phase_status or {},
        "created_at": "2026-04-06T16:30:00+09:00",
        "updated_at": updated_at,
    }


def approved_plan_state(
    session_id: str = "2026-04-06T16-30-example",
    *,
    status: str = "in_progress",
    current_phase: str = "execute",
    next_action: str = "Run execute. Read .dev-kit/sessions/2026-04-06T16-30-example/plan.md.",
    review: str | None = None,
    phase_status: dict[str, str] | None = None,
) -> dict[str, object]:
    return workflow_state(
        session_id,
        status=status,
        current_phase=current_phase,
        execution_profile="medium",
        plan_status="approved",
        plan_version=1,
        next_action=next_action,
        brief=f".dev-kit/sessions/{session_id}/brief.md",
        plan=f".dev-kit/sessions/{session_id}/plan.md",
        plan_review=f".dev-kit/sessions/{session_id}/plan-review.md",
        review=review,
        phase_status=phase_status or {"P1": "pending"},
    )


def write_session(root: Path, payload: dict[str, object], *, session_dir_name: str | None = None) -> tuple[Path, dict[str, object]]:
    session_id = str(payload["session_id"])
    session_name = session_dir_name or session_id
    session_rel = Path(".dev-kit/sessions") / session_name
    session_dir = root / session_rel
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / "state.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    artifacts = payload.get("artifacts", {})
    if isinstance(artifacts, dict):
        for artifact_path in artifacts.values():
            if not isinstance(artifact_path, str):
                continue
            full_path = root / artifact_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text("# placeholder\n", encoding="utf-8")
    return session_dir, payload


def write_current_pointer(root: Path, session_id: str, *, session_path: str | None = None) -> None:
    current_path = root / ".dev-kit" / "current.json"
    current_path.parent.mkdir(parents=True, exist_ok=True)
    current_path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "session_id": session_id,
                "session_path": session_path or f".dev-kit/sessions/{session_id}",
                "updated_at": "2026-04-06T16:45:00+09:00",
            }
        ),
        encoding="utf-8",
    )


def run_hook(script_path: Path, cwd: Path, payload: dict[str, object]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(script_path)],
        cwd=cwd,
        env={**os.environ, "PLUGIN_ROOT": str(PLUGIN_ROOT)},
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=True,
    )


class DevKitStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = dev_kit_state.load_state_schema()

    def test_resolve_workspace_root_prefers_env_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            with mock.patch.dict("os.environ", {"DEV_KIT_STATE_ROOT": str(root)}, clear=False):
                resolved = dev_kit_state.resolve_workspace_root(root / "subdir")
            self.assertEqual(resolved, root.resolve())

    def test_resolve_workspace_root_uses_git_toplevel(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True, text=True)
            nested = root / "nested"
            nested.mkdir()
            with mock.patch.dict("os.environ", {}, clear=False):
                resolved = dev_kit_state.resolve_workspace_root(nested)
            self.assertEqual(resolved, root.resolve())

    def test_resolve_workspace_root_falls_back_to_current_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            with mock.patch.dict("os.environ", {}, clear=False):
                with mock.patch.object(
                    dev_kit_state.subprocess,
                    "run",
                    side_effect=subprocess.CalledProcessError(1, ["git"]),
                ):
                    resolved = dev_kit_state.resolve_workspace_root(root)
            self.assertEqual(resolved, root.resolve())

    def test_validate_state_payload_accepts_clarify_initial_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            session_id = "2026-04-06T16-30-example"
            session_dir, _ = write_session(root, workflow_state(session_id))
            self.assertEqual(
                dev_kit_state.validate_state_payload(
                    workflow_state(session_id),
                    self.schema,
                    root,
                    session_path=session_dir,
                ),
                [],
            )

    def test_validate_state_payload_accepts_documented_workflow_transitions(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            session_id = "2026-04-06T16-30-example"
            session_dir = root / ".dev-kit" / "sessions" / session_id
            session_dir.mkdir(parents=True, exist_ok=True)

            cases = {
                "clarify init": workflow_state(session_id),
                "clarify to planning": workflow_state(
                    session_id,
                    current_phase="planning",
                    execution_profile="medium",
                    next_action=f"Run planning. Read .dev-kit/sessions/{session_id}/brief.md.",
                    brief=f".dev-kit/sessions/{session_id}/brief.md",
                ),
                "planning drafting": workflow_state(
                    session_id,
                    current_phase="planning",
                    execution_profile="medium",
                    plan_status="drafting",
                    plan_version=1,
                    next_action="Draft plan v1.",
                    brief=f".dev-kit/sessions/{session_id}/brief.md",
                ),
                "planning critique": workflow_state(
                    session_id,
                    current_phase="planning",
                    execution_profile="medium",
                    plan_status="in_review",
                    plan_version=1,
                    next_action="Critique plan v1.",
                    brief=f".dev-kit/sessions/{session_id}/brief.md",
                    plan=f".dev-kit/sessions/{session_id}/plan.md",
                    plan_review=f".dev-kit/sessions/{session_id}/plan-review.md",
                ),
                "planning revise": workflow_state(
                    session_id,
                    current_phase="planning",
                    execution_profile="medium",
                    plan_status="revising",
                    plan_version=1,
                    next_action="Revise plan v1.",
                    brief=f".dev-kit/sessions/{session_id}/brief.md",
                    plan=f".dev-kit/sessions/{session_id}/plan.md",
                    plan_review=f".dev-kit/sessions/{session_id}/plan-review.md",
                ),
                "planning to execute": approved_plan_state(
                    session_id,
                    current_phase="execute",
                    next_action=f"Run execute. Read .dev-kit/sessions/{session_id}/plan.md.",
                    phase_status={"P1": "pending", "P2": "pending"},
                ),
                "execute to review": approved_plan_state(
                    session_id,
                    current_phase="review",
                    next_action=f"Run review. Read .dev-kit/sessions/{session_id}/plan.md.",
                    phase_status={"P1": "completed", "P2": "completed"},
                ),
                "review pass": approved_plan_state(
                    session_id,
                    status="completed",
                    current_phase="review",
                    next_action="Session complete.",
                    review=f".dev-kit/sessions/{session_id}/review.md",
                    phase_status={"P1": "completed", "P2": "completed"},
                ),
                "review fail to execute": approved_plan_state(
                    session_id,
                    status="in_progress",
                    current_phase="execute",
                    next_action=f"Run execute. Address review findings against .dev-kit/sessions/{session_id}/plan.md.",
                    review=f".dev-kit/sessions/{session_id}/review.md",
                    phase_status={"P1": "completed", "P2": "completed"},
                ),
            }

            for name, payload in cases.items():
                with self.subTest(name=name):
                    self.assertEqual(
                        dev_kit_state.validate_state_payload(
                            payload,
                            self.schema,
                            root,
                            session_path=session_dir,
                        ),
                        [],
                    )

    def test_validate_state_payload_rejects_blocked_status(self) -> None:
        payload = approved_plan_state()
        payload["status"] = "blocked"
        errors = dev_kit_state.validate_state_payload(payload, self.schema)
        self.assertIn("state.json status must be one of in_progress, completed", errors)

    def test_validate_state_payload_rejects_failed_status(self) -> None:
        payload = approved_plan_state()
        payload["status"] = "failed"
        errors = dev_kit_state.validate_state_payload(payload, self.schema)
        self.assertIn("state.json status must be one of in_progress, completed", errors)

    def test_validate_state_payload_rejects_invalidated_plan_status(self) -> None:
        payload = approved_plan_state()
        payload["plan_status"] = "invalidated"
        errors = dev_kit_state.validate_state_payload(payload, self.schema)
        self.assertIn(
            "state.json plan_status must be one of not_started, drafting, in_review, revising, approved",
            errors,
        )

    def test_validate_state_payload_rejects_failed_phase_status(self) -> None:
        payload = approved_plan_state()
        payload["phase_status"] = {"P1": "failed"}
        errors = dev_kit_state.validate_state_payload(payload, self.schema)
        self.assertIn("state.json phase_status.P1 must be one of pending, executing, completed", errors)

    def test_validate_state_payload_rejects_artifact_path_escape(self) -> None:
        payload = approved_plan_state()
        payload["artifacts"]["plan"] = "../outside.md"
        with tempfile.TemporaryDirectory() as tmpdir:
            errors = dev_kit_state.validate_state_payload(payload, self.schema, Path(tmpdir))
        self.assertTrue(errors)

    def test_validate_state_payload_rejects_plan_review_from_other_session(self) -> None:
        payload = approved_plan_state()
        payload["artifacts"]["plan_review"] = ".dev-kit/sessions/2026-04-06T16-30-other/plan-review.md"
        with tempfile.TemporaryDirectory() as tmpdir:
            errors = dev_kit_state.validate_state_payload(payload, self.schema, Path(tmpdir))
        self.assertIn(
            "state.json artifacts.plan_review must match .dev-kit/sessions/2026-04-06T16-30-example/plan-review.md",
            errors,
        )

    def test_validate_state_payload_requires_plan_status_approved_for_execute(self) -> None:
        payload = workflow_state(
            current_phase="execute",
            execution_profile="medium",
            plan_status="drafting",
            plan_version=1,
            next_action="Execute draft plan.",
        )
        errors = dev_kit_state.validate_state_payload(payload, self.schema)
        self.assertIn("state.json current_phase execute requires plan_status approved", errors)

    def test_validate_state_payload_requires_not_started_plan_status_for_clarify(self) -> None:
        payload = workflow_state(
            current_phase="clarify",
            execution_profile="medium",
            plan_status="drafting",
            plan_version=1,
            next_action="Draft plan v1.",
            brief=".dev-kit/sessions/2026-04-06T16-30-example/brief.md",
            plan=".dev-kit/sessions/2026-04-06T16-30-example/plan.md",
        )
        errors = dev_kit_state.validate_state_payload(payload, self.schema)
        self.assertIn("state.json current_phase clarify requires plan_status not_started", errors)

    def test_validate_state_payload_rejects_approved_plan_while_still_in_planning(self) -> None:
        payload = approved_plan_state(current_phase="planning")
        errors = dev_kit_state.validate_state_payload(payload, self.schema)
        self.assertIn(
            "state.json current_phase planning requires plan_status not_started, drafting, in_review, or revising",
            errors,
        )

    def test_validate_state_payload_requires_review_artifact_when_completed(self) -> None:
        payload = approved_plan_state(
            status="completed",
            current_phase="review",
            next_action="Session complete.",
            review=None,
            phase_status={"P1": "completed"},
        )
        errors = dev_kit_state.validate_state_payload(payload, self.schema)
        self.assertIn("state.json artifacts.review is required when status is completed", errors)

    def test_validate_state_payload_requires_completed_status_to_stay_in_review(self) -> None:
        payload = approved_plan_state(
            status="completed",
            current_phase="execute",
            next_action="Session complete.",
            review=f".dev-kit/sessions/2026-04-06T16-30-example/review.md",
        )
        errors = dev_kit_state.validate_state_payload(payload, self.schema)
        self.assertIn("state.json status completed requires current_phase review", errors)

    def test_load_active_state_reads_current_pointer(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_session(root, approved_plan_state())
            write_current_pointer(root, "2026-04-06T16-30-example")

            payload, message = dev_kit_state.load_active_state(root)
            self.assertIsNotNone(payload)
            self.assertEqual(message, "")
            self.assertEqual(payload["session_id"], "2026-04-06T16-30-example")

    def test_load_active_state_handles_missing_current_pointer(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            payload, message = dev_kit_state.load_active_state(Path(tmpdir))
            self.assertIsNone(payload)
            self.assertEqual(message, "Dev Kit: no active session")

    def test_load_active_state_handles_corrupt_current_pointer(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            current_path = root / ".dev-kit" / "current.json"
            current_path.parent.mkdir(parents=True, exist_ok=True)
            current_path.write_text("{not-json", encoding="utf-8")

            payload, message = dev_kit_state.load_active_state(root)
            self.assertIsNone(payload)
            self.assertEqual(message, "Dev Kit warning: invalid .dev-kit/current.json")

    def test_load_active_state_handles_missing_session_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_current_pointer(root, "2026-04-06T16-30-missing")

            payload, message = dev_kit_state.load_active_state(root)
            self.assertIsNone(payload)
            self.assertEqual(message, "Dev Kit warning: active session state missing")

    def test_load_active_state_rejects_noncanonical_phase_plan_combination(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_session(root, approved_plan_state(current_phase="planning"))
            write_current_pointer(root, "2026-04-06T16-30-example")

            payload, message = dev_kit_state.load_active_state(root)
            self.assertIsNone(payload)
            self.assertEqual(message, "Dev Kit warning: invalid active session state")

    def test_load_active_state_rejects_pointer_escape(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            current_path = root / ".dev-kit" / "current.json"
            current_path.parent.mkdir(parents=True, exist_ok=True)
            current_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "session_id": "2026-04-06T16-30-escape",
                        "session_path": "../escape",
                        "updated_at": "2026-04-06T16:45:00+09:00",
                    }
                ),
                encoding="utf-8",
            )

            payload, message = dev_kit_state.load_active_state(root)
            self.assertIsNone(payload)
            self.assertEqual(message, "Dev Kit warning: current session path escapes the workspace root")

    def test_load_active_state_rejects_pointer_outside_sessions_store(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            foreign_dir = root / "foreign"
            foreign_dir.mkdir(parents=True, exist_ok=True)
            (foreign_dir / "state.json").write_text(json.dumps(approved_plan_state(), indent=2), encoding="utf-8")
            write_current_pointer(root, "2026-04-06T16-30-example", session_path="foreign")

            payload, message = dev_kit_state.load_active_state(root)
            self.assertIsNone(payload)
            self.assertEqual(message, "Dev Kit warning: current session path must match .dev-kit/sessions/<session-id>")

    def test_load_active_state_rejects_planning_session_without_brief_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            session_id = "2026-04-06T16-30-example"
            payload = workflow_state(
                session_id,
                current_phase="planning",
                execution_profile="medium",
                next_action=f"Run planning. Read .dev-kit/sessions/{session_id}/brief.md.",
            )
            write_session(root, payload)
            write_current_pointer(root, session_id)

            loaded, message = dev_kit_state.load_active_state(root)
            self.assertIsNone(loaded)
            self.assertEqual(message, "Dev Kit warning: invalid active session state")

    def test_load_active_state_rejects_missing_plan_artifact_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            session_id = "2026-04-06T16-30-example"
            payload = approved_plan_state(session_id)
            write_session(root, payload)
            write_current_pointer(root, session_id)

            for relative_path in (
                payload["artifacts"]["brief"],
                payload["artifacts"]["plan"],
                payload["artifacts"]["plan_review"],
            ):
                (root / str(relative_path)).unlink()

            loaded, message = dev_kit_state.load_active_state(root)
            self.assertIsNone(loaded)
            self.assertEqual(message, "Dev Kit warning: invalid active session state")

    def test_load_resumable_state_scans_when_current_pointer_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_session(root, approved_plan_state())

            payload, message = dev_kit_state.load_resumable_state(root)
            self.assertEqual(message, "")
            self.assertIsNotNone(payload)
            self.assertEqual(payload["session_id"], "2026-04-06T16-30-example")

    def test_load_resumable_state_falls_back_when_current_session_completed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_session(
                root,
                approved_plan_state(
                    "2026-04-06T16-30-completed",
                    status="completed",
                    current_phase="review",
                    next_action="Session complete.",
                    review=".dev-kit/sessions/2026-04-06T16-30-completed/review.md",
                ),
            )
            write_session(root, approved_plan_state("2026-04-06T16-40-active"))
            write_current_pointer(root, "2026-04-06T16-30-completed")

            payload, message = dev_kit_state.load_resumable_state(root)
            self.assertEqual(message, "")
            self.assertIsNotNone(payload)
            self.assertEqual(payload["session_id"], "2026-04-06T16-40-active")

    def test_load_resumable_state_ignores_completed_sessions(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_session(
                root,
                approved_plan_state(
                    status="completed",
                    current_phase="review",
                    next_action="Session complete.",
                    review=".dev-kit/sessions/2026-04-06T16-30-example/review.md",
                ),
            )

            payload, message = dev_kit_state.load_resumable_state(root)
            self.assertIsNone(payload)
            self.assertEqual(message, "Dev Kit: no resumable session")

    def test_load_resumable_state_reports_schema_error_when_no_active_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            with mock.patch.object(
                dev_kit_state,
                "load_validated_state_schema",
                return_value=(None, "Dev Kit warning: invalid bundled state schema"),
            ):
                payload, message = dev_kit_state.load_resumable_state(root)

            self.assertIsNone(payload)
            self.assertEqual(message, "Dev Kit warning: invalid bundled state schema")

    def test_load_resumable_state_warns_on_multiple_sessions(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            write_session(root, approved_plan_state("2026-04-06T16-30-one"))
            write_session(root, approved_plan_state("2026-04-06T16-40-two"))

            payload, message = dev_kit_state.load_resumable_state(root)
            self.assertIsNone(payload)
            self.assertEqual(
                message,
                "Dev Kit warning: multiple resumable sessions; set .dev-kit/current.json explicitly",
            )

    def test_command_summary_honors_workspace_root_override(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir) / "repo"
            nested_root = repo_root / "nested"
            subprocess.run(["git", "init", str(repo_root)], check=True, capture_output=True, text=True)
            write_session(nested_root, approved_plan_state())
            write_current_pointer(nested_root, "2026-04-06T16-30-example")
            args = argparse.Namespace(workspace_root=str(nested_root))

            with mock.patch("sys.stdout", new_callable=io.StringIO) as stdout:
                exit_code = dev_kit_state.command_summary(args)

            self.assertEqual(exit_code, 0)
            output = stdout.getvalue()
            self.assertIn("2026-04-06T16-30-example", output)
            self.assertIn("plan=approved/v1", output)

    def test_command_summary_prints_schema_error_when_scan_cannot_validate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            args = argparse.Namespace(workspace_root=tmpdir)

            with mock.patch.object(
                dev_kit_state,
                "load_validated_state_schema",
                return_value=(None, "Dev Kit warning: invalid bundled state schema"),
            ):
                with mock.patch("sys.stdout", new_callable=io.StringIO) as stdout:
                    exit_code = dev_kit_state.command_summary(args)

            self.assertEqual(exit_code, 0)
            self.assertEqual(stdout.getvalue().strip(), "Dev Kit warning: invalid bundled state schema")

    def test_render_summary_uses_compact_format(self) -> None:
        summary = dev_kit_state.render_summary(approved_plan_state())
        self.assertIn("phase=execute", summary)
        self.assertIn("status=in_progress", summary)
        self.assertIn("profile=medium", summary)
        self.assertIn("plan=approved/v1", summary)

    def test_session_start_hook_finds_dev_kit_root_from_nested_non_git_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            nested = root / "packages" / "app"
            nested.mkdir(parents=True, exist_ok=True)
            write_session(root, approved_plan_state())
            write_current_pointer(root, "2026-04-06T16-30-example")

            result = run_hook(
                SESSION_START_HOOK,
                nested,
                {
                    "session_id": "abc123",
                    "transcript_path": "/tmp/transcript.jsonl",
                    "cwd": str(nested),
                    "hook_event_name": "SessionStart",
                    "source": "startup",
                },
            )

            self.assertIn("2026-04-06T16-30-example", result.stdout)
            self.assertIn("plan=approved/v1", result.stdout)

    def test_user_prompt_submit_hook_finds_dev_kit_root_from_nested_non_git_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            nested = root / "packages" / "app"
            nested.mkdir(parents=True, exist_ok=True)
            write_session(root, approved_plan_state())
            write_current_pointer(root, "2026-04-06T16-30-example")

            result = run_hook(
                USER_PROMPT_SUBMIT_HOOK,
                nested,
                {
                    "session_id": "abc123",
                    "transcript_path": "/tmp/transcript.jsonl",
                    "cwd": str(nested),
                    "hook_event_name": "UserPromptSubmit",
                    "prompt": "Continue the task",
                },
            )

            self.assertIn("2026-04-06T16-30-example", result.stdout)
            self.assertIn("plan=approved/v1", result.stdout)

    def test_validate_schema_accepts_bundled_schema(self) -> None:
        self.assertEqual(dev_kit_state.validate_state_schema(self.schema), [])


if __name__ == "__main__":
    unittest.main()
