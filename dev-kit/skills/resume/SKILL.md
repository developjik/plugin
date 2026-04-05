---
name: resume
description: Resume an interrupted session. Scans docs/sessions/ for in-progress work and dispatches to the correct skill based on state.md. Triggers on "이어서", "resume", "continue", "아까 하던 거", "진행 중인 작업", "이전 작업", "다시 시작", or when a new session starts and prior work may exist.
---

# Resume Session

Resumes an interrupted session by scanning `docs/sessions/` and dispatching to the correct next skill.

## Core Principle

This skill is a **router, not a worker.** It finds the right session and the right next action, then hands off to the appropriate skill. It never performs implementation, planning, or review work itself.

## Hard Gates

1. **`docs/sessions/` does not exist → route to `clarify`.** No prior work to resume.
2. **Directories without `state.md` are ignored.** Corrupted or incomplete sessions are skipped.
3. **Multiple in-progress sessions → present list to user.** Never auto-select when there are multiple candidates.
4. **Never perform work directly.** Always dispatch to the skill indicated by Next Action.

## When To Use

- The user says "이어서 해줘", "resume", "continue", "아까 하던 거", "진행 중인 작업", "이전 작업", "다시 시작"
- A new Claude session starts and the user's intent is to resume prior work
- The user references prior work without specifying a new task

## When NOT To Use

- The user describes a new task ("새 기능 만들고 싶어", "I want to add...")
- The user asks about something unrelated to prior development work
- No `docs/sessions/` directory exists (first-time use)

## Process

### Phase 1: Session Scan

```
1. Check if docs/sessions/ directory exists
   - Does not exist → "새 작업인 것 같습니다. clarify를 시작합니다."
     Route to clarify.

2. List all subdirectories in docs/sessions/

3. Filter out non-session entries (files like `.DS_Store`, hidden files, anything that is not a directory)
   - Only consider entries that are directories

4. For each subdirectory:
   a. Check if state.md exists
   b. Read state.md
   c. If Status == "in-progress", add to candidate list

5. Candidate list is empty →
   "진행 중인 세션이 없습니다. 새 작업을 시작하려면 clarify를 시작합니다."
   Route to clarify.
```

### Phase 2: Session Selection

**Single candidate:**

```
"다음 세션을 이어서 진행합니다:

  [session-name] ([workflow], [current phase])

  Next Action: [Next Action from state.md]

  [스킬 이름]을(를) 실행합니다."
```

**Multiple candidates:**

Present a numbered list:

```
진행 중인 세션이 여러 개 있습니다:

  1. auth-login (simple, execute 중)
     Last: 2026-04-05 16:45 — Task 3 PASS

  2. payment-migration (complex, M2 executing)
     Last: 2026-04-07 15:30 — M2 execute started

어느 것을 이어서 할까요?
```

Wait for user selection. Do not proceed until the user chooses.

### Phase 3: Dispatch

Read the selected session's `state.md` Next Action field.

**Dispatch mapping:**

| Next Action contains | Dispatch to |
|---|---|
| "planning" | `planning` skill with session path |
| "execute" | `execute` skill with session path |
| "review-execute" or "review" | `review-execute` skill with session path |
| "milestone-planning" | `milestone-planning` skill with session path |
| "long-execute" | `long-execute` skill with session path |
| "simplify" | `simplify-code` skill |
| "clean" or "deslop" | `clean-ai-slop` skill |
| "karpathy" | `karpathy` skill |
| "rob-pike" | `rob-pike` skill |
| "debugging" | `systematic-debugging` skill |

**Dispatch message format:**

```
세션 docs/sessions/<session-id>/을(를) 이어서 진행합니다.
state.md의 Next Action: [Next Action 내용]

[스킬 이름]을(를) 실행합니다.
Session: docs/sessions/<session-id>/
```

### Session Summary Format

When presenting sessions to the user, generate a one-line summary per session:

- **Simple:** `[name] (simple, [current phase] 중)`
- **Complex:** `[name] (complex, M[N] [milestone status])`
- Include the last Execution Log entry as context

## Anti-Patterns

| Anti-Pattern | Why It Fails |
|---|---|
| Finding a session and starting work directly | resume is a router. Work is done by the dispatched skill |
| Ignoring in-progress sessions and creating a new one | Loses the user's prior work |
| Auto-selecting when multiple sessions exist | User may not want the "first" one found |
| Treating directories without state.md as sessions | Corrupted state. Must ignore |
| Re-reading entire session history before dispatching | Only state.md's Next Action is needed for routing |

## Minimal Checklist

- [ ] Scanned docs/sessions/ for in-progress sessions
- [ ] Ignored directories without state.md
- [ ] Presented multiple candidates to user (if > 1)
- [ ] Read Next Action from selected session's state.md
- [ ] Dispatched to the correct skill with session path

## Transition

- Session found → dispatch to Next Action skill with `Session: docs/sessions/<session-id>/`
- No sessions → route to `clarify`
- User says "new task" → route to `clarify`
