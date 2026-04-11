#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import shlex
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


OPENAI_DEFAULT_MODELS = {
    "planner": "gpt-5.4",
    "generator": "gpt-5.4",
    "qa-evaluator": "gpt-5.4",
    "design-evaluator": "gpt-5.4",
    "compactor": "gpt-5.4-mini",
}
ANTHROPIC_DEFAULT_MODELS = {
    "planner": "claude-sonnet-4-20250514",
    "generator": "claude-sonnet-4-20250514",
    "qa-evaluator": "claude-sonnet-4-20250514",
    "design-evaluator": "claude-sonnet-4-20250514",
    "compactor": "claude-haiku-3-5-20241022",
}


class RunnerError(RuntimeError):
    pass


@dataclass(frozen=True)
class RunResult:
    output: str
    provider: str
    model: str


def configured_provider() -> str:
    explicit = os.environ.get("HARNESS_DESIGN_KIT_PROVIDER", "").strip().lower()
    if explicit:
        return explicit
    if os.environ.get("HARNESS_DESIGN_KIT_RUNNER", "").strip().lower() == "external":
        return "external"
    if os.environ.get("ANTHROPIC_API_KEY", "").strip():
        return "anthropic"
    if os.environ.get("OPENAI_API_KEY", "").strip():
        return "openai"
    return "unconfigured"


def configured_model(actor: str, provider: str | None = None) -> str:
    provider_name = provider or configured_provider()
    if actor == "planner":
        env_value = os.environ.get("HARNESS_DESIGN_KIT_MODEL_PLANNER", "").strip()
    elif actor == "generator":
        env_value = os.environ.get("HARNESS_DESIGN_KIT_MODEL_GENERATOR", "").strip()
    elif actor == "compactor":
        env_value = (
            os.environ.get("HARNESS_DESIGN_KIT_COMPACTION_MODEL", "").strip()
            or os.environ.get("HARNESS_DESIGN_KIT_MODEL_EVALUATOR", "").strip()
        )
    else:
        env_value = os.environ.get("HARNESS_DESIGN_KIT_MODEL_EVALUATOR", "").strip()
    if env_value:
        return env_value
    shared = os.environ.get("HARNESS_DESIGN_KIT_MODEL", "").strip()
    if shared:
        return shared
    if provider_name == "anthropic":
        return ANTHROPIC_DEFAULT_MODELS.get(actor, ANTHROPIC_DEFAULT_MODELS["generator"])
    return OPENAI_DEFAULT_MODELS.get(actor, OPENAI_DEFAULT_MODELS["generator"])


def _system_prompt(actor: str) -> str:
    return (
        f"You are the {actor} for Harness Design Kit. "
        "Return only the requested markdown artifact. "
        "Do not wrap the answer in code fences or commentary."
    )


def _request_json(url: str, headers: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RunnerError(f"{url} returned HTTP {exc.code}: {error_body}") from exc
    except urllib.error.URLError as exc:
        raise RunnerError(f"runner request failed for {url}: {exc}") from exc


def _normalize_output(markdown: str) -> str:
    text = markdown.strip()
    if not text:
        raise RunnerError("runner returned an empty artifact")
    return text + "\n"


def _extract_openai_text(payload: dict[str, Any]) -> str:
    direct = payload.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return _normalize_output(direct)

    fragments: list[str] = []
    for item in payload.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if not isinstance(content, dict):
                continue
            if content.get("type") in {"output_text", "text"}:
                text = content.get("text")
                if isinstance(text, str) and text.strip():
                    fragments.append(text.strip())

    if fragments:
        return _normalize_output("\n\n".join(fragments))

    raise RunnerError("OpenAI response did not contain output_text content")


def _extract_anthropic_text(payload: dict[str, Any]) -> str:
    fragments: list[str] = []
    for content in payload.get("content", []):
        if not isinstance(content, dict):
            continue
        if content.get("type") == "text":
            text = content.get("text")
            if isinstance(text, str) and text.strip():
                fragments.append(text.strip())
    if fragments:
        return _normalize_output("\n\n".join(fragments))
    raise RunnerError("Anthropic response did not contain text content")


def _run_openai(actor: str, prompt: str, model: str) -> RunResult:
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RunnerError("OPENAI_API_KEY is required for provider=openai")
    base_url = os.environ.get("HARNESS_DESIGN_KIT_OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    payload = {
        "model": model,
        "input": [
            {
                "role": "system",
                "content": [{"type": "input_text", "text": _system_prompt(actor)}],
            },
            {
                "role": "user",
                "content": [{"type": "input_text", "text": prompt}],
            },
        ],
    }
    response = _request_json(
        f"{base_url}/responses",
        {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        payload,
    )
    return RunResult(_extract_openai_text(response), "openai", model)


def _run_anthropic(actor: str, prompt: str, model: str) -> RunResult:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        raise RunnerError("ANTHROPIC_API_KEY is required for provider=anthropic")
    payload = {
        "model": model,
        "max_tokens": 2400,
        "system": _system_prompt(actor),
        "messages": [{"role": "user", "content": prompt}],
    }
    response = _request_json(
        "https://api.anthropic.com/v1/messages",
        {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        payload,
    )
    return RunResult(_extract_anthropic_text(response), "anthropic", model)


def _run_external(actor: str, prompt: str, state: dict[str, object], session_path: Path) -> RunResult:
    command = os.environ.get("HARNESS_DESIGN_KIT_AGENT_RUNNER", "").strip()
    if not command:
        raise RunnerError("HARNESS_DESIGN_KIT_AGENT_RUNNER is required for provider=external")
    try:
        argv = shlex.split(command)
    except ValueError as exc:
        raise RunnerError(f"invalid HARNESS_DESIGN_KIT_AGENT_RUNNER: {exc}") from exc
    env = os.environ.copy()
    env.update(
        {
            "HARNESS_ACTOR": actor,
            "HARNESS_PHASE": str(state.get("phase", "")),
            "HARNESS_MODE": str(state.get("mode", "")),
            "HARNESS_SESSION_ID": str(state.get("session_id", "")),
            "HARNESS_SESSION_PATH": str(session_path),
        }
    )
    completed = subprocess.run(
        argv,
        input=prompt,
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.strip()
        raise RunnerError(
            f"external runner exited with {completed.returncode}"
            + (f": {stderr}" if stderr else "")
        )
    return RunResult(_normalize_output(completed.stdout), "external", "external-command")


def run_actor(actor: str, prompt: str, state: dict[str, object], session_path: Path) -> RunResult:
    provider = configured_provider()
    if provider == "unconfigured":
        raise RunnerError(
            "No native runner provider is configured. Set HARNESS_DESIGN_KIT_PROVIDER, "
            "OPENAI_API_KEY, ANTHROPIC_API_KEY, or HARNESS_DESIGN_KIT_RUNNER=external."
        )
    if provider == "external":
        return _run_external(actor, prompt, state, session_path)
    if provider not in {"openai", "anthropic"}:
        raise RunnerError(f"unsupported HARNESS_DESIGN_KIT_PROVIDER: {provider}")

    model = configured_model(actor, provider)
    if provider == "openai":
        return _run_openai(actor, prompt, model)
    return _run_anthropic(actor, prompt, model)
