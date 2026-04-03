---
name: clarify-requirements
description: Use when a user's request is vague, ambiguous, or underspecified. Launches an iterative Q&A loop to resolve ambiguity while a subagent explores the codebase in parallel. Outputs a clear, well-scoped context brief so the user can plan sharply. Triggers on "I want to...", "I need...", "let's build...", "can you help me...", "we should...", or any request where the full scope isn't immediately clear.
---

# Clarify Through Iterative Discovery

Narrows vague user requests into well-defined work scopes. Runs questions and code exploration in parallel to bring the user to a state where they can plan sharply.

## Core Principle

Ambiguity does not resolve in one pass. Multiple rounds of questions and code exploration intersect, gradually sharpening the picture. The purpose of this skill is not "writing code" — it is making "what the user wants" and "what state the codebase is in" vivid and clear.

## Hard Gates

1. **One question per message.** Never bundle multiple questions into a single message.
2. **Always use subagents.** While conversing with the user, dispatch subagents to explore the codebase in response to the user's answers.
3. **Do not start implementation until you can say "this is clear enough."** Understanding must be complete at the codebase level.
4. **Every question must narrow scope.** Do not repeat questions at the same level of ambiguity.
5. **Never dump raw code exploration results on the user.** Summarize findings in the context of the user's question.

## When To Use

- The user says "I want to…" but the scope is unclear
- The request is vague enough that implementation could go in multiple directions
- The user themselves hasn't fully articulated what they want
- There's a risk of clashing with existing codebase structure, so exploration is needed

## When NOT To Use

- The request is already specific and clear (proceed to implementation or plan skill)
- The scope is obvious, like a simple bug fix or config change
- The user explicitly says "don't ask questions, just do it"

## The Two-Track Process

### Track 1: User Q&A (Ambiguity Resolution)

Ask the user questions to resolve ambiguity.

**Question principles:**

- One question per message
- Offer choices when possible (A/B/C)
- When a new ambiguity emerges from an answer, drill into it in the next question
- Ask "which case?" rather than "why?" — draw out concrete scenarios, not abstract intent
- If an answer contradicts a previous one, flag it immediately and realign

**Question sequence guide:**

1. **Purpose**: "What is the end goal of this work?" (what they want to achieve)
2. **Scope**: "What's included and what's excluded?" (draw boundaries)
3. **Constraints**: "Are there existing constraints that affect this?" (time, compatibility, dependencies)
4. **Success criteria**: "What should the state look like when this is done?" (verifiable outcome)
5. **Priority**: "If there are multiple paths, what matters most?" (trade-offs)

After each question, briefly update "what we've established so far."

### Track 2: Codebase Exploration (Technical Context)

Use subagents to explore the codebase. Run in parallel with user Q&A.

**How to dispatch exploration:**

Immediately after asking the user a question, launch a subagent via the Agent tool. The goal is to make the user fully understand how the work plays out in the codebase. The subagent investigates:

- Related file structure and naming conventions
- Existing implementation patterns (error handling, state management, data flow)
- Dependencies and interface boundaries
- Recent change history (relevant commits)
- Test coverage status

**Subagent prompt template:**

```
subagent_type: Explore
description: "Explore [topic] codebase"
prompt: |
  The user has requested [summarized request].

  Investigate and report on:
  1. Related files and the role of each
  2. Existing implementation patterns (is something similar already in place?)
  3. Boundary areas this work is likely to affect
  4. Recent related changes
  5. Existing test state

  Report only key findings concisely.
  Do not dump entire file contents.
```

**Processing subagent results:**

When the subagent returns findings:

1. Cross-validate against the user's answers
2. If technical constraints unknown to the user are discovered, reflect them in the next question
3. If a conflict with existing code is likely, notify the user

## Putting It Together: The Loop

```dot
digraph clarify {
    rankdir=TB;
    "User states vague request" [shape=box];
    "Assess: what's ambiguous?" [shape=box];
    "Ask user ONE question" [shape=box];
    "Dispatch explore subagent" [shape=box, style=dashed];
    "Receive user answer" [shape=box];
    "Receive subagent findings" [shape=box, style=dashed];
    "Synthesize: still ambiguous?" [shape=diamond];
    "Present context brief" [shape=doublecircle];

    "User states vague request" -> "Assess: what's ambiguous?";
    "Assess: what's ambiguous?" -> "Ask user ONE question";
    "Ask user ONE question" -> "Dispatch explore subagent" [style=dashed, label="parallel"];
    "Ask user ONE question" -> "Receive user answer";
    "Dispatch explore subagent" -> "Receive subagent findings" [style=dashed];
    "Receive user answer" -> "Synthesize: still ambiguous?";
    "Receive subagent findings" -> "Synthesize: still ambiguous?" [style=dashed];
    "Synthesize: still ambiguous?" -> "Ask user ONE question" [label="yes"];
    "Synthesize: still ambiguous?" -> "Present context brief" [label="no"];
}
```

**Each cycle:**

1. Receive the user's answer
2. Merge subagent results if available (if still in progress, merge in the next cycle)
3. Update the "remaining ambiguities" list
4. Pick the next question (prioritize the one that most affects scope)
5. If needed, launch additional subagents (when previous exploration revealed new areas to investigate)

## Output: Context Brief

When ambiguity is sufficiently resolved, present the user with a Context Brief. This is the skill's final deliverable.

**Context Brief format:**

```markdown
## Context Brief: [Task Title]

### Goal

[One-sentence task goal]

### Scope

- **In scope**: [Included work]
- **Out of scope**: [Explicitly excluded work]

### Technical Context

[Technical facts discovered through code exploration]

- Current implementation state
- Affected areas
- Existing patterns to follow

### Constraints

[Identified constraints]

- External constraints
- Technical constraints
- Time/priority constraints

### Success Criteria

[Specific criteria for the completed state]

### Open Questions (if any)

[Questions still open — unresolved but not blocking]

### Complexity Assessment

Assess task complexity using these 5 signals. Score each signal, then determine the routing.

| Signal                   | Low (1)                          | Medium (2)                              | High (3)                                                 |
| ------------------------ | -------------------------------- | --------------------------------------- | -------------------------------------------------------- |
| **Scope breadth**        | Single feature or component      | 2-3 related components                  | 4+ components or cross-cutting concerns                  |
| **File impact**          | ≤3 files                         | 4-8 files                               | 9+ files or across 3+ directories                        |
| **Interface boundaries** | Works within existing interfaces | Extends existing interfaces             | Defines new interfaces or modifies contracts             |
| **Dependency depth**     | No ordering constraints          | Linear dependency chain                 | Branching dependencies requiring DAG                     |
| **Risk surface**         | No integration risk              | Internal integration between components | External systems, schema changes, backward compatibility |

**Score:** [sum of signals, range 5-15]
**Verdict:** [Simple (5-8) | Complex (9-15)]
**Rationale:** [1-2 sentences explaining the dominant complexity factor]

### Suggested Next Step

[Auto-determined by Complexity Assessment verdict — see Routing Rules below]
```

**Save the Context Brief to a file:**

```
docs/dev-kit/context/YYYY-MM-DD-<topic>-brief.md
```

(Follow a user-specified path instead if they request a different location.)

Show the Context Brief in the conversation first. Save it only after the user approves it. This file feeds directly into the `craft-plan` skill.

## Red Flags

Stop and recalibrate if any of these occur:

| Situation                                              | Response                                                                                                                            |
| ------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------- |
| User says "just figure it out"                         | Warn: starting before ambiguity is resolved leads to a high probability of rework. At minimum, confirm purpose and success criteria |
| Same topic questioned 3+ times                         | The user genuinely doesn't know. Separate knowns from unknowns, present assumptions for the unknowns, and confirm                   |
| Subagent finds conflicting existing code               | Notify the user immediately. Conflicts with existing structure require a design decision                                            |
| Request decomposes into multiple independent sub-tasks | Show the decomposition to the user and propose prioritizing one at a time                                                           |

## Anti-Patterns

| Anti-Pattern                             | Why It Fails                                                            |
| ---------------------------------------- | ----------------------------------------------------------------------- |
| Five questions in one message            | The user gives shallow answers. Ambiguity persists.                     |
| Questions without code exploration       | Scope can narrow in a direction that conflicts with existing code       |
| Showing full subagent output to the user | Too much noise. Provide only the summary relevant to the user's context |
| Deciding "that's enough" unilaterally    | Always present the Context Brief to the user and get confirmation       |
| Starting implementation                  | This skill ends at "clear context," not "implemented code"              |

## Minimal Checklist

Self-check at the end of each cycle:

- [ ] Did one ambiguity get resolved this cycle?
- [ ] Is subagent exploration in progress or complete?
- [ ] Is the next question based on previous answers?
- [ ] Has progress been clearly communicated to the user?

## Routing Rules

After the Context Brief is approved, the **Complexity Assessment verdict** determines the next skill:

| Verdict                  | Route                | Rationale                                                                           |
| ------------------------ | -------------------- | ----------------------------------------------------------------------------------- |
| **Simple** (score 5-8)   | `craft-plan`      | Task fits in a single plan cycle. Direct planning is sufficient.                    |
| **Complex** (score 9-15) | `decompose-milestones` | Task requires multiple plan cycles. Milestone decomposition needed before planning. |

**Override:** The user can always override the routing. If the user says "just plan it" for a complex task, route to `craft-plan`. If the user says "break it into milestones" for a simple task, route to `decompose-milestones`.

**Edge case (score 8-9):** Present both options to the user with a recommendation. Example: "This scores 9 — borderline complex. I recommend decompose-milestones because [dominant factor], but craft-plan could work if [condition]. Which do you prefer?"

The "Suggested Next Step" field in the Context Brief must reflect this routing:

- Simple: "Proceed to `craft-plan` — task fits in a single plan cycle."
- Complex: "Proceed to `decompose-milestones` — task requires milestone decomposition for multi-phase execution."
- Borderline: "Recommend `decompose-milestones` (score 9), but `craft-plan` is viable if [condition]. User choice needed."

## Transition

Once the Context Brief is approved by the user, route based on the Complexity Assessment:

- **Simple** (score 5-8) → `craft-plan` skill — single-cycle implementation planning
- **Complex** (score 9-15) → `decompose-milestones` skill — multi-phase milestone decomposition, then `orchestrate-execution` for execution
- **Borderline** (score 8-9) → present both options with recommendation, user decides
- If further exploration is needed → continue the `clarify-requirements` skill's Q&A loop
- If the scope is already trivial and planning is unnecessary → direct implementation

This skill itself **does not invoke the next skill.** It ends by presenting the Context Brief, saving it to a file, and suggesting the routed next step.

**Context Brief → craft-plan mapping:**

| Context Brief field | craft-plan input |
| ------------------- | ------------------- |
| Goal | Plan header goal |
| Scope (In/Out) | Plan header work scope |
| Technical Context | Architecture, tech stack, and file structure basis |
| Constraints | Constraints reflected during task decomposition |
| Success Criteria | Self-review criteria |
| Open Questions | Assumptions to capture and confirm with the user |
