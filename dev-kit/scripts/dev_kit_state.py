#!/usr/bin/env python3

from __future__ import annotations

import argparse
import contextlib
import json
import os
import re
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
COMPOUND_STATUSES = {"not_started", "extracted", "skipped", None}
LEARNINGS_DIR_NAME = "learnings"
LEARNINGS_INDEX_FILE = "index.json"
LEARNINGS_SCHEMA_VERSION = 1
LEARNING_STATUSES = {"active", "archived"}
LEARNING_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
ARTIFACT_FILENAMES = {
    "brief": "brief.md",
    "plan": "plan.md",
    "plan_review": "plan-review.md",
    "review": "review.md",
    "compound": "compound.md",
}


def nearest_dev_kit_root(start: Path) -> Path | None:
    for candidate in (start, *start.parents):
        candidate_state_root = candidate / STATE_DIR_NAME
        if (candidate_state_root / CURRENT_FILE).is_file():
            return candidate
        if (candidate_state_root / SESSIONS_DIR_NAME).is_dir():
            return candidate
    return None


def resolve_workspace_root(start_dir: Path | None = None) -> Path:
    override = Path.cwd() if start_dir is None else Path(start_dir).expanduser().resolve()
    env_root = os.environ.get("DEV_KIT_STATE_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()

    state_root_candidate = nearest_dev_kit_root(override)
    if state_root_candidate is not None:
        return state_root_candidate.resolve()

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
            payload = load_json(current_path)
        except (OSError, json.JSONDecodeError):
            return False
        if payload.get("session_id") != expected_session_id:
            return False
        try:
            current_path.unlink()
        except FileNotFoundError:
            return False
        return True


def normalize_relative_path(path_value: str) -> Path:
    return Path(path_value)


def resolve_workspace_relative_path(workspace_root: Path, path_value: str) -> Path:
    if not isinstance(path_value, str) or not path_value:
        raise RuntimeError("write-json path must be a non-empty relative path")

    relative_path = Path(path_value)
    if relative_path.is_absolute():
        raise RuntimeError("write-json path must be relative to the workspace root")

    root = workspace_root.resolve()
    resolved = (root / relative_path).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise RuntimeError("write-json path must stay within the workspace root") from exc

    dev_kit_root = state_root(workspace_root).resolve()
    try:
        resolved.relative_to(dev_kit_root)
    except ValueError as exc:
        raise RuntimeError("write-json path must stay within .dev-kit") from exc

    return resolved


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
    if set(artifacts.get("required", [])) != {"brief", "plan", "plan_review", "review", "compound"}:
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

    compound_status_enum = properties.get("compound_status", {}).get("enum", [])
    compound_status = payload.get("compound_status")
    if compound_status not in compound_status_enum:
        errors.append("state.json compound_status must be not_started, extracted, skipped, or null")

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
        if compound_status == "extracted" and artifacts.get("compound") is None:
            errors.append("state.json artifacts.compound is required when compound_status is extracted")

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
    compound = payload.get("compound_status") or "none"
    return (
        "Dev Kit: "
        f"{payload['session_id']} | "
        f"phase={payload['current_phase']} | "
        f"status={payload['status']} | "
        f"next={payload['next_action']} | "
        f"profile={profile} | "
        f"plan={payload['plan_status']}/v{payload['plan_version']} | "
        f"compound={compound}"
    )


# ── Learnings helpers ──


def learnings_root(workspace_root: Path) -> Path:
    return state_root(workspace_root) / LEARNINGS_DIR_NAME


def learnings_index_path(workspace_root: Path) -> Path:
    return learnings_root(workspace_root) / LEARNINGS_INDEX_FILE


def load_learnings_index(workspace_root: Path) -> dict[str, Any]:
    index_path = learnings_index_path(workspace_root)
    if not index_path.exists():
        return {"schema_version": LEARNINGS_SCHEMA_VERSION, "learnings": []}
    try:
        return load_json(index_path)
    except (OSError, json.JSONDecodeError):
        return {"schema_version": LEARNINGS_SCHEMA_VERSION, "learnings": []}


def save_learnings_index(workspace_root: Path, index: dict[str, Any]) -> None:
    path = learnings_index_path(workspace_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json_atomically(index, path)


def find_relevant_learnings(
    workspace_root: Path,
    *,
    tags: list[str] | None = None,
    context_types: list[str] | None = None,
    max_results: int = 5,
) -> list[dict[str, Any]]:
    """Search active learnings by tag and context overlap, ranked by relevance."""
    index = load_learnings_index(workspace_root)
    active = [l for l in index.get("learnings", []) if l.get("status") == "active"]

    if not tags and not context_types:
        # No filter: return most-referenced active learnings
        active.sort(key=lambda l: (-l.get("reference_count", 0), l.get("created_at", "")))
        return active[:max_results]

    query_tags = set(t.lower() for t in (tags or []))
    query_ctx = set(c.lower() for c in (context_types or []))

    scored: list[tuple[float, dict[str, Any]]] = []
    for entry in active:
        entry_tags = set(t.lower() for t in entry.get("tags", []))
        entry_ctx = set(c.lower() for c in entry.get("context_types", []))

        tag_overlap = len(query_tags & entry_tags)
        ctx_overlap = len(query_ctx & entry_ctx)
        score = tag_overlap * 2.0 + ctx_overlap * 1.5 + entry.get("reference_count", 0) * 0.1

        if tag_overlap > 0 or ctx_overlap > 0:
            scored.append((score, entry))

    scored.sort(key=lambda pair: -pair[0])
    return [entry for _, entry in scored[:max_results]]


def render_learnings_summary(workspace_root: Path, max_results: int = 5) -> str:
    """Render a compact text summary of available learnings for hook injection."""
    index = load_learnings_index(workspace_root)
    active = [l for l in index.get("learnings", []) if l.get("status") == "active"]

    if not active:
        return ""

    active.sort(key=lambda l: (-l.get("reference_count", 0), l.get("created_at", "")))
    top = active[:max_results]

    lines = [f"Compound Learnings ({len(active)} active):"]
    for entry in top:
        tags_str = ", ".join(entry.get("tags", [])[:4])
        refs = entry.get("reference_count", 0)
        lines.append(f"  - [{entry['id']}] {entry['title']} (tags: {tags_str}) (refs: {refs})")

    if len(active) > max_results:
        lines.append(f"  ... and {len(active) - max_results} more")

    return "\n".join(lines)


def _validate_learning_id(learning_id: str) -> str:
    if not isinstance(learning_id, str) or not learning_id:
        raise ValueError("learning_id must be a non-empty lowercase hyphenated identifier")
    if not LEARNING_ID_PATTERN.fullmatch(learning_id):
        raise ValueError("learning_id must match ^[a-z0-9]+(?:-[a-z0-9]+)*$")
    return learning_id


def add_learning(
    workspace_root: Path,
    *,
    learning_id: str,
    title: str,
    source_session: str,
    tags: list[str],
    context_types: list[str],
    content: str,
    created_at: str,
) -> None:
    """Add a new learning entry: write the .md file and update index.json."""
    lr = learnings_root(workspace_root)
    lr.mkdir(parents=True, exist_ok=True)

    validated_learning_id = _validate_learning_id(learning_id)
    md_filename = f"{validated_learning_id}.md"
    md_path = lr / md_filename
    md_path.write_text(content, encoding="utf-8")

    index = load_learnings_index(workspace_root)
    existing = next((l for l in index["learnings"] if l.get("id") == validated_learning_id), None)
    index["learnings"] = [l for l in index["learnings"] if l.get("id") != validated_learning_id]
    index["learnings"].append({
        "id": validated_learning_id,
        "title": title,
        "source_session": source_session,
        "tags": tags,
        "context_types": context_types,
        "file": md_filename,
        "created_at": created_at,
        "last_referenced_at": existing.get("last_referenced_at") if existing else None,
        "reference_count": existing.get("reference_count", 0) if existing else 0,
        "status": existing.get("status", "active") if existing else "active",
    })
    save_learnings_index(workspace_root, index)


def archive_learning(workspace_root: Path, learning_id: str) -> bool:
    """Mark a learning as archived. Returns True if found and updated."""
    index = load_learnings_index(workspace_root)
    for entry in index.get("learnings", []):
        if entry.get("id") == learning_id:
            entry["status"] = "archived"
            save_learnings_index(workspace_root, index)
            return True
    return False


def bump_learning_reference(workspace_root: Path, learning_id: str, referenced_at: str) -> bool:
    """Increment reference_count and update last_referenced_at. Returns True if found."""
    index = load_learnings_index(workspace_root)
    for entry in index.get("learnings", []):
        if entry.get("id") == learning_id:
            entry["reference_count"] = entry.get("reference_count", 0) + 1
            entry["last_referenced_at"] = referenced_at
            save_learnings_index(workspace_root, index)
            return True
    return False


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

    root = Path(args.workspace_root).resolve()
    try:
        path = resolve_workspace_relative_path(root, args.path)
        write_json_atomically(payload, path)
    except RuntimeError as exc:
        print(f"Dev Kit warning: {exc}")
        return 1
    return 0


def command_resolve_workspace_root(args: argparse.Namespace) -> int:
    start_dir: Path | None = None
    if args.cwd:
        start_dir = Path(args.cwd)
    else:
        raw = sys.stdin.read()
        if raw.strip():
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = None
            if isinstance(payload, dict):
                cwd = payload.get("cwd")
                if isinstance(cwd, str) and cwd:
                    start_dir = Path(cwd)
    if start_dir is None:
        print("Dev Kit error: resolve-workspace-root requires --cwd or stdin json with cwd")
        return 1
    print(resolve_workspace_root(start_dir))
    return 0


def command_learnings_summary(args: argparse.Namespace) -> int:
    root = Path(args.workspace_root).resolve() if args.workspace_root else resolve_workspace_root()
    max_results = args.max_results if hasattr(args, "max_results") and args.max_results else 5
    summary = render_learnings_summary(root, max_results=max_results)
    if summary:
        print(summary)
    return 0


def command_bump_learning(args: argparse.Namespace) -> int:
    root = Path(args.workspace_root).resolve() if args.workspace_root else resolve_workspace_root()
    from datetime import datetime, timezone

    referenced_at = datetime.now(timezone.utc).isoformat()
    if not bump_learning_reference(root, args.learning_id, referenced_at):
        print(f"Dev Kit warning: learning '{args.learning_id}' not found")
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

    resolve_root_parser = subparsers.add_parser("resolve-workspace-root", help="Resolve the preferred workspace root")
    resolve_root_parser.add_argument("--cwd", help="Starting cwd to resolve from")
    resolve_root_parser.set_defaults(func=command_resolve_workspace_root)

    write_json_parser = subparsers.add_parser("write-json", help="Atomically write JSON payload to a file")
    write_json_parser.add_argument("--workspace-root", required=True, help="Workspace root used for path validation")
    write_json_parser.add_argument("--path", required=True, help="Target path for atomic JSON write")
    write_json_parser.set_defaults(func=command_write_json)

    learnings_parser = subparsers.add_parser("learnings-summary", help="Print compound learnings summary")
    learnings_parser.add_argument("--workspace-root", help="Override workspace root resolution")
    learnings_parser.add_argument("--max-results", type=int, default=5, help="Max learnings to show")
    learnings_parser.set_defaults(func=command_learnings_summary)

    bump_learning_parser = subparsers.add_parser("bump-learning", help="Increment reference count for a learning")
    bump_learning_parser.add_argument("--workspace-root", help="Override workspace root resolution")
    bump_learning_parser.add_argument("--learning-id", required=True, help="Learning ID to bump")
    bump_learning_parser.set_defaults(func=command_bump_learning)

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
