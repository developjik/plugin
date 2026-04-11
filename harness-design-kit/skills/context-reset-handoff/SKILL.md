---
name: context-reset-handoff
description: Decide when compaction is no longer enough, write a clean handoff artifact, and resume long-running work from a fresh context.
---

# Context Reset Handoff

Use this skill when a long task starts losing coherence and a clean-slate restart is more reliable than staying in the same context window.

## Compaction Vs Reset

- `compaction`
  - shorten history while staying in the same session
  - good when the work is still coherent and the agent mainly needs less transcript weight
- `context reset`
  - start a fresh agent with a structured handoff
  - good when the agent is forgetting constraints, wrapping up too early, or repeating mistakes

If the current session is in `execution_mode=auto`, this skill is the promotion path from compaction-first execution to explicit reset mode.

## Reset Signals

Prefer a reset when you see several of these at once:

- context anxiety or premature wrap-up behavior
- repeated forgetting of accepted constraints
- contradictions between recent decisions and current implementation
- rising noise from old conversation history
- handoff artifacts are clearer than more conversation

## Handoff Minimum

Write `handoff.md` with:

- current goal
- chosen harness mode and why
- accepted product spec summary
- latest sprint contract
- completed work
- failing checks or unresolved bugs
- exact next steps
- commands, files, or URLs needed to resume

## State Updates

- set `phase` to `handoff`
- update `updated_at`
- append a reset event to `events.jsonl`

The runtime helper can do this directly:

```bash
python3 "${PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT:-.}}/scripts/harness_state.py" prepare-reset "reason"
```

Then resume with a fresh agent that reads `state.json`, `product-spec.md`, `sprint-contract.md`, `evaluation.md`, `progress.md`, and `handoff.md` before continuing.
