#!/usr/bin/env python3

from __future__ import annotations

import argparse
import contextlib
import json
import os
import sys
import tempfile
import subprocess
import time
from pathlib import Path
from typing import Any

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows compatibility
    fcntl = None

STATE_DIR_NAME = ".dev-kit"
SESSIONS_DIR_NAME = "sessions"
CURRENT_FILE = "current.json"
STATE_FILE = "state.json"
STATE_LOCK_SUFFIX = ".lock"
STATE_SCHEMA_VERSION = 1
STATE_STATUSES = {"in_progress", "completed", "failed", "paused"}
RESUMABLE_STATUSES = {"in_progress", "paused"}
PHASES = {"clarify", "planning", "execute", "review-execute"}
PROFILES = {"low", "medium", "high", None}
PLAN_STATUSES = {"not_started", "drafting", "in_review", "revising", "approved"}
PHASE_STATUSES = {"pending", "executing", "completed"}
ARTIFACT_FILENAMES = {
    "brief": "brief.md",
    "plan": "plan.md",
    "plan_review": "plan-review.md",
    "review": "review.md",
}


def resolve_workspace_root(start_dir: Path | None = None) -> Path:
    override = Path.cwd() if start_dir is None else Path(start_dir).resolve()
    env_root = os.environ.get("DEV_KIT_STATE_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=str(override),
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return override

    root = result.stdout.strip()
    if not root:
        return override
    return Path(root).resolve()


def plugin_root() -> Path:
    return Path(__file__).resolve().parent.parent


def state_root(workspace_root: Path) -> Path:
    return workspace_root / STATE_DIR_NAME


def sessions_root(workspace_root: Path) -> Path:
    return state_root(workspace_root) / SESSIONS_DIR_NAME


def session_relative_path(session_id: str) -> Path:
    return Path(STATE_DIR_NAME) / SESSIONS_DIR_NAME / session_id


def artifact_relative_path(session_id: str, artifact_name: str) -> Path:
    filename = ARTIFACT_FILENAMES.get(artifact_name, f"{artifact_name}.md")
    return session_relative_path(session_id) / filename


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


@contextlib.contextmanager
def _acquire_lock(lock_path: Path, *, attempts: int = 60, delay_seconds: float = 0.05):
    lock_path = lock_path.resolve()
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "a", encoding="utf-8") as lock_handle:
        fd = lock_handle.fileno()
        if fcntl is None:
            yield
            return

        for _ in range(max(1, attempts)):
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                time.sleep(delay_seconds)
        else:
            raise RuntimeError(f"timeout while waiting for lock: {lock_path}")

        try:
            yield
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)


def write_json_atomically(payload: Any, path: Path) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = path.with_name(path.name + STATE_LOCK_SUFFIX)
    with _acquire_lock(lock_path):
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=str(path.parent),
            prefix=f".{path.name}.tmp.",
            delete=False,
        ) as tmp:
            json.dump(payload, tmp, indent=2)
            tmp.flush()
            os.fsync(tmp.fileno())
            tmp_path = Path(tmp.name)
        os.replace(tmp_path, path)


def write_current_pointer_atomically(
    workspace_root: Path,
    *,
    session_id: str,
    session_path: str,
    updated_at: str,
) -> None:
    payload = {
        "schema_version": STATE_SCHEMA_VERSION,
        "session_id": session_id,
        "session_path": session_path,
        "updated_at": updated_at,
    }
    write_json_atomically(payload, state_root(workspace_root) / CURRENT_FILE)


def clear_current_pointer_if_matches(workspace_root: Path, expected_session_id: str) -> bool:
    current_path = state_root(workspace_root) / CURRENT_FILE
    if not current_path.exists():
        return False

    try:
        payload = load_json(current_path)
    except (OSError, json.JSONDecodeError):
        return False
    if payload.get("session_id") != expected_session_id:
        return False

    lock_path = current_path.with_name(current_path.name + STATE_LOCK_SUFFIX)
    with _acquire_lock(lock_path):
        try:
            current_path.unlink()
        except FileNotFoundError:
            return False
        return True


def normalize_relative_path(path_value: str) -> Path:
    return Path(path_value)


def is_relative_to_workspace(path_value: str, workspace_root: Path) -> bool:
    try:
        (workspace_root / normalize_relative_path(path_value)).resolve().relative_to(workspace_root.resolve())
        return True
    except ValueError:
        return False


def relative_path_string(path_value: Any) -> bool:
    if path_value is None:
        return True
    if not isinstance(path_value, str) or not path_value:
        return False
    return not Path(path_value).is_absolute()


def validate_current_payload(payload: Any) -> list[str]:
    if not isinstance(payload, dict):
        return ["current.json must be an object"]

    expected_keys = {"schema_version", "session_id", "session_path", "updated_at"}
    actual_keys = set(payload.keys())
    errors: list[str] = []

    missing = expected_keys - actual_keys
    extra = actual_keys - expected_keys
    if missing:
        errors.append(f"current.json missing keys: {sorted(missing)}")
    if extra:
        errors.append(f"current.json has unexpected keys: {sorted(extra)}")

    if payload.get("schema_version") != STATE_SCHEMA_VERSION:
        errors.append("current.json schema_version must be 1")
    if not isinstance(payload.get("session_id"), str) or not payload.get("session_id"):
        errors.append("current.json session_id must be a non-empty string")
    session_path = payload.get("session_path")
    if not isinstance(session_path, str) or not session_path:
        errors.append("current.json session_path must be a non-empty string")
    elif Path(session_path).is_absolute():
        errors.append("current.json session_path must be relative to the workspace root")
    if not isinstance(payload.get("updated_at"), str) or not payload.get("updated_at"):
        errors.append("current.json updated_at must be a non-empty string")

    return errors


def load_state_schema() -> dict[str, Any]:
    schema = load_json(plugin_root() / "schema" / "state.schema.json")
    if not isinstance(schema, dict):
        raise ValueError("Bundled state schema must be an object")
    return schema


def validate_state_schema(schema: Any) -> list[str]:
    if not isinstance(schema, dict):
        return ["Bundled state schema must be an object"]

    required_top_level = {
        "schema_version",
        "session_id",
        "title",
        "feature_slug",
        "status",
        "current_phase",
        "execution_profile",
        "plan_status",
        "plan_version",
        "next_action",
        "artifacts",
        "phase_status",
        "created_at",
        "updated_at",
    }
    errors: list[str] = []
    if schema.get("title") != "Dev Kit Session State":
        errors.append("Bundled state schema title must be 'Dev Kit Session State'")

    properties = schema.get("properties")
    if not isinstance(properties, dict):
        errors.append("Bundled state schema properties must be an object")
        return errors

    required = set(schema.get("required", []))
    if required != required_top_level:
        errors.append("Bundled state schema required fields do not match the canonical state model")

    if set(properties.get("status", {}).get("enum") or []) != {
        "in_progress",
        "completed",
        "failed",
        "paused",
    }:
        errors.append("Bundled state schema status enum is invalid")
    failure_reason_schema = properties.get("failure_reason")
    if failure_reason_schema is None:
        errors.append("Bundled state schema is missing failure_reason")
    else:
        failure_reason_types = set(failure_reason_schema.get("type", []))
        if set(failure_reason_types) != {"string", "null"} and failure_reason_types != {"null"}:
            errors.append("Bundled state schema failure_reason type is invalid")
    if properties.get("current_phase", {}).get("enum") != ["clarify", "planning", "execute", "review-execute"]:
        errors.append("Bundled state schema current_phase enum is invalid")
    if properties.get("execution_profile", {}).get("enum") != ["low", "medium", "high", None]:
        errors.append("Bundled state schema execution_profile enum is invalid")
    if properties.get("plan_status", {}).get("enum") != [
        "not_started",
        "drafting",
        "in_review",
        "revising",
        "approved",
    ]:
        errors.append("Bundled state schema plan_status enum is invalid")
    if properties.get("plan_version", {}).get("minimum") != 0:
        errors.append("Bundled state schema plan_version minimum is invalid")

    artifacts = properties.get("artifacts", {})
    if set(artifacts.get("required", [])) != {"brief", "plan", "plan_review", "review"}:
        errors.append("Bundled state schema artifacts required keys are invalid")

    phase_status = properties.get("phase_status", {})
    additional = phase_status.get("additionalProperties", {})
    if additional.get("enum") != ["pending", "executing", "completed"]:
        errors.append("Bundled state schema phase_status enum is invalid")

    return errors


def validate_state_payload(
    payload: Any,
    schema: dict[str, Any],
    workspace_root: Path | None = None,
    session_path: Path | None = None,
) -> list[str]:
    if not isinstance(payload, dict):
        return ["state.json must be an object"]

    properties = schema.get("properties", {})
    required_keys = set(schema.get("required", []))
    allowed_keys = set(properties.keys())
    errors: list[str] = []
    extra = set(payload.keys()) - allowed_keys
    missing = required_keys - set(payload.keys())
    if missing:
        errors.append(f"state.json missing keys: {sorted(missing)}")
    if extra:
        errors.append(f"state.json has unexpected keys: {sorted(extra)}")

    if payload.get("schema_version") != STATE_SCHEMA_VERSION:
        errors.append("state.json schema_version must be 1")

    session_id = payload.get("session_id")
    if not isinstance(session_id, str) or not session_id:
        errors.append("state.json session_id must be a non-empty string")
    if not isinstance(payload.get("title"), str) or not payload.get("title"):
        errors.append("state.json title must be a non-empty string")
    if not isinstance(payload.get("feature_slug"), str) or not payload.get("feature_slug"):
        errors.append("state.json feature_slug must be a non-empty string")

    status_enum = properties.get("status", {}).get("enum", [])
    status = payload.get("status")
    if status not in status_enum:
        errors.append("state.json status must be one of in_progress, completed, failed, paused")

    current_phase_enum = properties.get("current_phase", {}).get("enum", [])
    current_phase = payload.get("current_phase")
    if current_phase not in current_phase_enum:
        errors.append("state.json current_phase must be one of clarify, planning, execute, review-execute")

    execution_profile_enum = properties.get("execution_profile", {}).get("enum", [])
    if payload.get("execution_profile") not in execution_profile_enum:
        errors.append("state.json execution_profile must be low, medium, high, or null")

    plan_status_enum = properties.get("plan_status", {}).get("enum", [])
    plan_status = payload.get("plan_status")
    if plan_status not in plan_status_enum:
        errors.append("state.json plan_status must be one of not_started, drafting, in_review, revising, approved")

    plan_version = payload.get("plan_version")
    if not isinstance(plan_version, int) or isinstance(plan_version, bool) or plan_version < 0:
        errors.append("state.json plan_version must be an integer greater than or equal to 0")

    if not isinstance(payload.get("next_action"), str) or not payload.get("next_action"):
        errors.append("state.json next_action must be a non-empty string")

    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, dict):
        errors.append("state.json artifacts must be an object")
    else:
        artifact_properties = properties.get("artifacts", {}).get("properties", {})
        expected_artifacts = set(properties.get("artifacts", {}).get("required", [])) or set(artifact_properties.keys())
        missing_artifacts = expected_artifacts - set(artifacts.keys())
        extra_artifacts = set(artifacts.keys()) - expected_artifacts
        if missing_artifacts:
            errors.append(f"state.json artifacts missing keys: {sorted(missing_artifacts)}")
        if extra_artifacts:
            errors.append(f"state.json artifacts has unexpected keys: {sorted(extra_artifacts)}")
        for key in expected_artifacts:
            if key in artifacts and not relative_path_string(artifacts[key]):
                errors.append(f"state.json artifacts.{key} must be null or a relative path string")
            if workspace_root is not None and key in artifacts and isinstance(artifacts[key], str):
                if not is_relative_to_workspace(artifacts[key], workspace_root):
                    errors.append(f"state.json artifacts.{key} must stay within the workspace root")
                elif isinstance(session_id, str) and session_id:
                    expected_artifact_path = artifact_relative_path(session_id, key)
                    if normalize_relative_path(artifacts[key]) != expected_artifact_path:
                        errors.append(
                            f"state.json artifacts.{key} must match {expected_artifact_path.as_posix()}"
                        )

    phase_status = payload.get("phase_status")
    if not isinstance(phase_status, dict):
        errors.append("state.json phase_status must be an object")
    else:
        phase_status_enum = properties.get("phase_status", {}).get("additionalProperties", {}).get("enum", [])
        for key, value in phase_status.items():
            if not isinstance(key, str) or not key:
                errors.append("state.json phase_status keys must be non-empty strings")
            if value not in phase_status_enum:
                errors.append(
                    f"state.json phase_status.{key} must be one of pending, executing, completed"
                )

    for key in ("created_at", "updated_at"):
        if not isinstance(payload.get(key), str) or not payload.get(key):
            errors.append(f"state.json {key} must be a non-empty string")

    failure_reason = payload.get("failure_reason")
    if status in {"failed", "paused"}:
        if not isinstance(failure_reason, str) or not failure_reason.strip():
            errors.append("state.json failure_reason is required when status is failed or paused")
    elif failure_reason is not None:
        errors.append("state.json failure_reason must be null when status is not failed or paused")

    if workspace_root is not None and session_path is not None and isinstance(session_id, str) and session_id:
        expected_session_path = (workspace_root / session_relative_path(session_id)).resolve()
        if session_path.resolve() != expected_session_path:
            errors.append("state.json must live at .dev-kit/sessions/<session-id>/state.json")

    if isinstance(plan_version, int) and not isinstance(plan_version, bool):
        if plan_status == "not_started" and plan_version != 0:
            errors.append("state.json plan_version must be 0 when plan_status is not_started")
        if plan_status in PLAN_STATUSES - {"not_started"} and plan_version < 1:
            errors.append("state.json plan_version must be at least 1 after planning begins")

    if current_phase == "clarify" and plan_status != "not_started":
        errors.append("state.json current_phase clarify requires plan_status not_started")
    if current_phase == "planning" and plan_status not in PLAN_STATUSES - {"approved"}:
        errors.append(
            "state.json current_phase planning requires plan_status not_started, drafting, in_review, or revising"
        )
    if current_phase == "execute" and plan_status != "approved":
        errors.append("state.json current_phase execute requires plan_status approved")
    if current_phase == "review-execute" and plan_status != "approved":
        errors.append("state.json current_phase review-execute requires plan_status approved")

    if status == "completed":
        if current_phase != "review-execute":
            errors.append("state.json status completed requires current_phase review-execute")
        if plan_status != "approved":
            errors.append("state.json status completed requires plan_status approved")
        if isinstance(artifacts, dict) and artifacts.get("review") is None:
            errors.append("state.json artifacts.review is required when status is completed")
        if failure_reason is not None:
            errors.append("state.json failure_reason must be null when status is completed")

    if isinstance(artifacts, dict) and plan_status == "approved":
        if artifacts.get("plan") is None:
            errors.append("state.json artifacts.plan is required when plan_status is approved")
        if artifacts.get("plan_review") is None:
            errors.append("state.json artifacts.plan_review is required when plan_status is approved")

    if status == "completed":
        if not phase_status:
            errors.append("state.json phase_status must not be empty when status is completed")
        elif any(value != "completed" for value in phase_status.values()):
            errors.append("state.json phase_status must all be completed when status is completed")

    if current_phase in {"execute", "review-execute"} and not phase_status:
        errors.append(
            "state.json phase_status must include at least one phase when current_phase is execute or review-execute"
        )

    return errors


def validate_materialized_artifacts(payload: Any, workspace_root: Path) -> list[str]:
    if not isinstance(payload, dict):
        return []

    artifacts = payload.get("artifacts")
    if not isinstance(artifacts, dict):
        return []

    current_phase = payload.get("current_phase")
    plan_status = payload.get("plan_status")
    status = payload.get("status")
    errors: list[str] = []
    required_artifacts: set[str] = set()

    if current_phase in {"planning", "execute", "review-execute"}:
        required_artifacts.add("brief")
    if plan_status == "approved":
        required_artifacts.update({"plan", "plan_review"})
    if status == "completed":
        required_artifacts.add("review")

    for key in required_artifacts:
        path_value = artifacts.get(key)
        if path_value is None:
            errors.append(f"state.json artifacts.{key} is required for the current workflow phase")
            continue
        if not isinstance(path_value, str):
            continue
        artifact_path = (workspace_root / normalize_relative_path(path_value)).resolve()
        if not artifact_path.is_file():
            errors.append(f"state.json artifacts.{key} points to a missing file")

    for key, path_value in artifacts.items():
        if key in required_artifacts or not isinstance(path_value, str):
            continue
        artifact_path = (workspace_root / normalize_relative_path(path_value)).resolve()
        if not artifact_path.is_file():
            errors.append(f"state.json artifacts.{key} points to a missing file")

    return errors


def read_current_pointer(workspace_root: Path) -> tuple[dict[str, Any] | None, str | None]:
    current_path = state_root(workspace_root) / CURRENT_FILE
    if not current_path.exists():
        return None, "Dev Kit: no active session"

    try:
        payload = load_json(current_path)
    except (OSError, json.JSONDecodeError):
        return None, "Dev Kit warning: invalid .dev-kit/current.json"

    errors = validate_current_payload(payload)
    if errors:
        return None, "Dev Kit warning: invalid .dev-kit/current.json"
    return payload, None


def load_validated_state_schema() -> tuple[dict[str, Any] | None, str | None]:
    try:
        schema = load_state_schema()
    except (OSError, json.JSONDecodeError, ValueError):
        return None, "Dev Kit warning: invalid bundled state schema"

    schema_errors = validate_state_schema(schema)
    if schema_errors:
        return None, "Dev Kit warning: invalid bundled state schema"
    return schema, None


def load_state_at_session_path(
    session_path: Path,
    schema: dict[str, Any],
    workspace_root: Path,
) -> tuple[dict[str, Any] | None, str | None]:
    state_path = session_path / STATE_FILE
    if not state_path.exists():
        return None, "Dev Kit warning: active session state missing"

    try:
        payload = load_json(state_path)
    except (OSError, json.JSONDecodeError):
        return None, "Dev Kit warning: invalid active session state"

    errors = validate_state_payload(payload, schema, workspace_root, session_path=session_path)
    if not errors:
        errors.extend(validate_materialized_artifacts(payload, workspace_root))
    if errors:
        return None, "Dev Kit warning: invalid active session state"
    return payload, None


def load_active_state(workspace_root: Path) -> tuple[dict[str, Any] | None, str]:
    current_payload, warning = read_current_pointer(workspace_root)
    if current_payload is None:
        return None, warning or "Dev Kit: no active session"

    session_path_value = current_payload["session_path"]
    if not is_relative_to_workspace(session_path_value, workspace_root):
        return None, "Dev Kit warning: current session path escapes the workspace root"
    if normalize_relative_path(session_path_value) != session_relative_path(current_payload["session_id"]):
        return None, "Dev Kit warning: current session path must match .dev-kit/sessions/<session-id>"

    session_path = (workspace_root / session_path_value).resolve()
    schema, schema_warning = load_validated_state_schema()
    if schema is None:
        return None, schema_warning or "Dev Kit warning: invalid bundled state schema"

    payload, payload_warning = load_state_at_session_path(session_path, schema, workspace_root)
    if payload is None:
        return None, payload_warning or "Dev Kit warning: invalid active session state"
    if payload["session_id"] != current_payload["session_id"]:
        return None, "Dev Kit warning: current session pointer does not match state.json"
    return payload, ""


def scan_resumable_states(workspace_root: Path) -> tuple[list[dict[str, Any]], str | None]:
    schema, schema_warning = load_validated_state_schema()
    if schema is None:
        return [], schema_warning or "Dev Kit warning: invalid bundled state schema"

    discovered: list[dict[str, Any]] = []
    session_store = sessions_root(workspace_root)
    if not session_store.is_dir():
        return discovered, None

    for session_dir in sorted(path for path in session_store.iterdir() if path.is_dir()):
        payload, _ = load_state_at_session_path(session_dir.resolve(), schema, workspace_root)
        if payload is None:
            continue
        if payload.get("status") in RESUMABLE_STATUSES:
            discovered.append(payload)

    return (
        sorted(
            discovered,
            key=lambda item: (str(item.get("updated_at", "")), str(item.get("session_id", ""))),
            reverse=True,
        ),
        None,
    )


def load_resumable_state(workspace_root: Path) -> tuple[dict[str, Any] | None, str]:
    active_payload, active_message = load_active_state(workspace_root)
    if active_payload is not None and active_payload["status"] in RESUMABLE_STATUSES:
        return active_payload, ""

    discovered, scan_warning = scan_resumable_states(workspace_root)
    if active_payload is not None:
        discovered = [payload for payload in discovered if payload["session_id"] != active_payload["session_id"]]

    if len(discovered) == 1:
        return discovered[0], ""
    if len(discovered) > 1:
        return None, "Dev Kit warning: multiple resumable sessions; set .dev-kit/current.json explicitly"
    if active_payload is None and active_message and active_message != "Dev Kit: no active session":
        return None, active_message
    if scan_warning:
        return None, scan_warning
    return None, "Dev Kit: no resumable session"


def render_summary(payload: dict[str, Any]) -> str:
    profile = payload["execution_profile"] or "unset"
    return (
        "Dev Kit: "
        f"{payload['session_id']} | "
        f"phase={payload['current_phase']} | "
        f"status={payload['status']} | "
        f"next={payload['next_action']} | "
        f"profile={profile} | "
        f"plan={payload['plan_status']}/v{payload['plan_version']}"
    )


def command_summary(args: argparse.Namespace) -> int:
    root = Path(args.workspace_root).resolve() if args.workspace_root else resolve_workspace_root()
    payload, message = load_resumable_state(root)
    if payload is None:
        print(message)
        return 0

    print(render_summary(payload))
    return 0


def command_validate_schema(_: argparse.Namespace) -> int:
    try:
        schema = load_state_schema()
    except (OSError, json.JSONDecodeError, ValueError):
        print("Dev Kit warning: invalid bundled state schema")
        return 1
    errors = validate_state_schema(schema)
    if errors:
        print("Dev Kit warning: invalid bundled state schema")
        return 1
    print("Dev Kit: bundled state schema OK")
    return 0


def command_write_json(args: argparse.Namespace) -> int:
    data = sys.stdin.read()
    if not data.strip():
        print("Dev Kit error: no json payload provided")
        return 1

    try:
        payload = json.loads(data)
    except json.JSONDecodeError:
        print("Dev Kit error: invalid json payload")
        return 1

    try:
        write_json_atomically(payload, Path(args.path))
    except RuntimeError as exc:
        print(f"Dev Kit warning: {exc}")
        return 1
    return 0


def command_clear_current(args: argparse.Namespace) -> int:
    root = Path(args.workspace_root).resolve() if args.workspace_root else resolve_workspace_root()
    expected_session_id = args.session_id
    if expected_session_id is None:
        return 0

    removed = clear_current_pointer_if_matches(root, expected_session_id)
    if not removed:
        print("Dev Kit warning: current.json pointer did not match target session_id")
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Dev Kit state helpers")
    subparsers = parser.add_subparsers(dest="command", required=True)

    summary_parser = subparsers.add_parser("summary", help="Print the preferred resumable session summary")
    summary_parser.add_argument("--workspace-root", help="Override workspace root resolution")
    summary_parser.set_defaults(func=command_summary)

    schema_parser = subparsers.add_parser("validate-schema", help="Validate the bundled schema")
    schema_parser.set_defaults(func=command_validate_schema)

    write_json_parser = subparsers.add_parser("write-json", help="Atomically write JSON payload to a file")
    write_json_parser.add_argument("--path", required=True, help="Target path for atomic JSON write")
    write_json_parser.set_defaults(func=command_write_json)

    clear_current_parser = subparsers.add_parser("clear-current", help="Remove current.json only when it points to target session")
    clear_current_parser.add_argument("--workspace-root", help="Override workspace root resolution")
    clear_current_parser.add_argument("--session-id", required=True, help="Only clear if pointer session_id matches")
    clear_current_parser.set_defaults(func=command_clear_current)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
