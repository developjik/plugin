---
name: clarify
description: Mandatory entry phase when explicitly starting a new Dev Kit task. Produces a Context Brief, scores complexity, and initializes `.dev-kit/` session state for the unified clarify -> planning -> execute -> review-execute workflow. Already-clear work may use direct clarify instead of a longer question loop.
---

# Clarification Through Iterative Discovery

Turns every new task into a decision-ready work scope. Clarify does not choose between different workflows and it is never skipped. It always prepares the canonical handoff to `planning`.

## Core Principle

Clarify is the mandatory entry phase once a user explicitly starts a new Dev Kit task. When ambiguity is high, it runs as an interactive discovery loop. When the request is already concrete, it runs as direct clarify: confirm the scope from repo reality, lock a concise brief, and move on without unnecessary questions. Its output is always a Context Brief plus execution-profile guidance that planning can act on without reopening basic product questions.

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
    "review": null,
    "compound": null
  },
  "phase_status": {},
  "created_at": "YYYY-MM-DDTHH:MM:SS+TZ",
  "updated_at": "YYYY-MM-DDTHH:MM:SS+TZ"
}
```

All paths stored in JSON must be relative to the workspace root.

## When To Use

- When explicitly starting a new Dev Kit task
- When the request is vague enough that implementation could go in multiple directions
- When the user wants a new feature but scope, success criteria, or constraints are not yet concrete
- When the request already looks concrete but the brief and execution profile have not been materialized yet

## When NOT To Use

- When resuming a session that has already completed clarify and is now inside `planning`, `execute`, or `review-execute`
- When replacing or revising a plan inside an already-active planning session without changing the upstream task brief

## Two-Track Process

### Track 1: User Q&A

Ask questions that narrow:

1. Purpose
2. Scope boundaries
3. Constraints
4. Success criteria
5. Priority and tradeoffs

If the request is already concrete, use direct clarify: ask zero or one narrowing question only when needed, then summarize the locked scope and move on. After each answer, summarize what changed in the brief.

### Track 2: Codebase Exploration

Inspect the repo in parallel to discover:

- Relevant entry points and modules
- Existing interfaces that constrain the design
- Likely file impact
- Verification options already present in the project
- Existing patterns the plan should preserve

Summarize only the parts that matter to the user's decision.

### Track 3: Compound Learning Reference

If compound learnings are available (injected via session-start hook in the `## Compound Learnings` context block):

1. Scan the listed learnings for relevance to the current task
2. If a past learning directly applies, mention it when asking clarifying questions or grounding scope:
   > "A past learning [`<id>`] suggests <insight>. Does this apply here?"
3. Reference relevant learnings in the Technical Context section of the brief
4. Do not force-fit unrelated learnings — only reference when genuinely relevant

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

### Low-Profile Compact Brief

When the Complexity Assessment yields a low profile (score 5-7), the Context Brief MAY use this compact format instead of the full template above:

- **Goal**, **Scope**, and **Success Criteria** sections are required
- **Technical Context** collapses to 1-3 bullet points of relevant codebase findings
- **Constraints** collapses to a single bullet list (no subsections)
- **Open Questions** is omitted if none exist
- **Complexity Assessment** uses an inline summary instead of the full table:
  `**Complexity:** <score>/15 (low) — <one-line rationale>` followed by the profile, split, isolation, and risk fields

The compact brief still hands off cleanly to planning. Medium and high profiles use the full template.

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
| Skipping clarify because the request already looks clear | Clear work still needs a brief and execution profile; use direct clarify instead |
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

Every new task enters Dev Kit through clarify first, even when clarify runs in direct mode. This skill does not invoke the next skill itself. It saves the brief, updates `.dev-kit/` state, and points the session to `planning`.
