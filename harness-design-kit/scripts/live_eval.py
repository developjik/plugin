#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from harness_lib import (
    ValidationError,
    append_event,
    load_state,
    resolve_workspace_root,
    session_artifact_dir,
    state_root,
    utc_now,
    validate_named_schema,
    validate_session_bundle,
    write_state,
    write_text,
)


def event_path(session_path: Path) -> Path:
    return session_path / "events.jsonl"


def _fetch_url(url: str, timeout: int) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "HarnessDesignKit/0.2 live-eval",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body_bytes = response.read()
            body = body_bytes.decode("utf-8", errors="replace")
            return {
                "ok": True,
                "status": getattr(response, "status", 200),
                "url": response.geturl(),
                "headers": dict(response.headers.items()),
                "body": body,
                "error": "",
            }
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return {
            "ok": False,
            "status": exc.code,
            "url": url,
            "headers": dict(exc.headers.items()) if exc.headers else {},
            "body": body,
            "error": str(exc),
        }
    except Exception as exc:
        return {
            "ok": False,
            "status": 0,
            "url": url,
            "headers": {},
            "body": "",
            "error": str(exc),
        }


def _extract_title(html: str) -> str:
    match = re.search(r"(?is)<title[^>]*>(.*?)</title>", html)
    if not match:
        return ""
    title = re.sub(r"\s+", " ", match.group(1)).strip()
    return title


PLAYWRIGHT_PACKAGE = "playwright@latest"


def _playwright_runtime_root() -> Path:
    configured = os.environ.get("HARNESS_DESIGN_KIT_PLAYWRIGHT_ROOT")
    if configured:
        return Path(configured).expanduser().resolve()
    return state_root() / "tools" / "playwright-runtime"


def _playwright_module_dir(runtime_root: Path) -> Path:
    return runtime_root / "node_modules" / "playwright"


def _playwright_cli_script(runtime_root: Path) -> Path:
    return _playwright_module_dir(runtime_root) / "cli.js"


def _playwright_browser_marker(runtime_root: Path) -> Path:
    return runtime_root / ".chromium-installed"


def _playwright_exec_env(runtime_root: Path) -> dict[str, str]:
    env = os.environ.copy()
    node_modules = runtime_root / "node_modules"
    existing = env.get("NODE_PATH", "")
    env["NODE_PATH"] = str(node_modules) if not existing else os.pathsep.join([str(node_modules), existing])
    return env


def _ensure_playwright_runtime() -> tuple[bool, str, Path]:
    runtime_root = _playwright_runtime_root()
    runtime_root.mkdir(parents=True, exist_ok=True)

    package_json = runtime_root / "package.json"
    if not package_json.exists():
        package_json.write_text(
            json.dumps(
                {
                    "name": "harness-design-kit-playwright-runtime",
                    "private": True,
                    "description": "Cached Playwright runtime for Harness Design Kit live evaluation",
                },
                indent=2,
                ensure_ascii=True,
            )
            + "\n",
            encoding="utf-8",
        )

    module_dir = _playwright_module_dir(runtime_root)
    if not module_dir.exists():
        install = subprocess.run(
            ["npm", "install", "--no-save", PLAYWRIGHT_PACKAGE],
            cwd=runtime_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if install.returncode != 0:
            stderr = (install.stderr or install.stdout or "").strip()
            return False, stderr or "failed to install Playwright runtime", runtime_root

    cli_script = _playwright_cli_script(runtime_root)
    if not cli_script.exists():
        return False, "playwright CLI script is missing from the cached runtime", runtime_root

    marker = _playwright_browser_marker(runtime_root)
    if not marker.exists():
        install_browser = subprocess.run(
            ["node", str(cli_script), "install", "chromium"],
            cwd=runtime_root,
            capture_output=True,
            text=True,
            check=False,
            env=_playwright_exec_env(runtime_root),
        )
        if install_browser.returncode != 0:
            stderr = (install_browser.stderr or install_browser.stdout or "").strip()
            return False, stderr or "failed to install Chromium for Playwright", runtime_root
        marker.write_text("chromium\n", encoding="utf-8")

    return True, "", runtime_root


def _playwright_available() -> tuple[bool, str, Path]:
    return _ensure_playwright_runtime()


def _resolve_flow_path(session_path: Path, raw_path: str) -> Path:
    candidate = Path(raw_path).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    workspace_root = resolve_workspace_root()
    session_candidate = (session_path / candidate).resolve()
    if session_candidate.exists():
        return session_candidate
    return (workspace_root / candidate).resolve()


def _load_flow_definition(session_path: Path, raw_path: str | None) -> tuple[dict[str, Any] | None, str]:
    if not raw_path:
        return None, ""
    flow_path = _resolve_flow_path(session_path, raw_path)
    if not flow_path.exists():
        raise ValidationError(f"live-eval flow file does not exist: {flow_path}")
    try:
        payload = json.loads(flow_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValidationError(f"live-eval flow is not valid JSON: {flow_path}") from exc
    validate_named_schema("live-eval-flow.schema.json", payload)
    if not isinstance(payload, dict):
        raise ValidationError("live-eval flow must decode to an object")
    for index, check in enumerate(payload.get("command_checks", []), start=1):
        if not isinstance(check, dict):
            raise ValidationError(f"command_checks entry {index} must be an object")
        if not str(check.get("command", "")).strip():
            raise ValidationError(f"command_checks entry {index} requires command")
        if not any(field in check for field in ("expect_exit_code", "expect_contains", "expect_regex")):
            raise ValidationError(
                f"command_checks entry {index} requires expect_exit_code, expect_contains, or expect_regex"
            )
    for index, step in enumerate(payload.get("steps", []), start=1):
        step_type = step.get("type")
        if step_type in {"click", "fill"} and not step.get("selector"):
            raise ValidationError(f"flow step {index} ({step_type}) requires selector")
        if step_type == "press" and not (step.get("selector") or step.get("key")):
            raise ValidationError(f"flow step {index} (press) requires selector or key")
        if step_type == "assert_text" and not step.get("text"):
            raise ValidationError(f"flow step {index} (assert_text) requires text")
        if step_type == "assert_request" and not (step.get("url_contains") or step.get("method")):
            raise ValidationError(
                f"flow step {index} (assert_request) requires url_contains or method"
            )
        if step_type == "assert_response" and not (step.get("url_contains") or step.get("status")):
            raise ValidationError(
                f"flow step {index} (assert_response) requires url_contains or status"
            )
        if step_type == "assert_storage":
            if not step.get("key"):
                raise ValidationError(f"flow step {index} (assert_storage) requires key")
            if not any(field in step for field in ("equals", "includes", "non_empty")):
                raise ValidationError(
                    f"flow step {index} (assert_storage) requires equals, includes, or non_empty"
                )
    return payload, str(flow_path)


def _resolve_check_cwd(session_path: Path, raw_path: str | None) -> Path:
    if not raw_path:
        return resolve_workspace_root()
    candidate = Path(raw_path).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    session_candidate = (session_path / candidate).resolve()
    if session_candidate.exists():
        return session_candidate
    return (resolve_workspace_root() / candidate).resolve()


def _run_command_checks(session_path: Path, flow_definition: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not flow_definition:
        return []
    results: list[dict[str, Any]] = []
    for index, check in enumerate(flow_definition.get("command_checks", []), start=1):
        name = str(check.get("name") or f"command-check-{index}")
        command = str(check.get("command", "")).strip()
        cwd = _resolve_check_cwd(session_path, check.get("cwd"))
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=False,
            cwd=cwd,
        )
        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()
        expected_exit = int(check.get("expect_exit_code", 0))
        ok = result.returncode == expected_exit
        if "expect_contains" in check:
            ok = ok and str(check["expect_contains"]) in stdout
        if "expect_regex" in check:
            ok = ok and re.search(str(check["expect_regex"]), stdout) is not None
        results.append(
            {
                "name": name,
                "command": command,
                "cwd": str(cwd),
                "ok": ok,
                "exit_code": result.returncode,
                "expected_exit_code": expected_exit,
                "stdout": stdout[:4000],
                "stderr": stderr[:4000],
            }
        )
    return results


def _artifact_base_path(artifact_dir: Path, round_stamp: int) -> Path:
    base = artifact_dir / f"eval-r{round_stamp or 0}"
    if not (base.with_suffix(".md").exists() or base.with_suffix(".json").exists() or base.with_suffix(".png").exists()):
        return base
    suffix = 2
    while True:
        candidate = artifact_dir / f"eval-r{round_stamp or 0}-{suffix}"
        if not (
            candidate.with_suffix(".md").exists()
            or candidate.with_suffix(".json").exists()
            or candidate.with_suffix(".png").exists()
        ):
            return candidate
        suffix += 1


def _capture_screenshot(url: str, output_path: Path, timeout_ms: int) -> tuple[bool, str]:
    available, error, runtime_root = _playwright_available()
    if not available:
        return False, error or "playwright runtime is not available"
    cmd = [
        "node",
        str(_playwright_cli_script(runtime_root)),
        "screenshot",
        "--browser",
        "chromium",
        "--wait-for-timeout",
        str(timeout_ms),
        "--timeout",
        str(timeout_ms * 2),
        url,
        str(output_path),
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
        cwd=runtime_root,
        env=_playwright_exec_env(runtime_root),
    )
    if result.returncode == 0 and output_path.exists():
        return True, ""
    stderr = (result.stderr or result.stdout or "").strip()
    return False, stderr or "playwright screenshot failed"


def _run_playwright_audit(
    url: str,
    output_path: Path,
    timeout_ms: int,
    flow_definition: dict[str, Any] | None = None,
) -> dict[str, Any]:
    available, runtime_error, runtime_root = _playwright_available()
    if not available:
        return {
            "ok": False,
            "available": False,
            "error": runtime_error or "playwright runtime is not available",
            "screenshot_path": "",
            "console_messages": [],
            "page_errors": [],
            "failed_requests": [],
            "response_errors": [],
            "interactive_summary": {},
            "interaction_checks": [],
        }
    script = r"""
const fs = require('fs');
const { chromium } = require('playwright');

const [url, screenshotPath, timeoutMsRaw, resultPath, flowPath] = process.argv.slice(2);
const timeoutMs = Number(timeoutMsRaw);
const flow = flowPath && fs.existsSync(flowPath) ? JSON.parse(fs.readFileSync(flowPath, 'utf8')) : null;

function visibleText(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

(async () => {
  const MAX_NETWORK_ENTRIES = 1000;
  const consoleMessages = [];
  const pageErrors = [];
  const failedRequests = [];
  const responseErrors = [];
  const requestsSeen = [];
  const responsesSeen = [];
  const interactionChecks = [];
  const flowResults = [];
  let networkWindowStartRequests = 0;
  let networkWindowStartResponses = 0;
  let finalDocumentStatus = 0;
  let browser;
  let page;

  const collectInteractiveSummary = async () =>
    page.evaluate(() => {
      const visibleText = (value) => String(value || '').replace(/\s+/g, ' ').trim();
      const isVisible = (element) => {
        const rect = element.getBoundingClientRect();
        const style = window.getComputedStyle(element);
        return (
          style.display !== 'none' &&
          style.visibility !== 'hidden' &&
          rect.width > 0 &&
          rect.height > 0
        );
      };
      const sample = (elements, projector) =>
        elements
          .filter((element) => isVisible(element))
          .slice(0, 5)
          .map(projector);

      return {
        title: document.title,
        headingCount: document.querySelectorAll('h1, h2, h3').length,
        buttonCount: document.querySelectorAll('button, [role="button"], input[type="button"], input[type="submit"]').length,
        linkCount: document.querySelectorAll('a[href]').length,
        formCount: document.forms.length,
        inputCount: document.querySelectorAll('input:not([type="hidden"]), textarea, select').length,
        headings: sample([...document.querySelectorAll('h1, h2, h3')], (element) => visibleText(element.innerText || element.textContent)),
        buttons: sample(
          [...document.querySelectorAll('button, [role="button"], input[type="button"], input[type="submit"]')],
          (element) =>
            visibleText(
              element.innerText ||
                element.textContent ||
                element.getAttribute('aria-label') ||
                element.getAttribute('value')
            )
        ),
        links: sample([...document.querySelectorAll('a[href]')], (element) => ({
          text: visibleText(element.innerText || element.textContent),
          href: element.getAttribute('href') || '',
        })),
        forms: [...document.forms].slice(0, 3).map((form) => ({
          action: form.getAttribute('action') || '',
          method: (form.getAttribute('method') || 'get').toLowerCase(),
          fieldCount: form.querySelectorAll('input, textarea, select').length,
        })),
      };
    });

  const setNetworkWindowStart = () => {
    networkWindowStartRequests = requestsSeen.length;
    networkWindowStartResponses = responsesSeen.length;
  };

  const currentRequestWindow = () => requestsSeen.slice(networkWindowStartRequests);
  const currentResponseWindow = () => responsesSeen.slice(networkWindowStartResponses);

  const waitForWindowMatch = async (entriesFn, predicate, timeout) => {
    const deadline = Date.now() + timeout;
    while (Date.now() <= deadline) {
      if (entriesFn().some(predicate)) {
        return true;
      }
      const remaining = deadline - Date.now();
      if (remaining <= 0) {
        break;
      }
      await page.waitForTimeout(Math.min(100, remaining));
    }
    return false;
  };

  try {
    browser = await chromium.launch({ headless: true });
    page = await browser.newPage();

    page.on('console', (msg) => {
      const type = msg.type();
      if (type === 'error' || type === 'warning') {
        consoleMessages.push({ type, text: msg.text() });
      }
    });
    page.on('pageerror', (err) => {
      pageErrors.push(String(err));
    });
    page.on('requestfailed', (request) => {
      failedRequests.push({
        url: request.url(),
        method: request.method(),
        error: request.failure() ? request.failure().errorText : '',
      });
    });
    page.on('request', (request) => {
      requestsSeen.push({
        url: request.url(),
        method: request.method(),
      });
      if (requestsSeen.length > MAX_NETWORK_ENTRIES) {
        requestsSeen.shift();
      }
    });
    page.on('response', (response) => {
      responsesSeen.push({
        url: response.url(),
        status: response.status(),
      });
      if (responsesSeen.length > MAX_NETWORK_ENTRIES) {
        responsesSeen.shift();
      }
      if (response.status() >= 400) {
        responseErrors.push({
          url: response.url(),
          status: response.status(),
        });
      }
      try {
        const request = response.request();
        if (request.resourceType() === 'document' && request.frame() === page.mainFrame()) {
          finalDocumentStatus = response.status();
        }
      } catch (err) {}
    });

    const response = await page.goto(url, {
      waitUntil: 'networkidle',
      timeout: timeoutMs * 2,
    });
    await page.waitForTimeout(Math.min(timeoutMs, 3000));
    setNetworkWindowStart();

    const firstInput = page.locator('input:not([type="hidden"]):not([disabled]), textarea:not([disabled]), select:not([disabled])').first();
    if ((await firstInput.count()) > 0) {
      try {
        await firstInput.focus({ timeout: 1000 });
        interactionChecks.push({ target: 'first-input', action: 'focus', ok: true });
      } catch (err) {
        interactionChecks.push({ target: 'first-input', action: 'focus', ok: false, error: String(err) });
      }
    }

    const firstClickable = page.locator('button, [role="button"], a[href], input[type="button"], input[type="submit"]').first();
    if ((await firstClickable.count()) > 0) {
      try {
        await firstClickable.hover({ timeout: 1000 });
        interactionChecks.push({ target: 'first-clickable', action: 'hover', ok: true });
      } catch (err) {
        interactionChecks.push({ target: 'first-clickable', action: 'hover', ok: false, error: String(err) });
      }
    }

    async function runFlowStep(step, index) {
      const timeout = Number(step.timeout_ms || timeoutMs);
      const name = step.name || `step-${index + 1}`;
      const type = step.type;
      if (type === 'goto') {
        setNetworkWindowStart();
        const currentBase = page.url() && page.url().startsWith('http') ? page.url() : url;
        const target = step.url ? new URL(step.url, currentBase).toString() : url;
        await page.goto(target, { waitUntil: 'networkidle', timeout: timeout * 2 });
      } else if (type === 'click') {
        setNetworkWindowStart();
        await page.locator(step.selector).first().click({ timeout });
      } else if (type === 'fill') {
        setNetworkWindowStart();
        await page.locator(step.selector).first().fill(step.value || '', { timeout });
      } else if (type === 'press') {
        setNetworkWindowStart();
        const locator = step.selector
          ? page.locator(step.selector).first()
          : page.locator('body');
        await locator.press(step.key || 'Enter', { timeout });
      } else if (type === 'assert_text') {
        const text = String(step.text || '');
        const content = step.selector
          ? await page.locator(step.selector).first().textContent({ timeout })
          : await page.content();
        if (!String(content || '').includes(text)) {
          throw new Error(`expected text not found: ${text}`);
        }
      } else if (type === 'assert_url') {
        const currentUrl = page.url();
        if (step.url && currentUrl !== step.url) {
          throw new Error(`expected URL ${step.url} but got ${currentUrl}`);
        }
        if (step.url_contains && !currentUrl.includes(step.url_contains)) {
          throw new Error(`expected URL containing ${step.url_contains} but got ${currentUrl}`);
        }
      } else if (type === 'assert_request') {
        const matched = await waitForWindowMatch(
          currentRequestWindow,
          (entry) => {
            const methodOk = step.method ? entry.method.toLowerCase() === String(step.method).toLowerCase() : true;
            const urlOk = step.url_contains ? entry.url.includes(step.url_contains) : true;
            return methodOk && urlOk;
          },
          timeout
        );
        if (!matched) {
          throw new Error('expected matching request was not observed in the current flow window');
        }
      } else if (type === 'assert_response') {
        const matched = await waitForWindowMatch(
          currentResponseWindow,
          (entry) => {
            const statusOk = step.status ? entry.status === Number(step.status) : true;
            const urlOk = step.url_contains ? entry.url.includes(step.url_contains) : true;
            return statusOk && urlOk;
          },
          timeout
        );
        if (!matched) {
          throw new Error('expected matching response was not observed in the current flow window');
        }
      } else if (type === 'assert_storage') {
        const storageName = step.storage === 'session' ? 'sessionStorage' : 'localStorage';
        const value = await page.evaluate(({ storage, key }) => {
          return window[storage].getItem(key);
        }, { storage: storageName, key: step.key || '' });
        if (step.non_empty && !String(value || '').trim()) {
          throw new Error(`expected non-empty ${storageName} value for key ${step.key}`);
        }
        if (step.equals !== undefined && String(value || '') !== String(step.equals)) {
          throw new Error(`expected ${storageName} value ${step.equals} for key ${step.key}`);
        }
        if (step.includes && !String(value || '').includes(step.includes)) {
          throw new Error(`expected ${storageName} value containing ${step.includes} for key ${step.key}`);
        }
      } else if (type === 'screenshot') {
        const suffix = (step.name || `step-${index + 1}`).replace(/[^a-z0-9-_]+/gi, '-').toLowerCase();
        const stepPath = screenshotPath.replace(/\.png$/i, `-${suffix}.png`);
        await page.screenshot({ path: stepPath, fullPage: true });
      } else if (type === 'wait') {
        await page.waitForTimeout(Number(step.timeout_ms || 500));
      } else {
        throw new Error(`unsupported flow step: ${type}`);
      }
    }

    if (flow && Array.isArray(flow.steps)) {
      for (let index = 0; index < flow.steps.length; index += 1) {
        const step = flow.steps[index];
        const startedAt = Date.now();
        try {
          await runFlowStep(step, index);
          flowResults.push({
            index,
            name: step.name || `step-${index + 1}`,
            type: step.type,
            ok: true,
            elapsed_ms: Date.now() - startedAt,
          });
        } catch (err) {
          flowResults.push({
            index,
            name: step.name || `step-${index + 1}`,
            type: step.type,
            ok: false,
            elapsed_ms: Date.now() - startedAt,
            error: String(err),
          });
          throw err;
        }
      }
    }

    await page.screenshot({ path: screenshotPath, fullPage: true });
    const interactiveSummary = await collectInteractiveSummary();
    const finalHtml = await page.content();
    const finalContentType = await page.evaluate(() => document.contentType || '');

    const payload = {
      ok: true,
      available: true,
      screenshot_path: screenshotPath,
      final_url: page.url(),
      final_title: interactiveSummary.title || '',
      final_html: finalHtml,
      final_content_type: finalContentType,
      final_status: finalDocumentStatus || (response ? response.status() : 0),
      status: response ? response.status() : 0,
      console_messages: consoleMessages,
      page_errors: pageErrors,
      failed_requests: failedRequests,
      response_errors: responseErrors,
      interactive_summary: interactiveSummary,
      interaction_checks: interactionChecks,
      flow_name: flow && flow.name ? flow.name : '',
      flow_results: flowResults,
      error: '',
    };
    fs.writeFileSync(resultPath, JSON.stringify(payload, null, 2));
  } catch (err) {
    let failureSummary = {};
    let failureHtml = '';
    let failureContentType = '';
    let failureTitle = '';
    let failureUrl = '';
    if (page) {
      try {
        failureUrl = page.url();
      } catch (innerErr) {}
      try {
        failureSummary = await collectInteractiveSummary();
        failureTitle = failureSummary.title || '';
      } catch (innerErr) {}
      try {
        failureHtml = await page.content();
      } catch (innerErr) {}
      try {
        failureContentType = await page.evaluate(() => document.contentType || '');
      } catch (innerErr) {}
      try {
        if (!fs.existsSync(screenshotPath)) {
          await page.screenshot({ path: screenshotPath, fullPage: true });
        }
      } catch (innerErr) {}
    }
    const payload = {
      ok: false,
      available: true,
      screenshot_path: fs.existsSync(screenshotPath) ? screenshotPath : '',
      final_url: failureUrl,
      final_title: failureTitle,
      final_html: failureHtml,
      final_content_type: failureContentType,
      final_status: finalDocumentStatus,
      console_messages: consoleMessages,
      page_errors: pageErrors,
      failed_requests: failedRequests,
      response_errors: responseErrors,
      interactive_summary: failureSummary,
      interaction_checks: interactionChecks,
      flow_name: flow && flow.name ? flow.name : '',
      flow_results: flowResults,
      error: String(err),
    };
    fs.writeFileSync(resultPath, JSON.stringify(payload, null, 2));
  } finally {
    if (browser) {
      await browser.close();
    }
  }
})();
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = Path(tmpdir) / "playwright_audit.js"
        result_path = Path(tmpdir) / "playwright_audit.json"
        flow_path = Path(tmpdir) / "live_eval_flow.json"
        script_path.write_text(script, encoding="utf-8")
        if flow_definition is not None:
            flow_path.write_text(json.dumps(flow_definition, ensure_ascii=True), encoding="utf-8")
        cmd = [
            "node",
            str(script_path),
            url,
            str(output_path),
            str(timeout_ms),
            str(result_path),
        ]
        if flow_definition is not None:
            cmd.append(str(flow_path))
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            cwd=runtime_root,
            env=_playwright_exec_env(runtime_root),
        )
        if result_path.exists():
            payload = json.loads(result_path.read_text(encoding="utf-8"))
        else:
            stderr = (result.stderr or result.stdout or "").strip()
            payload = {
                "ok": False,
                "available": True,
                "error": stderr or "playwright audit failed",
                "screenshot_path": "",
                "console_messages": [],
                "page_errors": [],
                "failed_requests": [],
                "response_errors": [],
                "interactive_summary": {},
                "interaction_checks": [],
                "flow_name": flow_definition.get("name", "") if flow_definition else "",
                "flow_results": [],
            }
        return payload


def _write_markdown_summary(
    path: Path,
    payload: dict[str, Any],
    screenshot_path: str,
    screenshot_error: str,
    browser_audit: dict[str, Any],
    command_checks: list[dict[str, Any]],
) -> None:
    body_excerpt = payload.get("body", "")[:1000].strip()
    console_messages = browser_audit.get("console_messages", [])
    page_errors = browser_audit.get("page_errors", [])
    failed_requests = browser_audit.get("failed_requests", [])
    response_errors = browser_audit.get("response_errors", [])
    summary = browser_audit.get("interactive_summary", {})
    interaction_checks = browser_audit.get("interaction_checks", [])
    flow_results = browser_audit.get("flow_results", [])
    flow_failed = [entry for entry in flow_results if not entry.get("ok")]
    command_failed = [entry for entry in command_checks if not entry.get("ok")]
    lines = [
        "# Live Evaluation",
        "",
        "## Request",
        f"- URL: {payload.get('url', '')}",
        f"- Status: {payload.get('status', 0)}",
        f"- Timestamp: {utc_now()}",
        "",
        "## Page Metadata",
        f"- Title: {payload.get('title', '') or '_No title found._'}",
        f"- Content-Type: {payload.get('headers', {}).get('Content-Type', '')}",
        "",
        "## Browser Evidence",
        f"- Screenshot: {screenshot_path or '_Not captured._'}",
        f"- Screenshot error: {screenshot_error or '_None._'}",
        f"- Browser audit error: {browser_audit.get('error', '') or '_None._'}",
        "",
        "## Browser Audit",
        f"- Console issues: {len(console_messages)}",
        f"- Page errors: {len(page_errors)}",
        f"- Failed requests: {len(failed_requests)}",
        f"- HTTP >=400 responses: {len(response_errors)}",
        f"- Headings: {summary.get('headingCount', 0)}",
        f"- Buttons: {summary.get('buttonCount', 0)}",
        f"- Links: {summary.get('linkCount', 0)}",
        f"- Forms: {summary.get('formCount', 0)}",
        f"- Inputs: {summary.get('inputCount', 0)}",
        "",
        "## Interaction Checks",
    ]
    if interaction_checks:
        for check in interaction_checks:
            status = "ok" if check.get("ok") else "failed"
            lines.append(f"- {check.get('target', 'unknown')}: {check.get('action', 'unknown')} ({status})")
    else:
        lines.append("- _No browser interaction checks ran._")
    lines.extend(
        [
            "",
            "## Flow Execution",
        ]
    )
    if flow_results:
        lines.append(f"- Flow name: {browser_audit.get('flow_name', '') or '_Unnamed flow_'}")
        lines.append(f"- Steps executed: {len(flow_results)}")
        lines.append(f"- Failed steps: {len(flow_failed)}")
        for entry in flow_results[:10]:
            status = "ok" if entry.get("ok") else "failed"
            details = f"{entry.get('name', entry.get('type', 'step'))}: {entry.get('type', 'unknown')} ({status})"
            if entry.get("error"):
                details += f" - {entry['error']}"
            lines.append(f"- {details}")
    else:
        lines.append("- _No flow steps were executed._")
    lines.extend(
        [
            "",
            "## Command Checks",
        ]
    )
    if command_checks:
        lines.append(f"- Checks executed: {len(command_checks)}")
        lines.append(f"- Failed checks: {len(command_failed)}")
        for entry in command_checks[:10]:
            status = "ok" if entry.get("ok") else "failed"
            details = f"{entry.get('name', 'command-check')}: exit {entry.get('exit_code', 0)} ({status})"
            if entry.get("stderr"):
                details += f" - stderr: {entry['stderr']}"
            lines.append(f"- {details}")
    else:
        lines.append("- _No command checks were executed._")
    lines.extend(
        [
            "",
            "## Browser Errors",
        ]
    )
    if console_messages or page_errors or failed_requests or response_errors:
        for entry in console_messages[:5]:
            lines.append(f"- Console {entry.get('type', 'log')}: {entry.get('text', '')}")
        for entry in page_errors[:5]:
            lines.append(f"- Page error: {entry}")
        for entry in failed_requests[:5]:
            lines.append(
                f"- Request failed: {entry.get('method', 'GET')} {entry.get('url', '')} ({entry.get('error', '')})"
            )
        for entry in response_errors[:5]:
            lines.append(f"- HTTP error: {entry.get('status', 0)} {entry.get('url', '')}")
    else:
        lines.append("- _No browser-side errors captured._")
    lines.extend(
        [
            "",
            "## HTML Excerpt",
            "```html",
            body_excerpt or "<empty>",
            "```",
            "",
        ]
    )
    write_text(path, "\n".join(lines))


def run_live_eval(
    session_ref: str | None,
    url: str | None,
    timeout: int,
    browser: str,
    flow_path: str | None,
) -> int:
    session_path, state = load_state(session_ref)
    target_url = url or state.get("qa_target_url")
    if not target_url:
        raise ValidationError("live-eval requires a URL or qa_target_url in session state")
    flow_definition, resolved_flow_path = _load_flow_definition(
        session_path,
        flow_path or state.get("qa_flow_path", ""),
    )
    if flow_definition and browser == "never":
        raise ValidationError("live-eval flow execution requires browser mode")

    artifact_dir = session_artifact_dir(session_path) / "live-eval"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    stamp = state.get("current_round", 0)
    artifact_base = _artifact_base_path(artifact_dir, int(stamp or 0))
    json_path = artifact_base.with_suffix(".json")
    md_path = artifact_base.with_suffix(".md")
    screenshot_path = artifact_base.with_suffix(".png")

    payload = _fetch_url(target_url, timeout)
    payload["title"] = _extract_title(payload.get("body", ""))

    screenshot_error = ""
    screenshot_rel = ""
    browser_audit: dict[str, Any] = {
        "ok": False,
        "available": False,
        "error": "browser audit skipped",
        "console_messages": [],
        "page_errors": [],
        "failed_requests": [],
        "response_errors": [],
        "interactive_summary": {},
        "interaction_checks": [],
    }
    if browser != "never":
        browser_audit = _run_playwright_audit(
            target_url,
            screenshot_path,
            timeout * 1000,
            flow_definition=flow_definition,
        )
        if flow_definition and not browser_audit.get("available", False):
            raise ValidationError("live-eval flow execution requires a Playwright runtime")
        screenshot_error = browser_audit.get("error", "")
        if browser_audit.get("screenshot_path") and screenshot_path.exists():
            screenshot_rel = str(screenshot_path.relative_to(session_path))
        elif screenshot_path.exists():
            screenshot_rel = str(screenshot_path.relative_to(session_path))
        else:
            captured, screenshot_error = _capture_screenshot(target_url, screenshot_path, timeout * 1000)
            if captured:
                screenshot_rel = str(screenshot_path.relative_to(session_path))

    final_url = str(browser_audit.get("final_url", "") or "").strip()
    final_title = str(browser_audit.get("final_title", "") or "").strip()
    final_html = browser_audit.get("final_html", "")
    final_content_type = str(browser_audit.get("final_content_type", "") or "").strip()
    final_status = browser_audit.get("final_status")
    if final_url:
        payload["url"] = final_url
    if final_title:
        payload["title"] = final_title
    if isinstance(final_html, str) and final_html.strip():
        payload["body"] = final_html
    if final_content_type:
        headers = dict(payload.get("headers", {}))
        headers["Content-Type"] = final_content_type
        payload["headers"] = headers
    if isinstance(final_status, int) and final_status > 0:
        payload["status"] = final_status

    command_checks = _run_command_checks(session_path, flow_definition)
    payload["browser_audit"] = browser_audit
    payload["command_checks"] = command_checks
    write_text(json_path, json.dumps(payload, indent=2, ensure_ascii=True) + "\n")
    _write_markdown_summary(
        md_path,
        payload,
        screenshot_rel,
        screenshot_error,
        browser_audit,
        command_checks,
    )

    state["last_live_eval_artifact"] = str(md_path.relative_to(session_path))
    state["last_evaluator_run"] = utc_now()
    if resolved_flow_path:
        state["qa_flow_path"] = str(Path(resolved_flow_path))
    write_state(session_path, state)
    append_event(
        event_path(session_path),
        {
            "ts": utc_now(),
            "type": "live_evaluation_ran",
            "url": target_url,
            "status": payload.get("status", 0),
            "artifact": state["last_live_eval_artifact"],
            "screenshot": screenshot_rel,
            "browser_audit_ok": browser_audit.get("ok", False),
            "flow_name": browser_audit.get("flow_name", ""),
            "flow_steps": len(browser_audit.get("flow_results", [])),
            "flow_failed_steps": len(
                [entry for entry in browser_audit.get("flow_results", []) if not entry.get("ok")]
            ),
            "command_checks": len(command_checks),
            "command_failed_checks": len([entry for entry in command_checks if not entry.get("ok")]),
            "browser_error_count": len(browser_audit.get("console_messages", []))
            + len(browser_audit.get("page_errors", []))
            + len(browser_audit.get("failed_requests", []))
            + len(browser_audit.get("response_errors", [])),
        },
    )
    validate_session_bundle(session_path, state)
    if flow_definition:
        failed_steps = [
            entry for entry in browser_audit.get("flow_results", [])
            if not entry.get("ok")
        ]
        failed_checks = [entry for entry in command_checks if not entry.get("ok")]
        if not browser_audit.get("ok", False) or failed_steps or failed_checks:
            raise ValidationError(
                "live-eval flow failed with "
                f"{len(failed_steps)} failing browser step(s) and {len(failed_checks)} failing command check(s)"
            )
    print(state["last_live_eval_artifact"])
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Harness Design Kit live evaluation helper")
    parser.add_argument("--session", help="Session id or path. Defaults to current session.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    run_parser = subparsers.add_parser("run")
    run_parser.add_argument("--url", help="URL to evaluate. Defaults to qa_target_url in session state.")
    run_parser.add_argument("--timeout", type=int, default=10, help="HTTP timeout in seconds.")
    run_parser.add_argument(
        "--browser",
        choices=["auto", "never"],
        default="auto",
        help="Whether to attempt a browser screenshot with Playwright.",
    )
    run_parser.add_argument(
        "--flow",
        help="Optional JSON file describing a browser flow to execute.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "run":
            return run_live_eval(args.session, args.url, args.timeout, args.browser, args.flow)
    except (FileNotFoundError, ValidationError) as exc:
        print(str(exc))
        return 1
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
