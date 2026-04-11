# Harness Design Kit Help

Harness Design Kit packages the core patterns from Anthropic's long-running application harness article into a local plugin workflow.

The current plugin now includes a lightweight local runtime for:

- session initialization and validation
- session listing, pointer selection, handoff resume, and environment doctor checks
- phase transitions
- round tracking
- event logging
- handoff generation
- compaction checkpoint generation
- same-session compact resume through a dedicated compactor actor before reset
- auto-reset promotion based on repeated failure signals
- evaluator evidence checks with scored threshold enforcement and weighted frontend summaries
- live QA snapshots using HTTP fetch, browser audit data, optional Playwright screenshots, reusable flow scripts, and command checks
- runner-driven orchestration for planner, generator, compactor, and evaluator steps with native OpenAI/Anthropic providers or an external runner

## Entry Points

- `harness-orchestrator`
  - main planner-generator-evaluator build loop for long-running app work, using native providers or an external runner
- `frontend-design-loop`
  - design-focused generator-evaluator loop with explicit scoring
- `evaluator-calibration`
  - tighten or rebalance evaluator criteria when the evaluator is too lenient
- `context-reset-handoff`
  - create a structured reset artifact when compaction is no longer enough

## Agent Roles

- `planner`
  - expands a short prompt into a product spec and sprint outline
- `generator`
  - implements the active sprint contract and records evidence
- `compactor`
  - rewrites compact-state.md into accepted facts, failing evidence, and one exact next step
- `design-evaluator`
  - grades frontend work on design quality, originality, craft, and functionality
- `qa-evaluator`
  - tests the running app and gates each sprint on quality thresholds

## Session Files

Harness Design Kit keeps local state under:

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

To initialize a session manually:

```bash
python3 "${PLUGIN_ROOT:-.}/scripts/harness_state.py" init "<goal>" [app|frontend]
```

Useful runtime commands:

```bash
python3 "${PLUGIN_ROOT:-.}/scripts/harness_state.py" summary
python3 "${PLUGIN_ROOT:-.}/scripts/harness_state.py" validate
python3 "${PLUGIN_ROOT:-.}/scripts/harness_state.py" doctor
python3 "${PLUGIN_ROOT:-.}/scripts/harness_state.py" list-sessions
python3 "${PLUGIN_ROOT:-.}/scripts/harness_state.py" select-session <session-id>
python3 "${PLUGIN_ROOT:-.}/scripts/harness_state.py" start-round [candidate-id]
python3 "${PLUGIN_ROOT:-.}/scripts/harness_state.py" finish-round <refine|pivot|accept> [candidate-id]
python3 "${PLUGIN_ROOT:-.}/scripts/harness_state.py" propose-contract [proposed-by]
python3 "${PLUGIN_ROOT:-.}/scripts/harness_state.py" record-evaluation <pass|fail|revise|pivot> [evaluator]
python3 "${PLUGIN_ROOT:-.}/scripts/harness_state.py" request-evaluation "reason"
python3 "${PLUGIN_ROOT:-.}/scripts/harness_state.py" request-final-pass "reason"
python3 "${PLUGIN_ROOT:-.}/scripts/harness_state.py" prepare-compaction "reason"
python3 "${PLUGIN_ROOT:-.}/scripts/harness_state.py" prepare-reset "reason"
python3 "${PLUGIN_ROOT:-.}/scripts/harness_state.py" resume-from-handoff "reason"
python3 "${PLUGIN_ROOT:-.}/scripts/harness_state.py" set-qa-flow "${PLUGIN_ROOT:-.}/templates/qa-flow.json"
python3 "${PLUGIN_ROOT:-.}/scripts/harness_run.py" status
python3 "${PLUGIN_ROOT:-.}/scripts/harness_run.py" advance
python3 "${PLUGIN_ROOT:-.}/scripts/harness_run.py" check-reset
python3 "${PLUGIN_ROOT:-.}/scripts/harness_orchestrator.py" run-once
python3 "${PLUGIN_ROOT:-.}/scripts/harness_orchestrator.py" run-loop --max-steps 8
python3 "${PLUGIN_ROOT:-.}/scripts/live_eval.py" run --url http://localhost:3000 --flow "${PLUGIN_ROOT:-.}/templates/qa-flow.json"
```

Native runner env:

```bash
export HARNESS_DESIGN_KIT_PROVIDER=openai   # or anthropic or external
export HARNESS_DESIGN_KIT_MODEL=gpt-5.4
export HARNESS_DESIGN_KIT_MODEL_PLANNER=gpt-5.4
export HARNESS_DESIGN_KIT_MODEL_GENERATOR=gpt-5.4
export HARNESS_DESIGN_KIT_MODEL_EVALUATOR=gpt-5.4
export HARNESS_DESIGN_KIT_COMPACTION_MODEL=gpt-5.4-mini
export HARNESS_DESIGN_KIT_OPENAI_BASE_URL=https://api.openai.com/v1
export HARNESS_DESIGN_KIT_AGENT_RUNNER='python3 /absolute/path/to/runner.py'  # external only
```
