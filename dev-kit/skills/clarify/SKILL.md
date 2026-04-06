---
name: clarify
description: Use when a user's request is vague, ambiguous, or underspecified. Produces a Context Brief, scores complexity, and initializes `.dev-kit/` session state for the unified clarify -> planning -> execute -> review workflow.
---

# Clarification Through Iterative Discovery

Narrows vague requests into a decision-ready work scope. Clarify does not choose between different workflows. It always prepares the canonical handoff to `planning`.

## Core Principle

Clarify exists to remove ambiguity, not to start implementation. Its output is a Context Brief plus execution-profile guidance that planning can act on without reopening basic product questions.

## Hard Gates

1. **One question per message.** Never bundle multiple user questions into one turn.
2. **Always explore in parallel.** While asking the user about intent, inspect the codebase to ground scope in repo reality.
3. **Do not implement.** Clarify ends at a saved brief and updated session state.
4. **Every question must narrow scope.** Ask only questions that change the brief or lock an assumption.
5. **Complexity does not route.** Clarify may score complexity, but the next skill is always `planning`.

## Session Initialization

Clarify creates a new session directory for each task under the workspace root:

```text
.dev-kit/sessions/<session-id>/
```

**Session ID format:** `YYYY-MM-DDTHH-MM-<slug>`

- Use current date and time when clarify starts
- Derive `<slug>` from the user's request topic: lowercase, hyphenated, max 3 words

Write `.dev-kit/current.json`:

```json
{
  "schema_version": 1,
  "session_id": "<session-id>",
  "session_path": ".dev-kit/sessions/<session-id>",
  "updated_at": "YYYY-MM-DDTHH:MM:SS+TZ"
}
```

Write `.dev-kit/sessions/<session-id>/state.json`:

```json
{
  "schema_version": 1,
  "session_id": "<session-id>",
  "title": "[Topic Title]",
  "feature_slug": "<slug>",
  "status": "in_progress",
  "current_phase": "clarify",
  "execution_profile": null,
  "plan_status": "not_started",
  "plan_version": 0,
  "next_action": "Complete clarify and write brief.md.",
  "artifacts": {
    "brief": null,
    "plan": null,
    "plan_review": null,
    "review": null
  },
  "phase_status": {},
  "created_at": "YYYY-MM-DDTHH:MM:SS+TZ",
  "updated_at": "YYYY-MM-DDTHH:MM:SS+TZ"
}
```

All paths stored in JSON must be relative to the workspace root.

## When To Use

- The request is vague enough that implementation could go in multiple directions
- The user wants a new feature but scope, success criteria, or constraints are not yet concrete
- Existing codebase structure may materially affect the design

## When NOT To Use

- The work scope is already concrete and bounded
- The user explicitly says to skip clarification

## Two-Track Process

### Track 1: User Q&A

Ask questions that narrow:

1. Purpose
2. Scope boundaries
3. Constraints
4. Success criteria
5. Priority and tradeoffs

After each answer, summarize what changed in the brief.

### Track 2: Codebase Exploration

Inspect the repo in parallel to discover:

- Relevant entry points and modules
- Existing interfaces that constrain the design
- Likely file impact
- Verification options already present in the project
- Existing patterns the plan should preserve

Summarize only the parts that matter to the user's decision.

## Context Brief Template

Save the final brief to:

```text
.dev-kit/sessions/<session-id>/brief.md
```

Use this structure:

```markdown
# Context Brief: [Task Title]

## Goal
[One paragraph describing what the user wants]

## Scope
- **In scope:** [Included work]
- **Out of scope:** [Explicitly excluded work]

## Technical Context
[Relevant codebase findings, system boundaries, likely files, constraints]

## Constraints
- [Compatibility, deadlines, risk, dependency, rollout, product constraints]

## Success Criteria
- [Concrete, verifiable outcomes]

## Open Questions
- [Only unresolved but non-blocking items]

## Complexity Assessment

| Signal | Low (1) | Medium (2) | High (3) |
|--------|---------|-----------|----------|
| Scope breadth | Single feature or component | 2-3 related components | 4+ components or cross-cutting concerns |
| File impact | <=3 files | 4-8 files | 9+ files or 3+ directories |
| Interface boundaries | Works within existing interfaces | Extends existing interfaces | Defines or reshapes contracts |
| Dependency depth | No ordering constraints | Mostly linear ordering | Branching dependencies or phase boundaries |
| Risk surface | Low integration risk | Internal integration risk | External systems, schema, compatibility, or migration risk |

**Complexity Score:** [5-15]
**Execution Profile:** [low | medium | high]
**Recommended Split:** [none | task | phased]
**Recommended Isolation:** [inline | parallel-subagents | worktree-eligible]
**Risk Notes:** [1-3 sentences]

## Suggested Next Step
Run `planning`. Read `.dev-kit/sessions/<session-id>/brief.md`.
```

## Complexity Assessment Rules

Score the 5 signals, then map them to the execution profile:

- **Low**: score 5-7
  - recommended split: `none`
  - recommended isolation: `inline`
- **Medium**: score 8-10
  - recommended split: `task`
  - recommended isolation: `parallel-subagents`
- **High**: score 11-15
  - recommended split: `phased`
  - recommended isolation: `worktree-eligible`
  - note explicitly that worktree use still depends on planning confirming disjoint write sets

## State Update

Present the Context Brief to the user first. Once approved, save `brief.md` and update `state.json`:

- set `execution_profile` from the Complexity Assessment
- keep `plan_status` as `not_started`
- keep `plan_version` as `0`
- set `current_phase` to `planning`
- keep `status` as `in_progress`
- set `next_action` to `Run planning. Read .dev-kit/sessions/<session-id>/brief.md.`
- set `artifacts.brief` to `.dev-kit/sessions/<session-id>/brief.md`
- update `updated_at`

Also refresh `.dev-kit/current.json` so it still points to the same session with a new `updated_at` timestamp.

## Anti-Patterns

| Anti-Pattern | Why It Fails |
|---|---|
| Routing to different skills based on complexity | The visible workflow must stay fixed |
| Asking broad questions without exploration | Misses repo constraints and causes rework |
| Dumping raw exploration output | Too noisy; the user needs interpreted findings |
| Starting implementation from clarify | Breaks the stage boundary and weakens planning |

## Minimal Checklist

- [ ] Is the user goal concrete?
- [ ] Are scope boundaries explicit?
- [ ] Are technical constraints grounded in repo findings?
- [ ] Is the complexity assessment complete?
- [ ] Does the brief hand off cleanly to planning?

## Transition

Once the Context Brief is approved and saved:

- proceed to `planning`

This skill does not invoke the next skill itself. It saves the brief, updates `.dev-kit/` state, and points the session to `planning`.
