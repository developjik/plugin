# Dev Kit

Structured development workflow plugin for Claude Code and Codex — clarify, plan, execute, review-execute, debug.

## Overview

Dev Kit provides 12 skills covering the full development lifecycle. Each skill enforces strict Hard Gates to prevent common LLM coding mistakes, and uses information-isolated Worker-Validator patterns for independent verification.

## Workflow

```
                          ┌───────────────────────────────────────────────┐
                          │            Simple (complexity score 5-7)       │
                          │                                               │
                          │  clarify → planning → execute → review-execute│
                          │                                               │
   clarify ──routing──────┤                                               │
   (complexity score)     │         Borderline (complexity score 8-9)     │
                          │                                               │
                          │  User choice: planning or milestone-planning  │
                          │                                               │
                          ├───────────────────────────────────────────────┤
                          │           Complex (complexity score 10-15)    │
                          │                                               │
                          │  clarify → milestone-planning → long-execute  │
                          │              (per milestone:                  │
                          │               planning → execute              │
                          │              → review-execute)                │
                          └───────────────────────────────────────────────┘

  resume ──→ scans docs/sessions/ for in-progress work and dispatches to the correct skill

  Quality skills (user-invoked, not auto-triggered by the pipeline):
    karpathy          ──→ "during implementation" — surgical change discipline
    rob-pike          ──→ "optimize", "slow", "performance" — measurement-driven optimization
    clean-ai-slop     ──→ "clean up", "deslop" — AI-specific code smell removal (6 passes)
    simplify-code     ──→ "simplify", "review the changes" — parallel reuse/quality/efficiency review
    systematic-debugging ──→ bug, test failure, unexpected behavior — 7-phase root-cause workflow
```

> **Note:** Quality skills are standalone disciplines. They are not automatically invoked by the core pipeline. Other skills may *suggest* them as next steps, but the user decides whether to invoke them.

## Skills

### Core Pipeline

| Skill | Trigger | Description |
|---|---|---|
| **clarify** | "I want to...", "I need...", "let's build...", "can you help me...", "we should...", or any vague/underspecified request | Iterative Q&A + parallel codebase exploration to produce a Context Brief. Scores complexity on 5 signals and routes to simple or complex pipeline. |
| **planning** | After clarify completes, or explicit plan request with a clear prompt | Writes an executable plan document with worker-validator task pairs, verification strategy, and dependency ordering |
| **execute** | "run the plan", "execute the plan", "let's start implementing" | Loads plan, executes tasks in dependency order with Worker-Validator subagent loop. Parallelizable tasks run concurrently. |
| **review-execute** | "review the work", "verify the implementation", "check if the plan was executed correctly" | Information-isolated reviewer — reads only the plan document, inspects codebase from scratch, produces PASS/FAIL verdict |
| **resume** | "resume", "continue", "이어서", "아까 하던 거", "진행 중인 작업", "이전 작업", "다시 시작" | Scans `docs/sessions/` for in-progress work and dispatches to the correct skill based on `state.md` |

### Complex Workflow

| Skill | Trigger | Description |
|---|---|---|
| **milestone-planning** | "plan milestones", "break this into milestones", "ultraplan" | 5 parallel reviewer agents (Feasibility, Architecture, Risk, Dependency, User Value) decompose tasks into a milestone DAG with measurable success criteria |
| **long-execute** | "long run", "start long run", "execute milestones", "run all milestones" | Orchestrates multi-milestone execution with checkpoint/recovery. Each milestone runs planning → execute → review-execute. |

### Debugging

| Skill | Trigger | Description |
|---|---|---|
| **systematic-debugging** | Bug, test failure, unexpected behavior | 7-phase workflow: Define → Reproduce → Evidence → Isolate → Lock → Fix → Verify. Hard Gates block guess-based fixes. Includes supplementary guides for flaky tests, root-cause tracing, and defense-in-depth validation. |

### Code Quality

| Skill | Trigger | Description |
|---|---|---|
| **karpathy** | "implement...", "modify code...", or when you notice yourself about to make changes without reading the existing code first | 5 rules for surgical implementation: read before write, scope to request, verify assumptions, define success criteria, don't solve problems that don't exist |
| **rob-pike** | "optimize", "slow", "performance", "bottleneck", "speed up", "make faster", "too slow" | Rob Pike's 5 Rules — prevents premature optimization, enforces measurement-driven development. Scans for existing instrumentation before suggesting profiling. |
| **clean-ai-slop** | "clean up", "deslop", "slop", "clean AI code" | 6-pass cleanup of AI-specific code smells: dead code, over-commenting, unnecessary abstractions, defensive paranoia, verbose naming, LLM filler |
| **simplify-code** | "simplify", "clean up the code", "review the changes" | 3 parallel agents (Reuse, Quality, Efficiency) review diffs and fix issues directly |

## Key Design Principles

**Hard Gates** — Every skill defines exception-free rules. Violating a gate constitutes a process failure.

**Worker-Validator Isolation** — Validators use fixed prompt templates, receive no execution context, and produce binary verdicts. This prevents confirmation bias.

**Session State on Disk** — All state lives in `docs/sessions/<id>/` (state.md, brief.md, plan.md, reviews/, checkpoints/). Survives context window compression.

**Complexity-Based Routing** — `clarify` scores requests on 5 signals (scope breadth, file impact, interface boundaries, dependency depth, risk surface) and routes to simple or complex pipeline.

## Installation

```bash
# Clone or copy into your project's plugin directory
# Claude Code: add to .claude/plugins/ or reference in settings
# Codex: add to the configured plugins path
```

## Quick Start

```
"Clarify this task and create a plan for implementation."
"Debug this failing test with systematic root-cause analysis."
"Review and simplify the changed code for quality issues."
"Break this complex feature into milestones and execute them."
```

## Project Structure

```
dev-kit/
├── .claude-plugin/plugin.json          # Claude Code metadata
├── .codex-plugin/plugin.json           # Codex metadata
├── .mcp.json                           # MCP server configs (empty)
├── .app.json                           # App integrations (empty)
├── hooks/hooks.json                    # Lifecycle hooks (empty)
├── README.md
├── assets/
│   ├── icon.png                        # 256x256 plugin icon
│   └── logo.png                        # 512x256 plugin logo
├── scripts/                            # Utility scripts (reserved)
└── skills/
    ├── clarify/SKILL.md
    ├── planning/SKILL.md
    ├── execute/SKILL.md
    ├── review-execute/SKILL.md
    ├── resume/SKILL.md
    ├── milestone-planning/SKILL.md
    ├── long-execute/SKILL.md
    ├── systematic-debugging/
    │   ├── SKILL.md
    │   ├── condition-based-waiting.md          # Flaky test guide
    │   ├── condition-based-waiting-example.ts   # Polling utilities
    │   ├── defense-in-depth.md                 # Multi-layer validation
    │   ├── root-cause-tracing.md               # Call-chain tracing guide
    │   └── find-polluter.sh                    # Test pollution bisection script
    ├── karpathy/SKILL.md
    ├── rob-pike/SKILL.md
    ├── clean-ai-slop/SKILL.md
    └── simplify-code/SKILL.md
```

## License

MIT
