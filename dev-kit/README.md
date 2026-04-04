# Dev Kit

Plugin for Claude Code and OpenAI Codex providing disciplined development workflows.

## Installation

### Claude Code

```bash
claude --plugin-dir ./dev-kit
```

Or copy the `dev-kit/` directory to your project. The plugin is discovered via `.claude-plugin/plugin.json`.

### OpenAI Codex

Copy the `dev-kit/` directory into your project. The plugin is discovered via `.codex-plugin/plugin.json`.

## Quick Start

Dev Kit provides 11 skills organized into three categories. Start with the workflow that matches your task size:

| Task Size | Workflow | Skills |
|---|---|---|
| Simple change (1-3 files) | `write-surgically` | Make surgical edits directly |
| Medium task (clear scope) | `clarify-requirements` → `craft-plan` → `execute-plan` → `verify-implementation` | Plan pipeline |
| Large project | `clarify-requirements` → `decompose-milestones` → `orchestrate-execution` | Milestone pipeline |

### Common Prompts

```
"Help me clarify this vague request into a well-scoped brief."
"Write an executable implementation plan for this task."
"Run this implementation plan and validate each task independently."
"Review the implementation against the plan and give me a PASS/FAIL verdict."
"Break this project into milestones with dependency ordering."
"Execute all milestones with checkpoints and recovery."
"Implement this change surgically — minimum edits, no scope creep."
"Simplify the changed code for reuse, quality, and efficiency."
"Clean up the AI-generated code smells without changing behavior."
"Debug this failing test using a reproduce-first workflow."
"Find out where this code is actually slow before optimizing."
```

## Included Skills

### Workflow

- `clarify-requirements`: narrow vague requests into a saved context brief with complexity routing
- `craft-plan`: write executable implementation plans with explicit verification
- `execute-plan`: execute plans through worker-validator loops
- `verify-implementation`: independently verify implementation against the plan
- `decompose-milestones`: break large projects into milestone DAGs with parallel review
- `orchestrate-execution`: orchestrate multi-milestone execution with checkpoints and recovery

### Guardrails And Cleanup

- `write-surgically`: implementation discipline for scoped, verified code changes
- `remove-slop`: post-generation cleanup for AI-shaped code smells
- `simplify-changes`: diff-based quality, reuse, and efficiency review with direct fixes

### Debugging And Performance

- `debug-systematically`: reproduce-first, root-cause-first debugging workflow
- `measure-performance`: measurement-first optimization guardrails

## How Skills Connect

```
clarify-requirements
  ├── Simple  → craft-plan → execute-plan → verify-implementation
  └── Complex → decompose-milestones → orchestrate-execution

Guardrails (apply anytime):
  write-surgically    — during implementation
  remove-slop         — after AI generation
  simplify-changes    — after any changes

Diagnostics (on demand):
  debug-systematically  — on bugs/failures
  measure-performance   — on performance concerns
```

Planning artifacts are saved under `docs/dev-kit/`.

## Structure

- `.claude-plugin/plugin.json`: Claude Code plugin manifest
- `.codex-plugin/plugin.json`: Codex plugin manifest
- `skills/`: bundled workflow and discipline skills (shared by both platforms)
- `hooks/hooks.json`: hook definitions
- `scripts/`: local helper scripts
- `assets/`: icons, logos, screenshots
- `.app.json`: app or connector mappings
- `.mcp.json`: MCP server mappings

## Notes

- `debug-systematically/` includes supporting reference material and helper scripts
- `decompose-milestones` and `orchestrate-execution` extend the core plan/execute/review pipeline for larger work
