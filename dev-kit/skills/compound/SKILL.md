---
name: compound
description: Manage compound learnings — extract new learnings from completed sessions, review and refresh existing learnings, and view the learning knowledge base.
---

# Compound Learning Management

Manages the `.dev-kit/learnings/` knowledge base. Learnings accumulate across sessions and are surfaced as passive SessionStart context that can inform explicitly invoked `clarify` and `planning` phases.

## Core Principle

Every completed task is a potential source of reusable knowledge. Compound learning turns one-shot sessions into a growing knowledge base where past decisions, patterns, and insights inform future work. The mechanism is lightweight: extraction is optional per session, and consumption happens through passive hook context plus explicit phase usage.

## Modes

This skill operates in three modes depending on user intent:

### Mode 1: Extract (`/compound` or `/compound extract`)

Manually extract a learning from a completed or in-progress session.

**When to use:**
- When review-execute's automatic extraction was skipped but the user later realizes a learning is worth preserving
- When the user wants to document a learning from current work outside the normal flow

**Process:**

1. **Identify the session.** Use `.dev-kit/current.json` or ask the user for a session ID.
2. **Read session artifacts.** Load `brief.md`, `plan.md`, `review.md` (if available), and any `progress.md`.
3. **Identify the learning.** Ask the user:
   > "What reusable pattern, decision, or insight did you discover? (Describe briefly)"
4. **Write `compound.md`** to the session directory using this format:

```markdown
# <learning-id>

> Source: <session-id>

## Situation
[What problem or context triggered this learning]

## Decision
[What was decided or discovered]

## Rationale
- [Why this decision was made]
- [What alternatives were considered]

## Applicability
- [When to apply this learning]
- [When NOT to apply this learning]
```

5. **Create the learning entry:**
   - Derive `learning-id`: lowercase, hyphenated, max 4 words from the title
   - Write `.dev-kit/learnings/<learning-id>.md` with the same content
   - Update `.dev-kit/learnings/index.json` with a new entry:
     - `tags`: 3-6 keywords describing the learning domain
     - `context_types`: technology or domain context (e.g., `nodejs`, `react`, `api`, `database`)
     - `status`: `active`
     - `reference_count`: `0`
6. **Update session state** (if session exists):
   - `compound_status`: `extracted`
   - `artifacts.compound`: path to `compound.md`

### Mode 2: Refresh (`/compound refresh`)

Audit existing learnings and update their status.

**When to use:**
- Periodically (e.g., monthly) to prevent knowledge decay
- When the user suspects some learnings are outdated
- When major refactoring has changed the codebase significantly

**Process:**

1. **Load all learnings.** Read `.dev-kit/learnings/index.json`.
2. **Classify each active learning:**

| Classification | Criteria | Action |
|---|---|---|
| **keep** | Referenced in last 30 days, still valid | No change |
| **update** | Referenced but content is partially outdated | Revise the `.md` file |
| **replace** | A better pattern has been discovered | Archive old, create new |
| **archive** | No longer relevant (90+ days unreferenced, or codebase has diverged) | Set `status: "archived"` |

3. **Present the classification** to the user as a table:

```
Learning ID         | Status  | Last Ref  | Refs | Recommendation
--------------------|---------|-----------|------|---------------
async-error-pattern | active  | 3 days   | 5    | keep
old-auth-flow       | active  | 95 days  | 1    | archive
```

4. **Apply changes** after user approval:
   - Update `index.json` statuses
   - Revise `.md` files for `update` entries
   - Archive entries by setting `status: "archived"`

### Mode 3: List (`/compound list`)

Display the current state of the learning knowledge base.

**Process:**

1. Read `.dev-kit/learnings/index.json`
2. Display all learnings grouped by status:

```
Active Learnings (3):
  [async-error-pattern] Promise.all failure recovery (refs: 5, tags: async, error-handling)
  [batch-query-pattern] N+1 query optimization (refs: 3, tags: database, performance)
  [auth-middleware-v2] JWT validation approach (refs: 1, tags: auth, security)

Archived Learnings (1):
  [old-auth-flow] Legacy session-based auth (archived: 2026-03-15)
```

3. If the user asks about a specific learning, read and display the full `.md` file.

## Data Model

### learnings/index.json

```json
{
  "schema_version": 1,
  "learnings": [
    {
      "id": "async-error-pattern",
      "title": "Promise.all failure recovery pattern",
      "source_session": "2026-04-08T14-30-api-refactor",
      "tags": ["async", "error-handling", "typescript"],
      "context_types": ["nodejs", "api"],
      "file": "async-error-pattern.md",
      "created_at": "2026-04-08T16:00:00+09:00",
      "last_referenced_at": "2026-04-10T09:30:00+09:00",
      "reference_count": 3,
      "status": "active"
    }
  ]
}
```

### learnings/<id>.md

```markdown
# <learning-id>

> Source: <session-id>

## Situation
[Context]

## Decision
[What was decided]

## Rationale
- [Why]

## Applicability
- [When to use]
- [When not to use]
```

## Consumption Flow

Learnings are made available passively — no separate workflow entry is triggered:

1. `session-start.sh` reads `learnings/index.json`
2. Active learnings are summarized in SessionStart `additionalContext`
3. `clarify` can reference relevant learnings when it is explicitly invoked
4. `planning` can incorporate relevant past decisions into plan rationale when it is explicitly invoked
5. `execute` does not directly consume learnings (planning filters for it)
6. `review-execute` can check whether the implementation aligns with referenced learnings

Each time a learning is referenced in a session, its `reference_count` and `last_referenced_at` are updated.

## Hard Gates

1. **Extraction is always optional.** Never force the user to extract a learning.
2. **Learnings must be actionable.** Vague observations ("this was hard") are not learnings.
3. **One learning per concept.** Do not bundle multiple unrelated insights into one entry.
4. **Tags must be specific.** Use technology names and domain terms, not generic words like "code" or "fix".
5. **Do not modify learnings during normal flow.** Only this skill and the review-execute extraction step write to `.dev-kit/learnings/`.

## Anti-Patterns

| Anti-Pattern | Why It Fails |
|---|---|
| Extracting every trivial decision | Noise drowns out signal |
| Skipping tags and context_types | Makes relevance matching useless |
| Never running refresh | Stale learnings mislead future planning |
| Copying code snippets as learnings | Learnings are decisions and patterns, not code |
| Forcing extraction on simple tasks | Creates overhead without value |
