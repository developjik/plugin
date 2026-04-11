#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STATE_DIR = ".harness-design-kit"
ARTIFACT_SCHEMA_BY_FILENAME = {
    "product-spec.md": "product-spec.schema.json",
    "design-brief.md": "design-brief.schema.json",
    "sprint-contract.md": "sprint-contract.schema.json",
    "evaluation.md": "evaluation.schema.json",
    "progress.md": "progress.schema.json",
    "compact-state.md": "compact-state.schema.json",
    "handoff.md": "handoff.schema.json",
}
FALLBACK_TITLES = {
    "product-spec.md": "Product Spec",
    "design-brief.md": "Design Brief",
    "sprint-contract.md": "Sprint Contract",
    "evaluation.md": "Evaluation",
    "progress.md": "Progress",
    "compact-state.md": "Compact State",
    "handoff.md": "Handoff",
}
APP_EVALUATION_CRITERIA = (
    "product depth",
    "functionality",
    "visual design",
    "code quality",
)
FRONTEND_EVALUATION_CRITERIA = (
    "design quality",
    "originality",
    "craft",
    "functionality",
)
FRONTEND_PRIORITY_CRITERIA = (
    "design quality",
    "originality",
)
FRONTEND_SUPPORTING_CRITERIA = (
    "craft",
    "functionality",
)
PLACEHOLDER_VALUES = {
    "criterion",
    "score",
    "threshold",
    "weight",
    "finding 1",
    "evidence 1",
    "artifact 1",
    "step 1",
    "deliverable 1",
    "deliverable 2",
    "out of scope item 1",
    "test 1",
    "test 2",
    "verification 1",
    "verification 2",
    "criterion 1",
    "criterion 2",
    "risk 1",
    "risk 2",
    "change 1",
    "change 2",
    "result 1",
    "candidate 1",
    "candidate 2",
    "goal",
    "reason",
    "status",
    "summary goes here.",
    "contract summary goes here.",
    "completed work goes here.",
    "open issue goes here.",
    "reason goes here.",
    "next step 1",
}
NUMERIC_RE = re.compile(r"-?\d+(?:\.\d+)?")
STATE_FIELD_DEFAULTS = {
    "needs_evaluation": False,
    "final_pass_requested": False,
    "last_live_eval_artifact": "",
    "qa_target_url": "",
    "limitations": [],
    "parent_session_id": None,
    "resumed_from_handoff": False,
    "last_evaluation_scores": [],
    "last_evaluation_weighted_average": None,
    "last_evaluation_weighted_threshold": None,
    "last_evaluation_priority_criteria": [],
    "last_evaluation_decision_basis": "",
    "last_evaluation_threshold_misses": [],
    "last_evaluation_artifacts": [],
    "last_evaluation_recommendation": "",
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
    "round_budget": 1,
    "candidates": [],
}


class ValidationError(RuntimeError):
    pass


def plugin_root() -> Path:
    return Path(__file__).resolve().parent.parent


def schema_root() -> Path:
    return plugin_root() / "schema"


def templates_root() -> Path:
    return plugin_root() / "templates"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def resolve_workspace_root() -> Path:
    configured = os.environ.get("HARNESS_DESIGN_KIT_STATE_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    current = Path.cwd().resolve()
    for candidate in (current, *current.parents):
        if (candidate / STATE_DIR).exists():
            return candidate
    try:
        git_root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=current,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except Exception:
        return current
    return Path(git_root).resolve()


def state_root() -> Path:
    return resolve_workspace_root() / STATE_DIR


def current_pointer() -> Path:
    return state_root() / "current.json"


def load_json(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def append_event(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=True) + "\n")


def read_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            events.append(payload)
    return events


def slugify(text: str) -> str:
    chars: list[str] = []
    for char in text.lower():
        if char.isalnum():
            chars.append(char)
        elif char in (" ", "-", "_"):
            chars.append("-")
    slug = "".join(chars)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-") or "session"


def session_files(session_path: Path) -> dict[str, str]:
    relative = Path(STATE_DIR) / "sessions" / session_path.name
    return {
        "events": str(relative / "events.jsonl"),
        "product_spec": str(relative / "product-spec.md"),
        "design_brief": str(relative / "design-brief.md"),
        "sprint_contract": str(relative / "sprint-contract.md"),
        "evaluation": str(relative / "evaluation.md"),
        "progress": str(relative / "progress.md"),
        "compact_state": str(relative / "compact-state.md"),
        "handoff": str(relative / "handoff.md"),
    }


def load_pointer() -> dict[str, Any] | None:
    return load_json(current_pointer())


def resolve_session_path(session_ref: str | None = None) -> Path:
    if session_ref:
        explicit = Path(session_ref).expanduser()
        if explicit.exists():
            return explicit.resolve()
        candidate = state_root() / "sessions" / session_ref
        if candidate.exists():
            return candidate.resolve()
        raise FileNotFoundError(f"unknown session: {session_ref}")
    pointer = load_pointer()
    if not pointer:
        raise FileNotFoundError("Harness Design Kit: no active session")
    return (resolve_workspace_root() / pointer["session_path"]).resolve()


def load_state(session_ref: str | None = None) -> tuple[Path, dict[str, Any]]:
    session_path = resolve_session_path(session_ref)
    payload = load_json(session_path / "state.json")
    if not payload:
        raise FileNotFoundError(f"missing state.json for session {session_path.name}")
    if isinstance(payload, dict):
        for key, value in STATE_FIELD_DEFAULTS.items():
            payload.setdefault(key, list(value) if isinstance(value, list) else value)
    return session_path, payload


def write_state(session_path: Path, payload: dict[str, Any], sync_pointer: bool = True) -> None:
    payload["updated_at"] = utc_now()
    write_json(session_path / "state.json", payload)
    if sync_pointer:
        write_json(
            current_pointer(),
            {
                "session_id": payload["session_id"],
                "session_path": payload["session_path"],
                "updated_at": payload["updated_at"],
            },
        )


def load_schema(schema_name: str) -> dict[str, Any]:
    path = schema_root() / schema_name
    if not path.exists():
        raise FileNotFoundError(f"schema not found: {schema_name}")
    payload = load_json(path)
    if not isinstance(payload, dict):
        raise ValidationError(f"schema is not an object: {schema_name}")
    return payload


def extract_headings(markdown: str) -> list[str]:
    matches = re.findall(r"(?m)^\s{0,3}#{1,6}\s+(.+?)\s*$", markdown)
    return [match.strip() for match in matches]


def normalize_label(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def split_markdown_sections(markdown: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current: str | None = None
    buffer: list[str] = []
    for raw_line in markdown.splitlines():
        match = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*$", raw_line)
        if match:
            if current is not None:
                sections[current] = "\n".join(buffer).strip()
            current = match.group(1).strip()
            buffer = []
            continue
        if current is not None:
            buffer.append(raw_line)
    if current is not None:
        sections[current] = "\n".join(buffer).strip()
    return sections


def is_placeholder_value(value: str) -> bool:
    normalized = normalize_label(value)
    if not normalized:
        return True
    if normalized in {"none", "n a", "tbd", "todo", "pending"}:
        return True
    if normalized in PLACEHOLDER_VALUES:
        return True
    if "goes here" in normalized:
        return True
    return False


def parse_markdown_list_items(section_text: str) -> list[str]:
    items: list[str] = []
    for raw_line in section_text.splitlines():
        match = re.match(r"^\s*[-*]\s*(.+?)\s*$", raw_line)
        if not match:
            continue
        entry = match.group(1).strip()
        value = entry
        if ":" in entry:
            _, candidate = entry.split(":", 1)
            candidate = candidate.strip()
            if candidate:
                value = candidate
        if is_placeholder_value(value):
            continue
        items.append(value)
    return items


def parse_label_value_lines(section_text: str) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for raw_line in section_text.splitlines():
        match = re.match(r"^\s*[-*]\s*([^:]+):\s*(.*?)\s*$", raw_line)
        if not match:
            continue
        label = match.group(1).strip()
        value = match.group(2).strip()
        pairs.append((label, value))
    return pairs


def parse_numeric_field(value: str, field_name: str) -> float:
    match = NUMERIC_RE.search(value)
    if not match:
        raise ValidationError(f"{field_name} must contain a number, got {value!r}")
    return float(match.group())


def expected_evaluation_criteria(mode: str) -> tuple[str, ...]:
    if mode == "frontend":
        return FRONTEND_EVALUATION_CRITERIA
    return APP_EVALUATION_CRITERIA


def parse_score_breakdown(section_text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    current: dict[str, str] = {}
    for raw_label, raw_value in parse_label_value_lines(section_text):
        label = normalize_label(raw_label)
        if label == "criterion":
            if current:
                rows.append(current)
            current = {"criterion": raw_value}
            continue
        if label in {"score", "threshold", "weight"}:
            if not current:
                raise ValidationError("score breakdown must start with a Criterion line")
            current[label] = raw_value
    if current:
        rows.append(current)

    parsed: list[dict[str, Any]] = []
    for row in rows:
        criterion = row.get("criterion", "").strip()
        if is_placeholder_value(criterion):
            continue
        missing = [field for field in ("score", "threshold", "weight") if field not in row]
        if missing:
            raise ValidationError(f"score row for {criterion!r} is missing {missing}")
        score = parse_numeric_field(row["score"], f"{criterion} score")
        threshold = parse_numeric_field(row["threshold"], f"{criterion} threshold")
        weight = parse_numeric_field(row["weight"], f"{criterion} weight")
        if weight <= 0:
            raise ValidationError(f"{criterion} weight must be greater than 0")
        parsed.append(
            {
                "criterion": criterion,
                "score": score,
                "threshold": threshold,
                "weight": weight,
                "passed": score >= threshold,
                "criterion_key": normalize_label(criterion),
            }
        )
    return parsed


def compute_weighted_summary(scores: list[dict[str, Any]], mode: str) -> dict[str, Any]:
    if not scores:
        return {
            "weighted_average": None,
            "weighted_threshold": None,
            "priority_criteria": [],
            "priority_threshold_misses": [],
            "weight_profile_valid": True,
            "decision_basis": "no scored criteria were provided",
        }

    total_weight = sum(max(float(entry["weight"]), 0.0) for entry in scores)
    if total_weight <= 0:
        total_weight = float(len(scores))
    weighted_average = sum(float(entry["score"]) * float(entry["weight"]) for entry in scores) / total_weight
    weighted_threshold = (
        sum(float(entry["threshold"]) * float(entry["weight"]) for entry in scores) / total_weight
    )

    criteria_by_key = {
        normalize_label(entry["criterion"]): entry
        for entry in scores
    }
    priority_criteria: list[str] = []
    weight_profile_valid = True
    priority_threshold_misses: list[str] = []
    basis_parts = [
        f"weighted_average={weighted_average:.2f}",
        f"weighted_threshold={weighted_threshold:.2f}",
    ]

    if mode == "frontend":
        priority_criteria = list(FRONTEND_PRIORITY_CRITERIA)
        priority_weights = [
            float(criteria_by_key.get(key, {}).get("weight", 0.0))
            for key in FRONTEND_PRIORITY_CRITERIA
        ]
        supporting_weights = [
            float(criteria_by_key.get(key, {}).get("weight", 0.0))
            for key in FRONTEND_SUPPORTING_CRITERIA
        ]
        if priority_weights and supporting_weights:
            weight_profile_valid = min(priority_weights) > max(supporting_weights)
        priority_threshold_misses = [
            entry["criterion"]
            for entry in scores
            if normalize_label(entry["criterion"]) in FRONTEND_PRIORITY_CRITERIA and not entry["passed"]
        ]
        basis_parts.append(
            "priority weights must make design quality and originality heavier than craft and functionality"
        )

    if priority_threshold_misses:
        basis_parts.append(
            "priority threshold misses=" + ", ".join(priority_threshold_misses)
        )
    if not weight_profile_valid:
        basis_parts.append("frontend weight profile is invalid")

    return {
        "weighted_average": weighted_average,
        "weighted_threshold": weighted_threshold,
        "priority_criteria": priority_criteria,
        "priority_threshold_misses": priority_threshold_misses,
        "weight_profile_valid": weight_profile_valid,
        "decision_basis": "; ".join(basis_parts),
    }


def validate_contract_artifact(session_path: Path) -> dict[str, list[str]]:
    markdown = (session_path / "sprint-contract.md").read_text(encoding="utf-8")
    sections = split_markdown_sections(markdown)
    required_lists = {
        "Objective": 1,
        "Deliverables": 1,
        "Out Of Scope": 1,
        "Acceptance Tests": 1,
        "Verification Steps": 1,
        "Evidence Requirements": 1,
        "Exit Criteria": 1,
    }
    parsed: dict[str, list[str]] = {}
    for section_name, min_items in required_lists.items():
        items = parse_markdown_list_items(sections.get(section_name, ""))
        if len(items) < min_items:
            raise ValidationError(f"sprint-contract.md must include real content under {section_name}")
        parsed[section_name] = items

    status_items = parse_label_value_lines(sections.get("Contract Status", ""))
    status_map = {normalize_label(label): value.strip() for label, value in status_items}
    status_value = status_map.get("status", "")
    if is_placeholder_value(status_value):
        raise ValidationError("sprint-contract.md must include a non-placeholder contract status")
    parsed["Contract Status"] = [status_value]
    return parsed


def validate_evaluation_artifact(
    session_path: Path,
    state: dict[str, Any],
    verdict: str,
) -> dict[str, Any]:
    markdown = (session_path / "evaluation.md").read_text(encoding="utf-8")
    sections = split_markdown_sections(markdown)
    scores = parse_score_breakdown(sections.get("Score Breakdown", ""))
    if not scores:
        raise ValidationError("evaluation.md must include scored criteria in Score Breakdown")

    expected = {normalize_label(item) for item in expected_evaluation_criteria(state.get("mode", "app"))}
    present = {entry["criterion_key"] for entry in scores}
    missing = sorted(expected - present)
    if missing:
        raise ValidationError(f"evaluation.md is missing scored criteria: {missing}")
    unexpected = sorted(present - expected)
    if unexpected:
        raise ValidationError(f"evaluation.md contains unexpected criteria: {unexpected}")
    criterion_counts: dict[str, int] = {}
    for entry in scores:
        criterion_counts[entry["criterion_key"]] = criterion_counts.get(entry["criterion_key"], 0) + 1
    duplicate_criteria = sorted(
        key for key, count in criterion_counts.items()
        if count > 1
    )
    if duplicate_criteria:
        raise ValidationError(f"evaluation.md contains duplicate scored criteria: {duplicate_criteria}")

    findings = parse_markdown_list_items(sections.get("Findings", ""))
    evidence = parse_markdown_list_items(sections.get("Evidence", ""))
    reproduction = parse_markdown_list_items(sections.get("Reproduction Steps", ""))
    artifact_refs = parse_markdown_list_items(sections.get("Artifact References", ""))
    recommendations = parse_markdown_list_items(sections.get("Recommendation", ""))
    verdict_items = {normalize_label(label): value for label, value in parse_label_value_lines(sections.get("Verdict", ""))}
    declared_verdict = verdict_items.get("verdict", "").strip()
    if declared_verdict and not is_placeholder_value(declared_verdict):
        if normalize_label(declared_verdict) != normalize_label(verdict):
            raise ValidationError(
                f"evaluation.md verdict {declared_verdict!r} does not match record-evaluation {verdict!r}"
            )

    if not evidence:
        raise ValidationError("evaluation.md must include at least one concrete evidence item")
    if not artifact_refs:
        raise ValidationError("evaluation.md must include at least one artifact reference")
    if verdict in {"fail", "revise", "pivot"} and not findings:
        raise ValidationError("non-pass evaluations must include at least one finding")
    if verdict in {"fail", "revise"} and not reproduction:
        raise ValidationError("fail or revise evaluations must include reproduction steps")
    if not recommendations:
        raise ValidationError("evaluation.md must include a concrete recommendation")
    recommendation_action = ""
    for item in recommendations:
        normalized = normalize_label(item)
        if normalized.startswith("accept"):
            recommendation_action = "accept"
            break
        if normalized.startswith("refine"):
            recommendation_action = "refine"
            break
        if normalized.startswith("pivot"):
            recommendation_action = "pivot"
            break
        if normalized.startswith("fail"):
            recommendation_action = "fail"
            break
    if not recommendation_action:
        raise ValidationError(
            "evaluation.md Recommendation must begin with accept, refine, pivot, or fail"
        )

    weighted_summary = compute_weighted_summary(scores, state.get("mode", "app"))
    threshold_misses = [entry["criterion"] for entry in scores if not entry["passed"]]
    if state.get("mode") == "frontend" and not weighted_summary["weight_profile_valid"]:
        raise ValidationError(
            "frontend evaluations must weight design quality and originality more heavily "
            "than craft and functionality"
        )
    if verdict == "pass" and threshold_misses:
        raise ValidationError(
            f"cannot record pass while criteria miss threshold: {', '.join(threshold_misses)}"
        )
    if verdict == "pass" and weighted_summary["weighted_average"] is not None:
        if weighted_summary["weighted_average"] < weighted_summary["weighted_threshold"]:
            raise ValidationError(
                "cannot record pass while weighted average is below the weighted threshold"
            )
    if verdict in {"fail", "revise"} and not threshold_misses:
        raise ValidationError(
            f"{verdict} requires at least one threshold miss in Score Breakdown"
        )

    live_artifact = state.get("last_live_eval_artifact", "").strip()
    if state.get("qa_target_url"):
        if not live_artifact:
            raise ValidationError("qa_target_url requires a live evaluation artifact before recording")
        artifact_path = session_path / live_artifact
        if not artifact_path.exists():
            raise ValidationError(f"live evaluation artifact is missing: {live_artifact}")
        if not any(ref.endswith(live_artifact) or ref == live_artifact for ref in artifact_refs):
            raise ValidationError(
                "evaluation.md Artifact References must include the latest live evaluation artifact"
            )
        if state.get("qa_flow_path"):
            artifact_markdown = artifact_path.read_text(encoding="utf-8")
            if "## Flow Execution" not in artifact_markdown:
                raise ValidationError(
                    "qa_flow_path requires the latest live evaluation artifact to include flow execution output"
                )
            json_artifact_path = artifact_path.with_suffix(".json")
            json_payload = load_json(json_artifact_path)
            if not isinstance(json_payload, dict):
                raise ValidationError(
                    "qa_flow_path requires the latest live evaluation JSON artifact alongside the markdown summary"
                )
            browser_payload = json_payload.get("browser_audit", {})
            if not isinstance(browser_payload, dict):
                raise ValidationError("live evaluation JSON artifact is missing browser_audit")
            flow_results = browser_payload.get("flow_results", [])
            if not isinstance(flow_results, list) or not flow_results:
                raise ValidationError(
                    "qa_flow_path requires the latest live evaluation artifact to execute flow steps"
                )
            if any(not isinstance(entry, dict) or not entry.get("ok") for entry in flow_results):
                raise ValidationError(
                    "cannot record evaluation while the latest live evaluation flow has failing steps"
                )
            command_checks = json_payload.get("command_checks", [])
            if command_checks:
                if not isinstance(command_checks, list):
                    raise ValidationError("live evaluation JSON artifact command_checks must be a list")
                if any(not isinstance(entry, dict) or not entry.get("ok") for entry in command_checks):
                    raise ValidationError(
                        "cannot record evaluation while the latest live evaluation command checks have failures"
                    )

    return {
        "scores": [
            {
                "criterion": entry["criterion"],
                "score": entry["score"],
                "threshold": entry["threshold"],
                "weight": entry["weight"],
                "passed": entry["passed"],
            }
            for entry in scores
        ],
        "weighted_average": weighted_summary["weighted_average"],
        "weighted_threshold": weighted_summary["weighted_threshold"],
        "priority_criteria": weighted_summary["priority_criteria"],
        "decision_basis": weighted_summary["decision_basis"],
        "threshold_misses": threshold_misses,
        "artifact_refs": artifact_refs,
        "evidence": evidence,
        "findings": findings,
        "recommendation_action": recommendation_action,
    }


def _matches_type(expected: str, value: Any) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return (isinstance(value, int) or isinstance(value, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    if expected == "markdown-sections":
        return isinstance(value, str)
    raise ValidationError(f"unsupported schema type: {expected}")


def validate_payload(schema: dict[str, Any], value: Any, path: str = "$") -> None:
    expected_type = schema.get("type")
    if expected_type is not None:
        expected_types = expected_type if isinstance(expected_type, list) else [expected_type]
        if not any(_matches_type(candidate, value) for candidate in expected_types):
            raise ValidationError(f"{path}: expected {expected_types}, got {type(value).__name__}")
        if "markdown-sections" in expected_types:
            required_sections = schema.get("required_sections", [])
            found = set(extract_headings(value))
            missing = [section for section in required_sections if section not in found]
            if missing:
                raise ValidationError(f"{path}: missing markdown sections {missing}")
            return

    if "enum" in schema and value not in schema["enum"]:
        raise ValidationError(f"{path}: expected one of {schema['enum']}, got {value!r}")

    if schema.get("type") == "object":
        required = schema.get("required", [])
        for key in required:
            if key not in value:
                raise ValidationError(f"{path}: missing required key {key!r}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties", True) is False:
            for key in value.keys():
                if key not in properties:
                    raise ValidationError(f"{path}: unexpected key {key!r}")
        for key, child_schema in properties.items():
            if key in value:
                validate_payload(child_schema, value[key], f"{path}.{key}")
        return

    if schema.get("type") == "array":
        items = schema.get("items")
        if items:
            for index, item in enumerate(value):
                validate_payload(items, item, f"{path}[{index}]")
        min_items = schema.get("minItems")
        if min_items is not None and len(value) < min_items:
            raise ValidationError(f"{path}: expected at least {min_items} items, got {len(value)}")
        return


def validate_named_schema(schema_name: str, payload: Any) -> None:
    validate_payload(load_schema(schema_name), payload)


def validate_session_bundle(session_path: Path, state: dict[str, Any] | None = None) -> list[str]:
    if state is None:
        _, state = load_state(session_path.name)
    validate_named_schema("session.schema.json", state)
    validated = ["state.json"]
    for filename, schema_name in ARTIFACT_SCHEMA_BY_FILENAME.items():
        path = session_path / filename
        if not path.exists():
            raise ValidationError(f"missing artifact: {filename}")
        markdown = path.read_text(encoding="utf-8")
        validate_named_schema(schema_name, markdown)
        if filename == "compact-state.md":
            validate_compact_state_artifact(markdown, state)
        validated.append(filename)
    return validated


class SafeDict(dict[str, str]):
    def __missing__(self, key: str) -> str:
        return "{" + key + "}"


def render_template(template_name: str, replacements: dict[str, str]) -> str:
    template_path = templates_root() / template_name
    if not template_path.exists():
        title = FALLBACK_TITLES.get(template_name, template_name)
        return f"# {title}\n"
    return template_path.read_text(encoding="utf-8").format_map(SafeDict(replacements))


def initialize_artifacts(session_path: Path, replacements: dict[str, str]) -> None:
    for filename in ARTIFACT_SCHEMA_BY_FILENAME:
        content = render_template(filename, replacements)
        write_text(session_path / filename, content)


def non_heading_excerpt(path: Path, max_lines: int = 8) -> str:
    if not path.exists():
        return "_Not recorded._"
    lines = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        if not line.strip():
            continue
        if line.lstrip().startswith("#"):
            continue
        lines.append(line)
        if len(lines) >= max_lines:
            break
    return "\n".join(lines) if lines else "_No details recorded yet._"


def build_handoff_markdown(state: dict[str, Any], session_path: Path, reason: str) -> str:
    product_spec = non_heading_excerpt(session_path / "product-spec.md", max_lines=10)
    contract = non_heading_excerpt(session_path / "sprint-contract.md", max_lines=10)
    progress = non_heading_excerpt(session_path / "progress.md", max_lines=10)
    evaluation = non_heading_excerpt(session_path / "evaluation.md", max_lines=10)
    next_steps = []
    if state.get("phase") == "evaluate":
        next_steps.append("Review the latest evaluation and decide whether to refine or pivot.")
    elif state.get("phase") == "build":
        next_steps.append("Resume implementation against the active contract or continuous build scope.")
    else:
        next_steps.append("Read the session artifacts and continue from the current phase.")
    if state.get("qa_target_url"):
        next_steps.append(f"Open and test {state['qa_target_url']}.")
    resume_commands = [
        "python3 ./harness-design-kit/scripts/harness_state.py summary",
        "python3 ./harness-design-kit/scripts/harness_run.py status",
    ]
    if state.get("execution_mode") == "reset":
        resume_commands.append("python3 ./harness-design-kit/scripts/harness_run.py advance")
    lines = [
        "# Handoff",
        "",
        "## Current Goal",
        state.get("goal", ""),
        "",
        "## Harness Configuration",
        f"- Mode: {state.get('mode', 'unknown')}",
        f"- Architecture profile: {state.get('architecture_profile', 'unknown')}",
        f"- Execution mode: {state.get('execution_mode', 'unknown')}",
        f"- Evaluator mode: {state.get('evaluator_mode', 'unknown')}",
        f"- Current phase: {state.get('phase', 'unknown')}",
        f"- Current round: {state.get('current_round', 0)}",
        "",
        "## Accepted Product Spec Summary",
        product_spec,
        "",
        "## Latest Contract",
        contract,
        "",
        "## Completed Work",
        progress,
        "",
        "## Open Bugs Or Failing Checks",
        evaluation,
        "",
        "## Reset Reason",
        reason or state.get("last_reset_reason", ""),
        "",
        "## Exact Next Steps",
        *[f"- {step}" for step in next_steps],
        "",
        "## Resume Commands",
        *[f"- `{command}`" for command in resume_commands],
        "",
    ]
    return "\n".join(lines).rstrip() + "\n"


def collect_compact_source_artifacts(session_path: Path, state: dict[str, Any]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()

    def record(relative_path: str) -> None:
        if not relative_path or relative_path in seen:
            return
        if (session_path / relative_path).exists():
            ordered.append(relative_path)
            seen.add(relative_path)

    for filename in (
        "product-spec.md",
        "design-brief.md",
        "sprint-contract.md",
        "progress.md",
        "evaluation.md",
    ):
        record(filename)

    for field_name in ("last_contract_review_artifact", "last_live_eval_artifact"):
        relative_path = str(state.get(field_name, "") or "")
        if relative_path:
            record(relative_path)

    return ordered


def validate_compact_state_artifact(markdown: str, state: dict[str, Any] | None = None) -> None:
    if state and not state.get("last_compaction_artifact"):
        return
    sections = split_markdown_sections(markdown)
    accepted_facts = parse_markdown_list_items(sections.get("Accepted Facts", ""))
    if not accepted_facts:
        raise ValidationError("compact-state.md must include at least one accepted fact")

    open_questions = parse_markdown_list_items(sections.get("Open Questions", ""))
    if len(open_questions) > 3:
        raise ValidationError("compact-state.md may include at most three open questions")

    next_steps = parse_markdown_list_items(sections.get("Immediate Next Step", ""))
    if len(next_steps) != 1:
        raise ValidationError("compact-state.md must include exactly one immediate next step")

    source_artifacts = parse_markdown_list_items(sections.get("Source Artifacts", ""))
    if not source_artifacts:
        raise ValidationError("compact-state.md must reference at least one source artifact")

    resume_prompt = parse_markdown_list_items(sections.get("Resume Prompt", ""))
    if len(resume_prompt) != 1:
        raise ValidationError("compact-state.md must include exactly one resume prompt line")


def build_compact_state_markdown(
    state: dict[str, Any],
    session_path: Path,
    reason: str,
    *,
    next_actor: str = "",
    next_action: str = "",
    source_artifacts: list[str] | None = None,
) -> str:
    product_spec = non_heading_excerpt(session_path / "product-spec.md", max_lines=6)
    contract = non_heading_excerpt(session_path / "sprint-contract.md", max_lines=6)
    progress = non_heading_excerpt(session_path / "progress.md", max_lines=6)
    evaluation = non_heading_excerpt(session_path / "evaluation.md", max_lines=6)
    source_refs = source_artifacts or collect_compact_source_artifacts(session_path, state)
    accepted_facts = [
        f"Goal: {state.get('goal', '')}",
        (
            "Session configuration: "
            f"mode={state.get('mode', 'unknown')}, "
            f"architecture={state.get('architecture_profile', 'unknown')}, "
            f"phase={state.get('phase', 'unknown')}, "
            f"contract={state.get('contract_status', 'unknown')}"
        ),
    ]
    if product_spec not in {"_Not recorded._", "_No details recorded yet._"}:
        accepted_facts.append(f"Product spec delta: {product_spec.splitlines()[0]}")
    if state.get("current_candidate_id"):
        accepted_facts.append(f"Active candidate: {state.get('current_candidate_id')}")

    failing_evidence: list[str] = []
    if state.get("last_contract_review_findings"):
        failing_evidence.extend(str(item) for item in state["last_contract_review_findings"])
    elif evaluation not in {"_Not recorded._", "_No details recorded yet._"}:
        failing_evidence.append(evaluation.splitlines()[0])

    unresolved_questions = [
        str(item)
        for item in state.get("last_contract_review_findings", [])[:3]
        if str(item).strip()
    ]
    next_step = next_action or "Use this compact state to resume the active phase with the latest verified evidence."
    resume_prompt = (
        "Treat this compact state as the only context source. "
        f"Resume with {next_actor or 'the next actor'} and execute: {next_step}"
    )

    lines = [
        "# Compact State",
        "",
        "## Current Goal",
        f"- Goal: {state.get('goal', '')}",
        "",
        "## Session Snapshot",
        f"- Mode: {state.get('mode', 'unknown')}",
        f"- Architecture profile: {state.get('architecture_profile', 'unknown')}",
        f"- Execution mode: {state.get('execution_mode', 'unknown')}",
        f"- Evaluator mode: {state.get('evaluator_mode', 'unknown')}",
        f"- Current phase: {state.get('phase', 'unknown')}",
        f"- Current round: {state.get('current_round', 0)}",
        f"- Compaction reason: {reason or state.get('last_compaction_reason', '')}",
        "",
        "## Accepted Facts",
        *[f"- {item}" for item in accepted_facts],
        "",
        "## Active Contract",
        contract,
        "",
        "## Current Progress",
        progress,
        "",
        "## Latest Failing Evidence",
        *([f"- {item}" for item in failing_evidence] if failing_evidence else ["- No failing evidence currently recorded."]),
        "",
        "## Open Questions",
        *([f"- {item}" for item in unresolved_questions] if unresolved_questions else ["- No unresolved questions currently recorded."]),
        "",
        "## Immediate Next Step",
        f"- {next_step}",
        "",
        "## Resume Prompt",
        f"- {resume_prompt}",
        "",
        "## Source Artifacts",
        *([f"- {item}" for item in source_refs] if source_refs else ["- compact-state.md"]),
        "",
    ]
    return "\n".join(lines).rstrip() + "\n"


def session_artifact_dir(session_path: Path) -> Path:
    path = session_path / "artifacts"
    path.mkdir(parents=True, exist_ok=True)
    return path
