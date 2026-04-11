# Harness Design Kit

English | [한국어](./README.ko.md)

Harness Design Kit packages the core workflow ideas from Anthropic's March 24, 2026 engineering article, [Harness design for long-running application development](https://www.anthropic.com/engineering/harness-design-long-running-apps), into a local plugin for Codex and Claude Code.

It now ships a lightweight local runtime for the workflow layer:

- planner, generator, and evaluator role separation
- sprint contracts before implementation
- a `continuous` profile for build-then-final-pass workflows
- frontend generator-evaluator loops with explicit scoring
- machine-readable evaluation score capture with threshold enforcement
- weighted frontend evaluation summaries with enforced priority weights
- file-based handoffs for long work
- explicit reset-vs-compaction decisions
- evaluator policy modes such as `always`, `final-pass`, `edge-only`, and `off`
- phase transitions, event logs, handoff generation, and auto-reset promotion
- compaction checkpoints for continuous sessions before reset escalation
- a runner-driven orchestrator that can execute planner, generator, evaluator, and compactor steps through native OpenAI or Anthropic providers, or through an external command
- same-session compact resume that rewrites `compact-state.md` with a dedicated compactor actor before escalating to reset
- frontend candidate tracking with automatic refine, pivot, and accept loops
- evaluator calibration anchors injected into evaluator prompts
- Playwright MCP wiring plus a local live evaluation helper with browser audit output, optional scripted flows, and command checks backed by a cached local Playwright runtime

It does not claim to be a hosted harness platform. There is no remote resume service, sandbox pool, or credential vault in this plugin.

## Included Components

- `skills/harness-orchestrator/`
  - main long-running application workflow
- `skills/frontend-design-loop/`
  - design-specific generator-evaluator loop
- `skills/evaluator-calibration/`
  - improve evaluator strictness and consistency
- `skills/context-reset-handoff/`
  - structured reset workflow for degraded long sessions
- `agents/`
  - planner, generator, compactor, design-evaluator, and qa-evaluator prompts
- `scripts/harness_state.py`
  - local session state engine, validator, and handoff writer
- `scripts/harness_run.py`
  - runtime helper for phase advancement and auto-reset checks
- `scripts/harness_orchestrator.py`
  - native-or-external executor for planner, generator, compactor, and evaluator steps
- `scripts/harness_runner.py`
  - native provider adapters for OpenAI Responses and Anthropic Messages, plus the external runner bridge
- `scripts/live_eval.py`
  - live QA helper that fetches a target URL and captures Playwright screenshots when available
- `schema/`
  - session plus artifact contract schemas
- `templates/`
  - structured artifact templates for new sessions
- `fixtures/`
  - evaluator calibration examples
- `hooks/`
  - event and reset-aware session hooks

## Local State

The plugin stores workflow state under the workspace root:

```text
.harness-design-kit/
├── current.json
└── sessions/
    └── <session-id>/
        ├── state.json
        ├── events.jsonl
        ├── product-spec.md
        ├── design-brief.md
        ├── sprint-contract.md
        ├── evaluation.md
        ├── progress.md
        ├── compact-state.md
        └── handoff.md
```

## When To Use It

Use Harness Design Kit when:

- a short prompt needs to become a real product spec and multi-step build
- subjective quality matters, especially for frontend work
- one-shot generation is too weak or too inconsistent
- you need an explicit handoff structure for long tasks

Use a simpler workflow when the task is small, deterministic, and easy to verify directly.

## Quick Start

Set `PLUGIN_ROOT` to the installed plugin directory when you are outside this repository. Inside this repository, the examples below default to `./harness-design-kit`.

1. Initialize a session:

   ```bash
   python3 "${PLUGIN_ROOT:-./harness-design-kit}/scripts/harness_state.py" init "Build a browser-based DAW" app
   ```

2. Inspect the next actor and current phase:

   ```bash
   python3 "${PLUGIN_ROOT:-./harness-design-kit}/scripts/harness_run.py" status
   ```

   Or run an environment and session check:

   ```bash
   python3 "${PLUGIN_ROOT:-./harness-design-kit}/scripts/harness_state.py" doctor
   ```

3. Run the main workflow:

   ```text
   Use Harness Design Kit. Start harness-orchestrator for this app idea.
   ```

4. Advance the recorded phase after the current gate is satisfied:

   ```bash
   python3 "${PLUGIN_ROOT:-./harness-design-kit}/scripts/harness_run.py" advance
   ```

   In `final-pass` mode, request the evaluator gate before advancing out of `build`:

   ```bash
   python3 "${PLUGIN_ROOT:-./harness-design-kit}/scripts/harness_state.py" request-final-pass "ready for final QA"
   ```

5. When an app contract draft is ready, propose it for evaluator review:

   ```bash
   python3 "${PLUGIN_ROOT:-./harness-design-kit}/scripts/harness_state.py" propose-contract generator
   ```

6. For frontend-only work:

   ```text
   Use frontend-design-loop for this landing page.
   ```

7. If the task starts drifting:

   ```text
   Use context-reset-handoff and prepare a clean resume artifact.
   ```

8. Or trigger a reset artifact directly:

   ```bash
   python3 "${PLUGIN_ROOT:-./harness-design-kit}/scripts/harness_state.py" prepare-reset "repeated evaluator failures"
   ```

   Or capture a same-session compaction checkpoint before escalating to reset:

   ```bash
   python3 "${PLUGIN_ROOT:-./harness-design-kit}/scripts/harness_state.py" prepare-compaction "conversation drifted but should stay in the same session"
   ```

9. Run live QA against the current app URL:

   ```bash
   python3 "${PLUGIN_ROOT:-./harness-design-kit}/scripts/live_eval.py" run --url http://localhost:3000
   ```

   To execute a reusable browser flow as part of QA:

   ```bash
   python3 "${PLUGIN_ROOT:-./harness-design-kit}/scripts/harness_state.py" set-qa-flow "${PLUGIN_ROOT:-./harness-design-kit}/templates/qa-flow.json"
   python3 "${PLUGIN_ROOT:-./harness-design-kit}/scripts/live_eval.py" run --url http://localhost:3000 --flow "${PLUGIN_ROOT:-./harness-design-kit}/templates/qa-flow.json"
   ```

10. Resume a paused handoff in a fresh child session:

   ```bash
   python3 "${PLUGIN_ROOT:-./harness-design-kit}/scripts/harness_state.py" resume-from-handoff "fresh context resume"
   ```

11. Configure a native provider and run the orchestrator:

   ```bash
   export HARNESS_DESIGN_KIT_PROVIDER=openai
   export OPENAI_API_KEY=...
   python3 "${PLUGIN_ROOT:-./harness-design-kit}/scripts/harness_orchestrator.py" run-loop --max-steps 8
   ```

   Or use Anthropic:

   ```bash
   export HARNESS_DESIGN_KIT_PROVIDER=anthropic
   export ANTHROPIC_API_KEY=...
   python3 "${PLUGIN_ROOT:-./harness-design-kit}/scripts/harness_orchestrator.py" run-loop --max-steps 8
   ```

12. Or force the external runner path:

   ```bash
   export HARNESS_DESIGN_KIT_PROVIDER=external
   export HARNESS_DESIGN_KIT_AGENT_RUNNER='python3 /absolute/path/to/runner.py'
   python3 "${PLUGIN_ROOT:-./harness-design-kit}/scripts/harness_orchestrator.py" run-loop --max-steps 8
   ```

## Native Runner Configuration

- `HARNESS_DESIGN_KIT_PROVIDER`
  - `openai`, `anthropic`, or `external`
- `HARNESS_DESIGN_KIT_MODEL`
  - shared fallback model for all actors
- `HARNESS_DESIGN_KIT_MODEL_PLANNER`
  - planner-specific override
- `HARNESS_DESIGN_KIT_MODEL_GENERATOR`
  - generator-specific override
- `HARNESS_DESIGN_KIT_MODEL_EVALUATOR`
  - evaluator-specific override
- `HARNESS_DESIGN_KIT_COMPACTION_MODEL`
  - compactor-specific override; defaults to the evaluator model
- `HARNESS_DESIGN_KIT_OPENAI_BASE_URL`
  - optional custom base URL for OpenAI-compatible gateways
- `HARNESS_DESIGN_KIT_AGENT_RUNNER`
  - required only when `HARNESS_DESIGN_KIT_PROVIDER=external`

## Installation

- [Codex Local Plugin Install Guide](../docs/guides/install/codex-local-plugin-install.md)
- [Claude Code Local Plugin Install Guide](../docs/guides/install/claude-code-local-plugin-install.md)

After installing, available entry points include:

- `/harness-design-kit:help`
- `harness-orchestrator`
- `frontend-design-loop`
- `evaluator-calibration`
- `context-reset-handoff`
